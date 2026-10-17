from bot import config

TEXTS = {
    "EN": {
        "role_admin": "Administrator",
        "role_user": "User",
        "role_pending": "Pending",
        
        "start_admin": "👋 You are the first user — you are now an administrator.",
        "start_pending": "👋 Request created. Wait for administrator approval.",
        "new_request": "🔔 **New request!**\nUser {name} (ID: {uid}) is waiting for approval.",
        "welcome_back": "👋 Welcome back! Your role: {role}.",
        
        "menu_title": "Main menu:",
        "help_text": "Send a voice message to get text.\n/menu — main menu.",
        
        "btn_my_stats": "📊 My Stats",
        "btn_admin_panel": "🛠 Admin Panel",
        "btn_users": "👥 Users",
        "btn_global_stats": "📊 Global Stats",
        "btn_back_menu": "◀️ To Menu",
        "btn_back": "◀️ Back",
        "btn_make_admin": "⬆️ Make Admin",
        "btn_make_user": "👤 Make User",
        "btn_block": "🚫 Block",
        
        "stats_title": "📊 **Your Statistics**",
        "global_stats_title": "📊 **Global Service Statistics**",
        "stats_voices": "🎤 Processed voices: **{count}**",
        "stats_duration": "⏱ Total duration: **{duration}**",
        "stats_size": "💾 Total size: **{size}**",
        "stats_privacy": "*Message texts are not saved.*",
        
        "user_info": "👤 {name}\nID: `{uid}`\nRole: {role}\n\n📊 **Statistics:**\nVoices: {count}\nDuration: {duration}\nSize: {size}",
        
        "admin_panel_title": "🛠 Admin Panel",
        "users_list_title": "👥 Users ({count}):",
        "no_users": "No users found.",
        "pending_count": " ({count} new)",
        
        "no_rights": "⛔ Insufficient permissions.",
        "user_not_found": "User not found",
        "last_admin_error": "Cannot demote the last administrator",
        "role_changed": "🔔 **Permissions changed!**\nUser {name} (ID: {uid}) was assigned the role: {role}",
        "done": "Done",
        
        "group_added": "✅ Bot added! Voice messages in this group will be transcribed automatically.",
        "group_denied": "⛔ To add the bot to a group, you must be an approved user (send /start in private messages).",
        
        "loading_model": "🧠 Loading model into memory...",
        "recognizing": "⏳ Recognizing...",
        "in_queue": "⏳ In queue. Ahead of you: {ahead}",
        "in_queue_loading": "⏳ In queue. Ahead of you: {ahead} (loading model)",
        "added_to_queue": "⏳ Added to queue...",
        "recognition_error": "❌ Recognition error: {error}",
        "empty_result": "🤷 Failed to recognize speech.",
        
        "send_start": "Please send /start first.",
        "pending_approval": "⏳ Your request has not been approved yet."
    },
    "RU": {
        "role_admin": "Администратор",
        "role_user": "Пользователь",
        "role_pending": "Ожидает",
        
        "start_admin": "👋 Вы первый пользователь — стали администратором.",
        "start_pending": "👋 Заявка создана. Ожидайте одобрения администратором.",
        "new_request": "🔔 **Новая заявка!**\nПользователь {name} (ID: {uid}) ждет одобрения.",
        "welcome_back": "👋 С возвращением! Ваша роль: {role}.",
        
        "menu_title": "Главное меню:",
        "help_text": "Отправьте голосовое сообщение — получите текст.\n/menu — главное меню.",
        
        "btn_my_stats": "📊 Моя статистика",
        "btn_admin_panel": "🛠 Админ-панель",
        "btn_users": "👥 Пользователи",
        "btn_global_stats": "📊 Общая статистика",
        "btn_back_menu": "◀️ В меню",
        "btn_back": "◀️ Назад",
        "btn_make_admin": "⬆️ Сделать админом",
        "btn_make_user": "👤 Сделать пользователем",
        "btn_block": "🚫 Заблокировать",
        
        "stats_title": "📊 **Ваша статистика**",
        "global_stats_title": "📊 **Общая статистика сервиса**",
        "stats_voices": "🎤 Обработано голосовых: **{count}**",
        "stats_duration": "⏱ Общая длительность: **{duration}**",
        "stats_size": "💾 Общий вес: **{size}**",
        "stats_privacy": "*Тексты сообщений не сохраняются.*",
        
        "user_info": "👤 {name}\nID: `{uid}`\nРоль: {role}\n\n📊 **Статистика:**\nГолосовых: {count}\nДлительность: {duration}\nВес: {size}",
        
        "admin_panel_title": "🛠 Админ-панель",
        "users_list_title": "👥 Пользователи ({count}):",
        "no_users": "Пользователей нет.",
        "pending_count": " ({count} новых)",
        
        "no_rights": "⛔ Недостаточно прав.",
        "user_not_found": "Пользователь не найден",
        "last_admin_error": "Нельзя убрать последнего администратора",
        "role_changed": "🔔 **Изменение прав!**\nПользователю {name} (ID: {uid}) выдана роль: {role}",
        "done": "Готово",
        
        "group_added": "✅ Бот добавлен! Голосовые сообщения в этой группе будут автоматически расшифровываться.",
        "group_denied": "⛔ Для добавления бота в группу вы должны быть одобренным пользователем (нажмите /start в личных сообщениях бота).",
        
        "loading_model": "🧠 Загрузка модели в память...",
        "recognizing": "⏳ Распознаю...",
        "in_queue": "⏳ В очереди. Перед вами: {ahead}",
        "in_queue_loading": "⏳ В очереди. Перед вами: {ahead} (загружается модель)",
        "added_to_queue": "⏳ Добавлено в очередь...",
        "recognition_error": "❌ Ошибка распознавания: {error}",
        "empty_result": "🤷 Не удалось распознать речь.",
        
        "send_start": "Сначала отправьте /start.",
        "pending_approval": "⏳ Ваша заявка ещё не одобрена."
    }
}

def t(key: str, **kwargs) -> str:
    lang = config.LANGUAGE
    text = TEXTS.get(lang, TEXTS["EN"]).get(key, f"Missing key: {key}")
    return text.format(**kwargs) if kwargs else text