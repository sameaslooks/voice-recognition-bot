import logging
import os
import re
from logging.handlers import TimedRotatingFileHandler
from bot import config

def _custom_namer(default_name: str) -> str:
    dir_name = os.path.dirname(default_name)
    base_name = os.path.basename(default_name)
    match = re.search(r'bot\.log\.(\d{4}-\d{2}-\d{2})', base_name)
    if match:
        date_str = match.group(1)
        return os.path.join(dir_name, f"bot-{date_str}.log")
    return default_name

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(config.LOG_LEVEL)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = os.path.join(os.path.dirname(config.DB_PATH), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "bot.log")
    
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=config.LOG_BACKUP_DAYS,
        encoding="utf-8",
        utc=True 
    )
    
    file_handler.namer = _custom_namer
    file_handler.suffix = "%Y-%m-%d" 
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.INFO)

    return logger

def update_log_retention(days: int):
    for handler in logging.getLogger().handlers:
        if isinstance(handler, TimedRotatingFileHandler):
            handler.backupCount = days
            logging.info(f"Log retention updated to {days} days (0 = infinite)")