BOT_TEXTS = {
    "welcome_phone": {
        "ru": "Добро пожаловать 👋\nПожалуйста, поделитесь своим номером телефона, чтобы продолжить.",
        "en": "Welcome 👋\nPlease share your phone number to continue.",
        "uz": "Xush kelibsiz 👋\nDavom etish uchun telefon raqamingizni ulashing."
    },
    "request_phone": {
        "ru": "Пожалуйста, поделитесь своим номером телефона, чтобы продолжить.",
        "en": "Please share your phone number to continue.",
        "uz": "Davom etish uchun telefon raqamingizni ulashing."
    },
    "waiting_activation": {
        "ru": "⏳ Ваш аккаунт ожидает подтверждения.\nВы получите доступ вскоре после подтверждения.",
        "en": "⏳ Your account is awaiting confirmation.\nYou will get access soon after confirmation.",
        "uz": "⏳ Hisobingiz tasdiqlanishni kutmoqda.\nTasdiqlangandan so'ng tez orada ruxsat olasiz."
    },
    "open_panel": {
        "ru": "✅ Откройте панель отгрузок:",
        "en": "✅ Open the shipping panel:",
        "uz": "✅ Yuk tashish panelini oching:"
    },
    "error_own_phone": {
        "ru": "❌ Пожалуйста, отправьте свой собственный номер телефона",
        "en": "❌ Please send your own phone number",
        "uz": "❌ Iltimos, o'zingizning telefon raqamingizni yuboring"
    },
    "error_start_first": {
        "ru": "❌ Пожалуйста, сначала используйте команду /start",
        "en": "❌ Please use the /start command first",
        "uz": "❌ Iltimos, oldin /start buyrug'idan foydalaning"
    },
    "phone_saved": {
        "ru": "✅ Телефон сохранен. Ваш аккаунт будет активирован после проверки.",
        "en": "✅ Phone saved. Your account will be activated after verification.",
        "uz": "✅ Telefon saqlandi. Tekshiruvdan so'ng hisobingiz faollashadi."
    },
    "btn_share_phone": {
        "ru": "📱 Поделиться номером телефона",
        "en": "📱 Share phone number",
        "uz": "📱 Telefon raqamini ulashish"
    },
    "btn_open_panel": {
        "ru": "📦 Открыть Отгрузки",
        "en": "📦 Open Deliveries",
        "uz": "📦 Yuk tashishni ochish"
    },
    "settings_prompt": {
        "ru": "⚙️ Выберите язык:",
        "en": "⚙️ Choose language:",
        "uz": "⚙️ Tilni tanlang:"
    },
    "language_changed": {
        "ru": "✅ Язык успешно изменен на Русский.",
        "en": "✅ Language successfully changed to English.",
        "uz": "✅ Til muvaffaqiyatli O'zbek tiliga o'zgartirildi."
    }
}

def get_text(key: str, lang: str = "ru") -> str:
    """Helper to fetch translated text."""
    if key not in BOT_TEXTS:
        return key
    
    translations = BOT_TEXTS[key]
    return translations.get(lang, translations.get("ru", key))
