"""
Do'kon hisob-kitob Telegram boti
=================================

Imkoniyatlar:
    📦 Ombor           — mahsulot kiritish (nomi, tannarxi, miqdori)
    💰 Sotish          — mahsulot sotish, ombordan avtomatik ayirish
    💸 Chiqim          — xarajatlarni yozib borish
    💵 Kassa           — kassa ochish / yopish
    📊 Hisobot         — kunlik / haftalik / oylik / yillik / sana bo'yicha
    📄 PDF             — hisobotni PDF shaklida yuklab olish
    📊 Excel           — hisobotni Excel shaklida yuklab olish
    📈 Grafiklar       — kunlik foyda/zarar diagrammasi
    🤖 AI tahlili      — Anthropic API orqali matnli tahlil (ixtiyoriy)
    🌐 Til             — O'zbek(lotin/kirill) / Rus / Ingliz

O'rnatish:
    pip install python-telegram-bot --upgrade openpyxl reportlab matplotlib requests

Ishga tushirish:
    python bot.py

Eslatma:
    1. @BotFather orqali token oling va BOT_TOKEN ga qo'ying.
    2. AI tahlili ishlashi uchun ANTHROPIC_API_KEY ni muhit o'zgaruvchisiga qo'ying (ixtiyoriy).
"""

import os
import re
import logging
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

import database as db
from language import t
from keyboards import (
    main_menu_keyboard,
    cancel_keyboard,
    items_inline_keyboard,
    report_period_keyboard,
    language_keyboard,
)
from reports import generate_excel, generate_pdf, generate_chart

# ---- SOZLAMALAR ----
BOT_TOKEN = "8612572282:AAGNHC7CkXC3foUv1hWNZRkVHgV7IRGUOIM"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- CONVERSATION STATES ----
(
    OMBOR_NAME, OMBOR_PRICE, OMBOR_QTY,
    SALE_QTY, SALE_PRICE,
    EXPENSE_DESC, EXPENSE_AMOUNT,
    CASH_OPEN_AMOUNT, CASH_CLOSE_AMOUNT,
    REPORT_CUSTOM_DATE,
) = range(10)


def get_lang(context):
    return context.user_data.get("lang", "uz_latin")


def is_cancel(text, lang):
    return text == t("cancel", lang)


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(
        t("welcome", lang, name=update.effective_user.first_name),
        reply_markup=main_menu_keyboard(lang),
    )


# ---------------- OMBOR ----------------

async def ombor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(t("ombor_name", lang), reply_markup=cancel_keyboard(lang))
    return OMBOR_NAME


async def ombor_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    context.user_data["new_item_name"] = update.message.text.strip()
    await update.message.reply_text(t("ombor_price", lang))
    return OMBOR_PRICE


async def ombor_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        price = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return OMBOR_PRICE
    context.user_data["new_item_price"] = price
    await update.message.reply_text(t("ombor_qty", lang))
    return OMBOR_QTY


