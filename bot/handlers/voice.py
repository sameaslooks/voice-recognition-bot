import os
import tempfile
import asyncio
from aiogram import F, Router
from aiogram.types import Message
from bot import db, speech
from bot.locales import t

router = Router()

async def _update_status_loop(status_msg: Message, future: asyncio.Future, my_id: int):
    last_text = ""
    try:
        while not future.done():
            ahead = speech.get_position(my_id)
            loading = speech.is_loading()
            
            if ahead == 0:
                text = t("loading_model") if loading else t("recognizing")
            else:
                if loading and ahead == 1:
                    text = t("in_queue_loading", ahead=ahead)
                else:
                    text = t("in_queue", ahead=ahead)
                    
            if text != last_text:
                await status_msg.edit_text(text)
                last_text = text
                
            await asyncio.sleep(1.0)
    except Exception:
        pass

@router.message(F.voice)
async def handle_voice(message: Message, user: dict) -> None:
    file = await message.bot.get_file(message.voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        ogg_path = tmp.name
    try:
        await message.bot.download_file(file.file_path, ogg_path)
        
        future, my_id = await speech.enqueue(ogg_path)
        status = await message.reply(t("added_to_queue"))
        updater = asyncio.create_task(_update_status_loop(status, future, my_id))
        
        try:
            text = await future
        except Exception as exc:
            updater.cancel()
            await status.edit_text(t("recognition_error", error=exc))
            return
        finally:
            if not updater.done():
                updater.cancel()

        if not text.strip():
            await status.edit_text(t("empty_result"))
            return

        duration = message.voice.duration
        size = message.voice.file_size or 0
        
        await db.add_stat(message.from_user.id, message.chat.id, duration, size)
        
        await status.edit_text(f"📝 {text}")
    finally:
        try:
            os.unlink(ogg_path)
        except OSError:
            pass