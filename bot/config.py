import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
LANGUAGE = os.getenv("LANGUAGE", "EN").upper()
DB_PATH = os.getenv("DB_PATH", "bot.db")
MODEL_DIR = os.getenv("MODEL_DIR", "models")
NUM_THREADS = int(os.getenv("NUM_THREADS", "2"))
MAX_SEGMENT_SEC = float(os.getenv("MAX_SEGMENT_SEC", "25"))
MODEL_IDLE_TIMEOUT = int(os.getenv("MODEL_IDLE_TIMEOUT", "1800"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TRANSCRIPTS = os.getenv("LOG_TRANSCRIPTS", "false").lower() == "true"
LOG_BACKUP_DAYS = int(os.getenv("LOG_BACKUP_DAYS", "30"))

ENCODER_PATH = os.path.join(MODEL_DIR, "encoder.int8.onnx")
DECODER_PATH = os.path.join(MODEL_DIR, "decoder.onnx")
JOINER_PATH = os.path.join(MODEL_DIR, "joiner.onnx")
TOKENS_PATH = os.path.join(MODEL_DIR, "tokens.txt")

MODEL_URLS = {
    "encoder.int8.onnx": "https://huggingface.co/Alexxerm/gigaam-v3-e2e-rnnt-sherpa-onnx/resolve/main/encoder.int8.onnx",
    "decoder.onnx": "https://huggingface.co/Alexxerm/gigaam-v3-e2e-rnnt-sherpa-onnx/resolve/main/decoder.onnx",
    "joiner.onnx": "https://huggingface.co/Alexxerm/gigaam-v3-e2e-rnnt-sherpa-onnx/resolve/main/joiner.onnx",
    "tokens.txt": "https://huggingface.co/Alexxerm/gigaam-v3-e2e-rnnt-sherpa-onnx/resolve/main/tokens.txt"
}

async def ensure_models() -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    for filename, url in MODEL_URLS.items():
        filepath = os.path.join(MODEL_DIR, filename)
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            continue
            
        logging.info(f"Downloading {filename}...")
        async with httpx.AsyncClient(follow_redirects=True, timeout=None) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                with open(filepath, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)
        logging.info(f"File {filename} downloaded successfully.")

def validate() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in .env")
    if LANGUAGE not in ("EN", "RU"):
        raise RuntimeError("LANGUAGE must be either 'EN' or 'RU'")
    for p in (ENCODER_PATH, DECODER_PATH, JOINER_PATH, TOKENS_PATH):
        if not os.path.exists(p):
            raise RuntimeError(f"Model file not found: {p}")