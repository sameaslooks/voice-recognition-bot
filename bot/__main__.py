import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot import config, db, speech
from bot.handlers import admin, common, voice, groups
from bot.middlewares import AccessMiddleware
from bot.utils.logger import setup_logger, update_log_retention
from bot.locales import t

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description=t("cmd_start")),
        BotCommand(command="author", description=t("cmd_author")),
        BotCommand(command="admin", description=t("cmd_admin")),
        BotCommand(command="help", description=t("cmd_help")),
    ]
    await bot.set_my_commands(commands)

async def main() -> None:
    setup_logger()
    
    await config.ensure_models()
    config.validate()

    await db.connect()
    logging.info("SQLite is ready")
    
    saved_days = int(await db.get_setting("log_backup_days", "30"))
    update_log_retention(saved_days)

    await speech.start()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    
    await set_commands(bot)

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