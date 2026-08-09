"""
keyboards.py — Bot menyu tugmalari
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from language import t


def main_menu_keyboard(lang="uz_latin"):
    buttons = [
        ["📦 Ombor", "🗑 Mahsulot o'chirish"],
        ["➕ Mahsulot qo'shish", "💰 Sotish"],
        ["📜 Sotuvlar tarixi", "💸 Chiqim"],
        ["📜 Chiqimlar tarixi", "💵 Kassa"],
        ["⚙️ Doimiy xarajat", "📊 Hisobot"],
        ["📄 Ombor PDF", "📄 PDF"],
        ["📊 Excel", "📈 Grafiklar"],
        ["🤖 AI tahlili", "🌐 Til"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def cancel_keyboard(lang="uz_latin"):
    return ReplyKeyboardMarkup([[t("cancel", lang)]], resize_keyboard=True)


def unit_choice_keyboard(lang="uz_latin"):
    """Mahsulot birligini tanlash: dona, kg, litr, metr."""
    buttons = [
        ["📦 Dona", "⚖️ Kg"],
        ["🧴 Litr", "📏 Metr"],
        [t("cancel", lang)],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def items_inline_keyboard(items):
    """Ombordagi mahsulotlar ro'yxatidan tanlash uchun inline tugmalar."""
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                f"{item['name']} (qoldiq: {item['quantity']} {item['unit']})",
                callback_data=f"item_{item['id']}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def items_delete_inline_keyboard(items):
    """Har bir mahsulotni o'chirish uchun tugmalar."""
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                f"🗑 {item['name']} o'chirish",
                callback_data=f"delitem_{item['id']}",
            )
        ])
    return InlineKeyboardMarkup(buttons)


def sales_inline_keyboard(sales):
    """Har bir sotuv uchun tahrirlash/o'chirish tugmalari."""
    buttons = []
    for s in sales:
        label = f"{s['item_name']} — {s['quantity']} x {s['sale_price']} so'm ({s['sold_at'][:10]})"
        buttons.append([InlineKeyboardButton(label, callback_data="noop")])
        buttons.append([
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"sale_edit_{s['id']}"),
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"sale_del_{s['id']}"),
        ])
    return InlineKeyboardMarkup(buttons)


def expenses_inline_keyboard(expenses):
    """Har bir chiqim uchun tahrirlash/o'chirish tugmalari."""
    buttons = []
    for e in expenses:
        label = f"{e['description']} — {e['amount']} so'm ({e['created_at'][:10]})"
        buttons.append([InlineKeyboardButton(label, callback_data="noop")])
        buttons.append([
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"exp_edit_{e['id']}"),
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"exp_del_{e['id']}"),
        ])
    return InlineKeyboardMarkup(buttons)


def date_choice_keyboard():
    buttons = [
        [InlineKeyboardButton("📆 Bugun", callback_data="date_today")],
        [InlineKeyboardButton("🗓 Boshqa sana kiritish", callback_data="date_custom")],
    ]
    return InlineKeyboardMarkup(buttons)


def cash_actions_keyboard():
    buttons = [
        [InlineKeyboardButton("➕ Qo'lda kirim qo'shish", callback_data="cash_in")],
        [InlineKeyboardButton("➖ Qo'lda chiqim (pul olish)", callback_data="cash_out")],
    ]
    return InlineKeyboardMarkup(buttons)


def recurring_cost_keyboard():
    buttons = [
        [InlineKeyboardButton("🏠 Ijara", callback_data="rec_ijara")],
        [InlineKeyboardButton("🚚 Yuk tashish", callback_data="rec_yuk")],
    ]
    return InlineKeyboardMarkup(buttons)


def report_period_keyboard(lang="uz_latin"):
    buttons = [
        [InlineKeyboardButton(t("report_daily", lang), callback_data="period_daily")],
        [InlineKeyboardButton(t("report_weekly", lang), callback_data="period_weekly")],
        [InlineKeyboardButton(t("report_monthly", lang), callback_data="period_monthly")],
        [InlineKeyboardButton(t("report_yearly", lang), callback_data="period_yearly")],
        [InlineKeyboardButton(t("report_custom", lang), callback_data="period_custom")],
    ]
    return InlineKeyboardMarkup(buttons)


def language_keyboard():
    buttons = [
        [InlineKeyboardButton("🇺🇿 O'zbek (lotin)", callback_data="lang_uz_latin")],
        [InlineKeyboardButton("🇺🇿 Ўзбек (кирилл)", callback_data="lang_uz_cyrillic")],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")],
    ]
    return InlineKeyboardMarkup(buttons)
