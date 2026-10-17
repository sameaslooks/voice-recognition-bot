from aiogram import Router
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from bot import db
from bot.locales import t
from bot.keyboards import about_public_kb

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_group(event: ChatMemberUpdated) -> None:
    if event.chat.type not in ["group", "supergroup"]:
        return

    chat_id = event.chat.id
    title = event.chat.title or "Unknown Group"
    added_by = event.from_user.id

    user = await db.get_user(added_by)
    if not user or user["role"] == "pending":
        await event.answer(t("group_denied"))
        await event.bot.leave_chat(chat_id)
        return

    await db.add_group(chat_id, title, added_by)
    await event.answer(t("group_added"), reply_markup=about_public_kb())

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_MEMBER >> IS_NOT_MEMBER))
async def bot_removed_from_group(event: ChatMemberUpdated) -> None:
    if event.chat.type not in ["group", "supergroup"]:
        return
        
    await db.remove_group(event.chat.id)