from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot import db
from bot.constants import ROLE_ADMIN, ROLE_PENDING
from bot.keyboards import (
    admin_menu_kb, user_actions_kb, users_list_kb, stats_kb,
    format_size, format_duration, main_menu_kb
)
from bot.locales import t

router = Router()

def _is_admin(user: dict) -> bool:
    return user["role"] == ROLE_ADMIN

async def _pending_count() -> int:
    users = await db.get_all_users()
    return sum(1 for u in users if u["role"] == ROLE_PENDING)

@router.message(Command("admin"))
async def cmd_admin(message: Message, user: dict) -> None:
    if not _is_admin(user):
        await message.answer(t("no_rights"))
        return
    await message.answer(t("admin_panel_title"), reply_markup=admin_menu_kb(await _pending_count()))

@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    await callback.message.edit_text(t("admin_panel_title"), reply_markup=admin_menu_kb(await _pending_count()))
    await callback.answer()

@router.callback_query(F.data == "admin:users")
async def cb_users(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    users = await db.get_all_users()
    if not users:
        await callback.message.edit_text(t("no_users"))
        await callback.answer()
        return
    await callback.message.edit_text(t("users_list_title", count=len(users)), reply_markup=users_list_kb(users))
    await callback.answer()

@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    
    g_stats = await db.get_global_stats()
    text = (
        f"{t('global_stats_title')}\n\n"
        f"{t('stats_voices', count=g_stats['count'])}\n"
        f"{t('stats_duration', duration=format_duration(g_stats['duration']))}\n"
        f"{t('stats_size', size=format_size(g_stats['size']))}\n\n"
        f"{t('stats_privacy')}"
    )
    await callback.message.edit_text(text, reply_markup=stats_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin:back")
async def cb_back(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    await callback.message.edit_text(t("admin_panel_title"), reply_markup=admin_menu_kb(await _pending_count()))
    await callback.answer()

@router.callback_query(F.data.startswith("user:"))
async def cb_user(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user) or callback.data == "user:my_stats":
        return
    uid = int(callback.data.split(":", 1)[1])
    target = await db.get_user(uid)
    if not target:
        await callback.answer(t("user_not_found"), show_alert=True)
        return
        
    u_stats = await db.get_user_stats(uid)
    name = f"@{target['username']}" if target["username"] else str(uid)
    role_name = t(f"role_{target['role']}")
    
    text = t("user_info", 
             name=name, uid=uid, role=role_name, 
             count=u_stats['count'], 
             duration=format_duration(u_stats['duration']), 
             size=format_size(u_stats['size']))
             
    await callback.message.edit_text(text, reply_markup=user_actions_kb(uid, target["role"]), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data.startswith("set_role:"))
async def cb_set_role(callback: CallbackQuery, user: dict, bot: Bot) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    _, uid_s, role = callback.data.split(":")
    uid = int(uid_s)
    target = await db.get_user(uid)
    if not target:
        await callback.answer(t("user_not_found"), show_alert=True)
        return

    if role != ROLE_ADMIN and target["role"] == ROLE_ADMIN:
        admins = [u for u in await db.get_all_users() if u["role"] == ROLE_ADMIN]
        if len(admins) <= 1:
            await callback.answer(t("last_admin_error"), show_alert=True)
            return

    await db.set_role(uid, role)
    updated = await db.get_user(uid)
    name = f"@{updated['username']}" if updated["username"] else str(uid)
    role_name = t(f"role_{role}")
    
    admins = await db.get_admins()
    msg_text = t("role_changed", name=name, uid=uid, role=role_name)
    
    for admin in admins:
        try:
            await bot.send_message(admin["user_id"], msg_text, parse_mode="Markdown")
        except Exception:
            pass

    u_stats = await db.get_user_stats(uid)
    text = t("user_info", 
             name=name, uid=uid, role=role_name, 
             count=u_stats['count'], 
             duration=format_duration(u_stats['duration']), 
             size=format_size(u_stats['size']))
             
    await callback.message.edit_text(text, reply_markup=user_actions_kb(uid, updated["role"]), parse_mode="Markdown")
    await callback.answer(t("done"))