from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message
from bot import db
from bot.locales import t
import logging

class AccessMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return await handler(event, data)

        # Groups
        if hasattr(event, "chat") and event.chat.type in ["group", "supergroup"]:
            if isinstance(event, Message) and (event.text == "/start" or not event.voice):
                return
                
            group = await db.get_group(event.chat.id)
            if not group:
                logging.warning(f"Group {event.chat.id} not found in DB. Ignoring.")
                return
            
            inviter = await db.get_user(group["added_by"])
            if not inviter or inviter["role"] == "pending":
                logging.warning(f"Inviter {group['added_by']} is not approved. Ignoring.")
                return
            
            logging.info(f"Group {event.chat.id} passed middleware.")
            data["user"] = {"user_id": event.chat.id, "username": event.chat.title, "role": "group"}
            data["inviter"] = inviter
            return await handler(event, data)

        # Private messages
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        user = await db.get_user(from_user.id)
        if user is None:
            if isinstance(event, Message):
                await event.answer(t("send_start"))
            return

        if user["role"] == "pending":
            if isinstance(event, Message):
                await event.answer(t("pending_approval"))
            return

        data["user"] = user
        return await handler(event, data)