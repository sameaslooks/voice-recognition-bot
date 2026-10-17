import logging
from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot import db
from bot.constants import ROLE_ADMIN, ROLE_PENDING, AUTHOR_NAME, GITHUB_PROFILE, GITHUB_REPO
from bot.keyboards import (
    admin_menu_kb, user_actions_kb, users_list_kb, groups_list_kb, group_details_kb, stats_kb, about_kb,
    format_size, format_duration, main_menu_kb
)
from bot.locales import t
from bot.utils.logger import update_log_retention

router = Router()

def _is_admin(user: dict) -> bool:
    return user["role"] == ROLE_ADMIN

async def _pending_count() -> int:
    users = await db.get_all_users()
    return sum(1 for u in users if u["role"] == ROLE_PENDING)

async def _get_admin_kb():
    log_status = await db.get_setting("log_transcripts", "false")
    log_days = int(await db.get_setting("log_backup_days", "30"))
    status_str = "ON" if log_status == "true" else "OFF"
    return admin_menu_kb(await _pending_count(), status_str, log_days)

@router.message(Command("admin"))
async def cmd_admin(message: Message, user: dict) -> None:
    if not _is_admin(user):
        await message.answer(t("no_rights"))
        return
    await message.answer(t("admin_panel_title"), reply_markup=await _get_admin_kb())

@router.message(Command("find"))
async def cmd_find(message: Message, user: dict) -> None:
    if not _is_admin(user):
        return
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Usage: `/find <id_or_username>`", parse_mode="Markdown")
        return
        
    query = args[1].replace("@", "")
    results = await db.search_user(query)
    
    if not results:
        await message.answer("No users found.")
        return
        
    text = "🔍 **Search Results:**\n\n"
    for r in results[:5]:
        name = r['username'] if r['username'] else str(r['user_id'])
        text += f"👤 `{name}` (ID: `{r['user_id']}`)\n"
        text += f"├ {t('stats_voices', count=r['count'])}\n"
        text += f"└ {t('stats_duration', duration=format_duration(r['duration']))}\n\n"
        
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    await callback.message.edit_text(t("admin_panel_title"), reply_markup=await _get_admin_kb())
    await callback.answer()

@router.callback_query(F.data == "admin:about")
async def cb_about(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
        
    text = t("about_text", 
             author=AUTHOR_NAME, 
             github_profile=GITHUB_PROFILE, 
             github_repo=GITHUB_REPO)
             
    await callback.message.edit_text(text, reply_markup=about_kb(), parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data == "admin:toggle_log")
async def cb_toggle_log(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
        
    current = await db.get_setting("log_transcripts", "false")
    new_val = "false" if current == "true" else "true"
    await db.set_setting("log_transcripts", new_val)
    
    await callback.message.edit_reply_markup(reply_markup=await _get_admin_kb())
    await callback.answer(f"Logging: {'ON' if new_val == 'true' else 'OFF'}")

@router.callback_query(F.data == "admin:toggle_backup")
async def cb_toggle_backup(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
        
    options = [30, 60, 90, 180, 360, 0]
    current_str = await db.get_setting("log_backup_days", "30")
    current = int(current_str)
    
    try:
        idx = options.index(current)
        new_val = options[(idx + 1) % len(options)]
    except ValueError:
        new_val = 30
        
    await db.set_setting("log_backup_days", str(new_val))
    update_log_retention(new_val)
    
    await callback.message.edit_reply_markup(reply_markup=await _get_admin_kb())
    await callback.answer("Log retention updated")

@router.callback_query(F.data.startswith("admin:users"))
async def cb_users(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    parts = callback.data.split(":")
    page = int(parts[2]) if len(parts) > 2 else 1
    users = await db.get_all_users()
    if not users:
        await callback.message.edit_text(t("no_users"))
        await callback.answer()
        return
    await callback.message.edit_text(t("users_list_title", count=len(users)), reply_markup=users_list_kb(users, page=page))
    await callback.answer()

@router.callback_query(F.data == "ignore")
async def cb_ignore(callback: CallbackQuery) -> None:
    await callback.answer()

@router.callback_query(F.data.startswith("admin:groups"))
async def cb_groups(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    parts = callback.data.split(":")
    page = int(parts[2]) if len(parts) > 2 else 1
    groups = await db.get_groups_stats()
    if not groups:
        await callback.message.edit_text(t("no_groups_stats"), reply_markup=stats_kb())
        await callback.answer()
        return
    await callback.message.edit_text(t("groups_stats_title"), reply_markup=groups_list_kb(groups, page=page))
    await callback.answer()

@router.callback_query(F.data.startswith("group_details:"))
async def cb_group_details(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    
    chat_id = int(callback.data.split(":")[1])
    details = await db.get_group_details(chat_id)
    
    if not details or details["total_count"] == 0:
        await callback.answer("No data for this group yet.", show_alert=True)
        return
        
    group_info = await db.get_group(chat_id)
    title = group_info["title"] if group_info else f"Group {chat_id}"
    
    text = f"📊 **{t('group_details_title', title=title)}**\n\n"
    text += f"{t('stats_voices', count=details['total_count'])}\n"
    text += f"{t('stats_duration', duration=format_duration(details['total_duration']))}\n"
    text += f"{t('stats_size', size=format_size(details['total_size']))}\n\n"
    
    text += "👤 **Top Users (by count):**\n"
    for u in details["users"][:10]:
        name = u['username'] if u['username'] else str(u['user_id'])
        text += f"• `{name}`: {u['count']} ({format_duration(u['duration'])})\n"
        
    if len(details["users"]) > 10:
        text += "_...and more users_"

    await callback.message.edit_text(text, reply_markup=group_details_kb(chat_id), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    
    g_stats = await db.get_global_stats()
    
    log_status = await db.get_setting("log_transcripts", "false")
    privacy_text = t("stats_privacy_on") if log_status == "true" else t("stats_privacy")

    text = (
        f"{t('global_stats_title')}\n\n"
        f"{t('stats_voices', count=g_stats['count'])}\n"
        f"{t('stats_duration', duration=format_duration(g_stats['duration']))}\n"
        f"{t('stats_size', size=format_size(g_stats['size']))}\n\n"
        f"{privacy_text}"
    )
    await callback.message.edit_text(text, reply_markup=stats_kb(), parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin:back")
async def cb_back(callback: CallbackQuery, user: dict) -> None:
    if not _is_admin(user):
        await callback.answer(t("no_rights"), show_alert=True)
        return
    await callback.message.edit_text(t("admin_panel_title"), reply_markup=await _get_admin_kb())
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