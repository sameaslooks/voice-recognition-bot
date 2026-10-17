from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram import Bot

from bot import db
from bot.constants import ROLE_ADMIN, ROLE_PENDING, AUTHOR_NAME, GITHUB_PROFILE, GITHUB_REPO
from bot.keyboards import main_menu_kb, back_to_main_kb, format_size, format_duration
from bot.locales import t

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    user = await db.get_user(message.from_user.id)
    if user is None:
        is_first = await db.is_first_user()
        role = ROLE_ADMIN if is_first else ROLE_PENDING
        await db.create_user(message.from_user.id, message.from_user.username, role)
        
        if role == ROLE_ADMIN:
            await message.answer(t("start_admin"))
        else:
            await message.answer(t("start_pending"))
            admins = await db.get_admins()
            name = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
            for admin in admins:
                try:
                    await bot.send_message(
                        admin["user_id"],
                        t("new_request", name=name, uid=message.from_user.id),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
            return

        user = await db.get_user(message.from_user.id)

    role_name = t(f"role_{user['role']}")
    await message.answer(
        t("welcome_back", role=role_name),
        reply_markup=main_menu_kb(user)
    )

@router.message(Command("menu"))
async def cmd_menu(message: Message, user: dict) -> None:
    await message.answer(t("menu_title"), reply_markup=main_menu_kb(user))

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(t("help_text"))

@router.message(Command("author"))
async def cmd_author(message: Message) -> None:
    text = t("about_text", author=AUTHOR_NAME, github_profile=GITHUB_PROFILE, github_repo=GITHUB_REPO)
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)

@router.callback_query(F.data == "about:show")
async def cb_about_show(callback: CallbackQuery) -> None:
    text = t("about_text", author=AUTHOR_NAME, github_profile=GITHUB_PROFILE, github_repo=GITHUB_REPO)
    await callback.message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, user: dict) -> None:
    await callback.message.edit_text(t("menu_title"), reply_markup=main_menu_kb(user))
    await callback.answer()

@router.callback_query(F.data == "user:my_stats")
async def cb_my_stats(callback: CallbackQuery, user: dict) -> None:
    stats = await db.get_user_stats(user["user_id"])
    text = (
        f"{t('stats_title')}\n\n"
        f"{t('stats_voices', count=stats['count'])}\n"
        f"{t('stats_duration', duration=format_duration(stats['duration']))}\n"
        f"{t('stats_size', size=format_size(stats['size']))}"
    )
    await callback.message.edit_text(text, reply_markup=back_to_main_kb(), parse_mode="Markdown")
    await callback.answer()