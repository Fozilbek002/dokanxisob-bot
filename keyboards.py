"""
keyboards.py — Bot menyu tugmalari
"""

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from language import t


def main_menu_keyboard(lang="uz_latin"):
    buttons = [
        ["📦 Ombor", "📋 Ro'yxat"],
        ["💰 Sotish", "💸 Chiqim"],
        ["💵 Kassa", "📊 Hisobot"],
        ["📄 PDF", "📊 Excel"],
        ["📈 Grafiklar", "🤖 AI tahlili"],
        ["🌐 Til"],
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def cancel_keyboard(lang="uz_latin"):
    return ReplyKeyboardMarkup([[t("cancel", lang)]], resize_keyboard=True)


def items_inline_keyboard(items):
    """Ombordagi mahsulotlar ro'yxatidan tanlash uchun inline tugmalar."""
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                f"{item['name']} (qoldiq: {item['quantity']})",
                callback_data=f"item_{item['id']}",
            )
        ])
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
