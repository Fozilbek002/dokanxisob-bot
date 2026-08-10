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
        "ombor_unit": "Bu mahsulot qanday o'lchov birligida hisoblanadi?",
        "ombor_unit_invalid": "Iltimos, tugmalardan birini tanlang.",
        "ombor_price": "1 {unit} kelish (tannarx) narxini kiriting (so'm):",
        "ombor_qty": "Nechta/necha {unit} oldingiz?",
        "ombor_added": "✅ '{name}' omborga qo'shildi: {qty} {unit} x {price} so'm = jami {total} so'm.",
        "ombor_transport_prompt": "Shu yukka (partiyaga) transport/yuk tashish xarajati bo'ldimi? Bo'lsa summasini kiriting (so'm), bo'lmasa \"Yo'q\" tugmasini bosing:",
        "no_transport": "🚫 Yo'q",
        "ombor_transport_summary": "\n🚚 Yuk xarajati: {transport} so'm ({per_unit} so'm/{unit} qo'shildi, tannarxga kiritildi)",
        "ombor_list_header": "📦 Ombordagi mahsulotlar:",
        "ombor_list_empty": "Omborda hozircha mahsulot yo'q. \"📦 Ombor\" tugmasi orqali qo'shing.",
        "ombor_delete_hint": "Mahsulotni o'chirish uchun tugmani bosing:",
        "ombor_deleted": "🗑 Mahsulot omborddan o'chirildi.",
        "sale_list_empty": "Hozircha sotuvlar yo'q.",
        "sale_list_header": "📜 <b>Oxirgi sotuvlar</b> (tahrirlash yoki o'chirish uchun tugmani bosing):",
        "sale_deleted": "🗑 Sotuv bekor qilindi, mahsulot omborga qaytarildi, kassa to'g'irlandi.",
        "sale_not_found": "Bu sotuv topilmadi (avval o'chirilgan bo'lishi mumkin).",
        "sale_edit_qty_prompt": "'{name}' sotuvi uchun yangi miqdorni kiriting:",
        "sale_edit_price_prompt": "Yangi sotish narxini kiriting (so'm):",
        "sale_edited": "✅ Sotuv tahrirlandi, ombor va kassa avtomatik to'g'irlandi.",
        "expense_list_empty": "Hozircha chiqimlar yo'q.",
        "expense_list_header": "📜 <b>Oxirgi chiqimlar</b> (tahrirlash yoki o'chirish uchun tugmani bosing):",
        "expense_deleted": "🗑 Chiqim o'chirildi.",
        "expense_edit_prompt": "Yangi summani kiriting (so'm):",
        "expense_edited": "✅ Chiqim tahrirlandi.",
        # Sotish
        "sale_choose_item": "Qaysi mahsulotni sotasiz?",
        "sale_no_items": "Omborda mahsulot yo'q. Avval /ombor orqali mahsulot qo'shing.",
        "sale_qty": "Necha dona sotildi? (omborda: {stock})",
        "sale_not_enough": "❗ Omborda yetarli emas! Omborda: {stock}",
        "sale_price": "Sotish narxini kiriting (so'm):",
        "sale_choose_date": "Bu sotuv qaysi sanaga tegishli?",
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
        "report_custom_prompt": "Sanani kiriting.\nBir kunlik: 14.06.2026\nOraliq: 14.06.2026-20.06.2026\n(1 kundan 1 yilgacha istalgan oraliqni kiritishingiz mumkin)",
        "report_text": (
            "📊 Hisobot ({period})\n\n"
            "💰 Kirim (sotuvlar): {income} so'm\n"
            "💸 Chiqim (qo'lda kiritilgan): {expenses} so'm\n"
            "🏠 Ijara (kunlik ulush): {recurring} so'm\n"
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
        "ombor_pdf_ready": "📄 Ombor ro'yxati PDF tayyor.",
        "ai_analyzing": "🤖 AI tahlil qilmoqda...",
        "ai_no_key": "🤖 AI tahlili uchun ANTHROPIC_API_KEY sozlanmagan. bot.py faylida sozlang.",
        "invalid_number": "❗ Iltimos, to'g'ri son kiriting.",
        "invalid_date": "❗ Sana formati noto'g'ri. Masalan: 14.06.2026 yoki 14.06.2026-20.06.2026",
        "invalid_date_single": "❗ Sana formati noto'g'ri. Masalan: 14.06.2026",
        # Kassa
        "cash_balance": "💰 Kassadagi joriy summa: {balance} so'm",
        "cash_recent": "Oxirgi harakatlar:",
        "cash_in_prompt": "Kassaga qo'shiladigan summani kiriting (so'm):",
        "cash_out_prompt": "Kassadan olinadigan summani kiriting (so'm):",
        "cash_updated": "✅ Kassa yangilandi.",
        # Doimiy xarajat
        "recurring_current": "⚙️ Joriy oylik ijara: {ijara} so'm\n\nO'zgartirish uchun tanlang:",
        "recurring_ijara_prompt": "Oylik ijara summasini kiriting (so'm):",
        "recurring_saved": "✅ Saqlandi: {amount} so'm/oy. Bu summa kunlik hisobotlarda avtomatik bo'lib hisoblanadi.",
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
