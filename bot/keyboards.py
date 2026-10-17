from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot.constants import ROLE_EMOJI, ROLE_ADMIN
from bot.locales import t

def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s" if t("menu_title") == "Main menu:" else f"{h}ч {m}м {s}с"
    return f"{m}m {s}s" if t("menu_title") == "Main menu:" else f"{m}м {s}с"

def main_menu_kb(user: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("btn_my_stats"), callback_data="user:my_stats")]
    ]
    if user.get("role") == ROLE_ADMIN:
        rows.append([InlineKeyboardButton(text=t("btn_admin_panel"), callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back_menu"), callback_data="main_menu")]
    ])

def admin_menu_kb(pending: int = 0) -> InlineKeyboardMarkup:
    label = t("btn_users")
    if pending:
        label += t("pending_count", count=pending)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data="admin:users")],
        [InlineKeyboardButton(text=t("btn_global_stats"), callback_data="admin:stats")],
        [InlineKeyboardButton(text=t("btn_back_menu"), callback_data="main_menu")],
    ])

def users_list_kb(users: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for u in users:
        emoji = ROLE_EMOJI.get(u["role"], "❓")
        name = f"@{u['username']}" if u["username"] else str(u["user_id"])
        rows.append([InlineKeyboardButton(text=f"{emoji} {name}", callback_data=f"user:{u['user_id']}")])
    rows.append([InlineKeyboardButton(text=t("btn_back"), callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def user_actions_kb(uid: int, role: str) -> InlineKeyboardMarkup:
    rows = []
    if role != "admin":
        rows.append([InlineKeyboardButton(text=t("btn_make_admin"), callback_data=f"set_role:{uid}:admin")])
    if role != "user":
        rows.append([InlineKeyboardButton(text=t("btn_make_user"), callback_data=f"set_role:{uid}:user")])
    if role != "pending":
        rows.append([InlineKeyboardButton(text=t("btn_block"), callback_data=f"set_role:{uid}:pending")])
    rows.append([InlineKeyboardButton(text=t("btn_back"), callback_data="admin:users")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def stats_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back"), callback_data="admin:menu")]
    ])