async def ombor_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        qty = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return OMBOR_QTY

    name = context.user_data["new_item_name"]
    price = context.user_data["new_item_price"]
    db.add_item(name, price, qty)

    await update.message.reply_text(
        t("ombor_added", lang, name=name, qty=qty, price=price),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


# ---------------- SOTISH ----------------

async def sale_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    items = db.get_items()
    if not items:
        await update.message.reply_text(t("sale_no_items", lang), reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END
    await update.message.reply_text(t("sale_choose_item", lang), reply_markup=items_inline_keyboard(items))
    return ConversationHandler.END  # tanlov inline callback orqali davom etadi


async def sale_item_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split("_")[1])
    item = db.get_item(item_id)
    context.user_data["sale_item"] = dict(item)
    await query.message.reply_text(
        t("sale_qty", lang, stock=item["quantity"]),
        reply_markup=cancel_keyboard(lang),
    )
    return SALE_QTY


async def sale_qty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        qty = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return SALE_QTY

    item = context.user_data["sale_item"]
    if qty > item["quantity"]:
        await update.message.reply_text(t("sale_not_enough", lang, stock=item["quantity"]))
        return SALE_QTY

    context.user_data["sale_qty"] = qty
    await update.message.reply_text(t("sale_price", lang))
    return SALE_PRICE


async def sale_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        price = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return SALE_PRICE

    item = context.user_data["sale_item"]
    qty = context.user_data["sale_qty"]

    db.add_sale(item["id"], item["name"], qty, price, item["purchase_price"])
    db.update_stock(item["id"], item["quantity"] - qty)

    total = qty * price
    profit = total - (qty * item["purchase_price"])

    await update.message.reply_text(
        t("sale_done", lang, name=item["name"], qty=qty, price=price, total=total, profit=profit),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


# ---------------- CHIQIM ----------------

async def expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(t("expense_desc", lang), reply_markup=cancel_keyboard(lang))
    return EXPENSE_DESC


async def expense_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    context.user_data["expense_desc"] = update.message.text.strip()
    await update.message.reply_text(t("expense_amount", lang))
    return EXPENSE_AMOUNT


async def expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return EXPENSE_AMOUNT

    desc = context.user_data["expense_desc"]
    db.add_expense(desc, amount)
    await update.message.reply_text(
        t("expense_done", lang, desc=desc, amount=amount),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


# ---------------- KASSA ----------------

async def cash_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    status = db.get_cash_status()
    if status:
        await update.message.reply_text(
            t("cash_already_open", lang, date=status["opened_at"][:16].replace("T", " "), amount=status["opening_balance"]),
        )
        await update.message.reply_text(t("cash_close_amount", lang), reply_markup=cancel_keyboard(lang))
        return CASH_CLOSE_AMOUNT
    else:
        await update.message.reply_text(t("cash_open_amount", lang), reply_markup=cancel_keyboard(lang))
        return CASH_OPEN_AMOUNT


async def cash_open_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return CASH_OPEN_AMOUNT
    db.open_cash(amount)
    await update.message.reply_text(t("cash_opened", lang, amount=amount), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


async def cash_close_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return CASH_CLOSE_AMOUNT
    db.close_cash(amount)
    await update.message.reply_text(t("cash_closed", lang, amount=amount), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


# ---------------- HISOBOT ----------------

def period_range(period):
    """Berilgan davr nomi uchun (boshlanish, tugash, label) ni qaytaradi."""
    now = datetime.now()
    if period == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = f"Kunlik ({start.strftime('%d.%m.%Y')})"
    elif period == "weekly":
        start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        label = f"Haftalik ({start.strftime('%d.%m.%Y')} - {now.strftime('%d.%m.%Y')})"
    elif period == "monthly":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        label = f"Oylik ({start.strftime('%m.%Y')})"
    elif period == "yearly":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        label = f"Yillik ({start.strftime('%Y')})"
    else:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        label = "Bugun"
    return start.isoformat(), now.isoformat(), label


async def report_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(t("report_choose_period", lang), reply_markup=report_period_keyboard(lang))


async def report_period_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    period = query.data.split("_", 1)[1]

    if period == "custom":
        await query.message.reply_text(t("report_custom_prompt", lang), reply_markup=cancel_keyboard(lang))
        return REPORT_CUSTOM_DATE

    start_iso, end_iso, label = period_range(period)
    await send_report(query.message, context, start_iso, end_iso, label, lang)
    return ConversationHandler.END


async def report_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)

    match = re.match(r"(\d{2})\.(\d{2})\.(\d{4})\s*-\s*(\d{2})\.(\d{2})\.(\d{4})", update.message.text.strip())
    if not match:
        await update.message.reply_text(t("invalid_date", lang))
        return REPORT_CUSTOM_DATE

    d1, m1, y1, d2, m2, y2 = match.groups()
    try:
        start = datetime(int(y1), int(m1), int(d1))
        end = datetime(int(y2), int(m2), int(d2), 23, 59, 59)
    except ValueError:
        await update.message.reply_text(t("invalid_date", lang))
        return REPORT_CUSTOM_DATE

    label = f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"
    await send_report(update.message, context, start.isoformat(), end.isoformat(), label, lang)
    return ConversationHandler.END


async def send_report(message, context, start_iso, end_iso, label, lang):
    report = db.get_report(start_iso, end_iso)
    context.user_data["last_report"] = report
    context.user_data["last_report_label"] = label

    result_label = t("profit_label", lang) if report["net_profit"] >= 0 else t("loss_label", lang)
    text = t(
        "report_text", lang,
        period=label,
        income=f"{report['total_income']:,.0f}",
        expenses=f"{report['total_expenses']:,.0f}",
        gross_profit=f"{report['total_gross_profit']:,.0f}",
        result_label=result_label,
        net_profit=f"{report['net_profit']:,.0f}",
    )
    await message.reply_text(text, reply_markup=main_menu_keyboard(lang))


# ---------------- PDF / EXCEL / GRAFIK / AI ----------------

async def send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    report = context.user_data.get("last_report")
    if not report:
        await update.message.reply_text(t("no_report_yet", lang))
        return
    await update.message.reply_text(t("generating", lang))
    path = generate_pdf(report, context.user_data.get("last_report_label", ""))
    with open(path, "rb") as f:
        await update.message.reply_document(f, caption=t("pdf_ready", lang))


async def send_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    report = context.user_data.get("last_report")
    if not report:
        await update.message.reply_text(t("no_report_yet", lang))
        return
    await update.message.reply_text(t("generating", lang))
    path = generate_excel(report, context.user_data.get("last_report_label", ""))
    with open(path, "rb") as f:
        await update.message.reply_document(f, caption=t("excel_ready", lang))


async def send_chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    report = context.user_data.get("last_report")
    if not report:
        await update.message.reply_text(t("no_report_yet", lang))
        return
    await update.message.reply_text(t("generating", lang))
    path = generate_chart(report, context.user_data.get("last_report_label", ""))
    with open(path, "rb") as f:
        await update.message.reply_photo(f, caption=t("chart_ready", lang))


async def send_ai_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    report = context.user_data.get("last_report")
    if not report:
        await update.message.reply_text(t("no_report_yet", lang))
        return
    if not ANTHROPIC_API_KEY:
        await update.message.reply_text(t("ai_no_key", lang))
        return

    await update.message.reply_text(t("ai_analyzing", lang))
    try:
        import requests
        prompt = (
            f"Do'kon hisoboti: kirim {report['total_income']:.0f} so'm, "
            f"chiqim {report['total_expenses']:.0f} so'm, "
            f"sof foyda/zarar {report['net_profit']:.0f} so'm. "
            f"Sotuvlar soni: {len(report['sales'])}. "
            "Shu ma'lumotlar asosida qisqa (5-6 gapli) tahlil va tavsiya yozib ber, o'zbek tilida."
        )
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        data = resp.json()
        analysis = "".join(block.get("text", "") for block in data.get("content", []))
        await update.message.reply_text(f"🤖 {analysis}")
    except Exception as e:
        logger.error("AI xatolik: %s", e)
        await update.message.reply_text("❗ AI tahlilida xatolik yuz berdi.")


# ---------------- TIL ----------------

async def lang_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("choose_lang", get_lang(context)), reply_markup=language_keyboard())


async def lang_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_", 1)[1]
    context.user_data["lang"] = lang
    await query.message.reply_text(t("main_menu", lang), reply_markup=main_menu_keyboard(lang))


# ---------------- BEKOR QILISH / XATOLIK ----------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(t("cancelled", lang), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Xatolik:", exc_info=context.error)


# ---------------- MAIN ----------------

def main():
    db.init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Ombor
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📦 Ombor$"), ombor_start)],
        states={
            OMBOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ombor_name)],
            OMBOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ombor_price)],
            OMBOR_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ombor_qty)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

    # Sotish
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Sotish$"), sale_start)],
        states={
            SALE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_qty)],
            SALE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_price)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))
    app.add_handler(CallbackQueryHandler(sale_item_chosen, pattern="^item_"))

    # Chiqim
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💸 Chiqim$"), expense_start)],
        states={
            EXPENSE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_desc)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, expense_amount)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

    # Kassa
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💵 Kassa$"), cash_start)],
        states={
            CASH_OPEN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_open_amount)],
            CASH_CLOSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_close_amount)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

    # Hisobot
    app.add_handler(MessageHandler(filters.Regex("^📊 Hisobot$"), report_start))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(report_period_chosen, pattern="^period_")],
        states={
            REPORT_CUSTOM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_custom_date)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

    # PDF / Excel / Grafik / AI
    app.add_handler(MessageHandler(filters.Regex("^📄 PDF$"), send_pdf))
    app.add_handler(MessageHandler(filters.Regex("^📊 Excel$"), send_excel))
    app.add_handler(MessageHandler(filters.Regex("^📈 Grafiklar$"), send_chart))
    app.add_handler(MessageHandler(filters.Regex("^🤖 AI tahlili$"), send_ai_analysis))

    # Til
    app.add_handler(MessageHandler(filters.Regex("^🌐 Til$"), lang_start))
    app.add_handler(CallbackQueryHandler(lang_chosen, pattern="^lang_"))

    app.add_error_handler(error_handler)

    print("Bot ishga tushdi... To'xtatish uchun Ctrl+C bosing.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import time
    while True:
        try:
            main()
        except Exception as e:
            logger.exception("Bot yiqildi, 5 soniyadan keyin qayta ishga tushadi: %s", e)
            time.sleep(5)
