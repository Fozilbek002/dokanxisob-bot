"""
language.py — Ko'p tillilik uchun matnlar lug'ati

Hozircha to'liq: O'zbek (lotin)
Qisman: O'zbek (kirill), Rus, Ingliz — kerak bo'lsa to'ldiring
"""

TEXTS = {
    "uz_latin": {
        "welcome": "Assalomu alaykum, {name}! 👋\nDo'kon hisob-kitob botiga xush kelibsiz.",
        "choose_lang": "Tilni tanlang:",
        "main_menu": "Asosiy menyu:",
        "cancel": "❌ Bekor qilish",
        "cancelled": "Amal bekor qilindi.",
        # Ombor
        "ombor_name": "Mahsulot nomini kiriting:",
        "ombor_price": "Kelish (tannarx) narxini kiriting (so'm):",
        "ombor_qty": "Miqdorini kiriting:",
        "ombor_added": "✅ '{name}' omborga qo'shildi: {qty} dona, tannarx {price} so'm.",
        # Sotish
        "sale_choose_item": "Qaysi mahsulotni sotasiz?",
        "sale_no_items": "Omborda mahsulot yo'q. Avval /ombor orqali mahsulot qo'shing.",
        "sale_qty": "Necha dona sotildi? (omborda: {stock})",
        "sale_not_enough": "❗ Omborda yetarli emas! Omborda: {stock}",
        "sale_price": "Sotish narxini kiriting (so'm):",
        "sale_done": "✅ Sotildi: {name} — {qty} dona x {price} so'm = {total} so'm\nFoyda: {profit} so'm",
        # Chiqim
        "expense_desc": "Chiqim izohini kiriting (masalan: ijara, transport):",
        "expense_amount": "Summasini kiriting (so'm):",
        "expense_done": "✅ Chiqim qo'shildi: {desc} — {amount} so'm",
        # Kassa
        "cash_already_open": "Kassa allaqachon ochiq. Ochilgan: {date}, boshlang'ich summa: {amount} so'm",
        "cash_open_amount": "Kassani ochish uchun boshlang'ich summani kiriting (so'm):",
        "cash_opened": "✅ Kassa ochildi. Boshlang'ich summa: {amount} so'm",
        "cash_not_open": "Hozir ochiq kassa yo'q.",
        "cash_close_amount": "Kassani yopish uchun yakuniy summani kiriting (so'm):",
        "cash_closed": "✅ Kassa yopildi. Yakuniy summa: {amount} so'm",
        # Hisobot
        "report_choose_period": "Qaysi davr uchun hisobot kerak?",
        "report_daily": "📅 Kunlik",
        "report_weekly": "📅 Haftalik",
        "report_monthly": "📅 Oylik",
        "report_yearly": "📅 Yillik",
        "report_custom": "📅 Sana tanlash",
        "report_custom_prompt": "Sanani kiriting (KUN.OY.YIL - KUN.OY.YIL), masalan: 01.08.2026-06.08.2026",
        "report_text": (
            "📊 Hisobot ({period})\n\n"
            "💰 Kirim (sotuvlar): {income} so'm\n"
            "💸 Chiqim: {expenses} so'm\n"
            "📦 Sotuvlardan sof foyda: {gross_profit} so'm\n\n"
            "{result_label}: {net_profit} so'm"
        ),
        "profit_label": "✅ SOF FOYDA",
        "loss_label": "🔻 SOF ZARAR",
        "no_report_yet": "Avval /hisobot orqali hisobot ko'ring, keyin PDF/Excel/Grafik oling.",
        "generating": "⏳ Tayyorlanmoqda...",
        "pdf_ready": "📄 PDF hisobot tayyor.",
        "excel_ready": "📊 Excel hisobot tayyor.",
        "chart_ready": "📈 Grafik tayyor.",
        "ai_analyzing": "🤖 AI tahlil qilmoqda...",
        "ai_no_key": "🤖 AI tahlili uchun ANTHROPIC_API_KEY sozlanmagan. bot.py faylida sozlang.",
        "invalid_number": "❗ Iltimos, to'g'ri son kiriting.",
        "invalid_date": "❗ Sana formati noto'g'ri. Masalan: 01.08.2026-06.08.2026",
    },

    "uz_cyrillic": {
        "welcome": "Ассалому алайкум, {name}! 👋\nДўкон ҳисоб-китоб ботига хуш келибсиз.",
        "main_menu": "Асосий меню:",
        "cancel": "❌ Бекор қилиш",
        "cancelled": "Амал бекор қилинди.",
        # Qolgan kalitlar uz_latin'dan meros olinadi (quyida fallback orqali)
    },

    "ru": {
        "welcome": "Здравствуйте, {name}! 👋\nДобро пожаловать в бот учёта магазина.",
        "main_menu": "Главное меню:",
        "cancel": "❌ Отмена",
        "cancelled": "Действие отменено.",
    },

    "en": {
        "welcome": "Hello, {name}! 👋\nWelcome to the shop accounting bot.",
        "main_menu": "Main menu:",
        "cancel": "❌ Cancel",
        "cancelled": "Action cancelled.",
    },
}


def t(key, lang="uz_latin", **kwargs):
    """Berilgan til uchun matnni qaytaradi. Topilmasa uz_latin'dan oladi (fallback)."""
    text = TEXTS.get(lang, {}).get(key) or TEXTS["uz_latin"].get(key, key)
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text
