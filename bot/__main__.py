import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot import config, db, speech
from bot.handlers import admin, common, voice, groups
from bot.middlewares import AccessMiddleware

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    logging.getLogger("httpx").setLevel(logging.WARNING)

    await config.ensure_models()
    config.validate()

    await db.connect()
    logging.info("SQLite is ready")

    await speech.start()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    access = AccessMiddleware()
    dp.message.middleware(access)
    dp.callback_query.middleware(access)

    dp.include_router(groups.router)
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(voice.router)

    try:
        logging.info("Polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "my_chat_member"])
    finally:
        await speech.stop()
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass