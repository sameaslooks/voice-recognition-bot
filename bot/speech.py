import asyncio
import logging
import time
import gc
import numpy as np  # type: ignore
import sherpa_onnx  # type: ignore
import subprocess
import tempfile
import wave
from pathlib import Path
from bot import config

_queue: asyncio.Queue = asyncio.Queue()
_worker_task: asyncio.Task | None = None
_idle_task: asyncio.Task | None = None

_recognizer = None
_model_lock = asyncio.Lock()
_last_used = 0.0
_is_loading = False

_total_submitted = 0
_total_processed = 0

def _load_model():
    global _recognizer, _is_loading
    if _recognizer is None:
        _is_loading = True
        logging.info("Loading GigaAM into memory...")
        _recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=config.ENCODER_PATH,
            decoder=config.DECODER_PATH,
            joiner=config.JOINER_PATH,
            tokens=config.TOKENS_PATH,
            num_threads=config.NUM_THREADS,
            sample_rate=16000,
            feature_dim=64,
            decoding_method="greedy_search",
            model_type="nemo_transducer",
        )
        _is_loading = False
        logging.info("Model loaded successfully!")

def _unload_model():
    global _recognizer
    if _recognizer is not None:
        logging.info(f"Unloading model (idle > {config.MODEL_IDLE_TIMEOUT}s)...")
        del _recognizer
        _recognizer = None
        gc.collect()
        logging.info("Model unloaded, memory freed.")

def _recognize_sync(ogg_path: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav_path = tmp.name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path],
            check=True, capture_output=True,
        )
        with wave.open(wav_path, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    finally:
        Path(wav_path).unlink(missing_ok=True)

    sr = 16000
    seg = int(config.MAX_SEGMENT_SEC * sr)
    parts = []
    for start in range(0, len(samples), seg):
        chunk = samples[start:start + seg]
        if len(chunk) < sr // 10:
            continue
        stream = _recognizer.create_stream()
        stream.accept_waveform(sr, chunk)
        _recognizer.decode_stream(stream)
        piece = stream.result.text.strip()
        if piece:
            parts.append(piece)
    return " ".join(parts)

async def _run_worker() -> None:
    global _total_processed, _last_used
    loop = asyncio.get_running_loop()
    
    while True:
        future, ogg_path, my_id = await _queue.get()
        
        async with _model_lock:
            if _recognizer is None:
                await loop.run_in_executor(None, _load_model)
                
            _last_used = time.monotonic()
            
            try:
                text = await loop.run_in_executor(None, _recognize_sync, ogg_path)
                future.set_result(text)
            except Exception as e:
                future.set_exception(e)
            finally:
                _total_processed += 1
                _queue.task_done()

async def _run_idle_checker() -> None:
    while True:
        await asyncio.sleep(60)
        async with _model_lock:
            if _recognizer is not None and (time.monotonic() - _last_used > config.MODEL_IDLE_TIMEOUT):
                _unload_model()

async def start() -> None:
    global _worker_task, _idle_task
    _worker_task = asyncio.create_task(_run_worker())
    _idle_task = asyncio.create_task(_run_idle_checker())
    logging.info("Queue and idle timer started")

async def stop() -> None:
    if _worker_task:
        _worker_task.cancel()
    if _idle_task:
        _idle_task.cancel()
    try:
        if _worker_task:
            await _worker_task
        if _idle_task:
            await _idle_task
    except asyncio.CancelledError:
        pass

async def enqueue(ogg_path: str) -> tuple[asyncio.Future, int]:
    global _total_submitted
    _total_submitted += 1
    my_id = _total_submitted
    
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    await _queue.put((future, ogg_path, my_id))
    return future, my_id

def get_position(my_id: int) -> int:
    ahead = my_id - _total_processed - 1
    return max(0, ahead)

def is_loading() -> bool:
    return _is_loading