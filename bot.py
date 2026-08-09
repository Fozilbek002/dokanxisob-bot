"""
Do'kon hisob-kitob Telegram boti
=================================

Imkoniyatlar:
    📦 Ombor              — ombordagi mahsulotlar ro'yxati
    ➕ Mahsulot qo'shish   — yangi mahsulot kiritish
    💰 Sotish             — mahsulot sotish (sana tanlash bilan), kassaga avtomatik kirim
    💸 Chiqim             — xarajatlarni yozib borish
    💵 Kassa              — joriy kassa balansini ko'rish, qo'lda kirim/chiqim
    ⚙️ Doimiy xarajat     — ijara va yuk tashish oylik summasi (kunlik hisobotga bo'linadi)
    📊 Hisobot            — kunlik / haftalik / oylik / yillik / erkin sana oralig'i
    📄 Ombor PDF          — ombordagi mahsulotlar ro'yxati PDF shaklida
    📄 PDF / 📊 Excel / 📈 Grafiklar — hisobot fayllari
    🤖 AI tahlili         — Anthropic API orqali matnli tahlil (ixtiyoriy)
    🌐 Til                — O'zbek(lotin/kirill) / Rus / Ingliz

MUHIM: har bir Telegram foydalanuvchisi (owner_id) faqat o'z ma'lumotlarini ko'radi —
ombor, sotuv, chiqim, kassa va hisobotlar butunlay alohida saqlanadi.
"""

import os
import re
import logging
from datetime import datetime, timedelta, date

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
    items_delete_inline_keyboard,
    date_choice_keyboard,
    cash_actions_keyboard,
    recurring_cost_keyboard,
    report_period_keyboard,
    language_keyboard,
)
from reports import generate_excel, generate_pdf, generate_chart, generate_items_pdf

# ---- SOZLAMALAR ----
BOT_TOKEN = "8612572282:AAGNHC7CkXC3foUv1hWNZRkVHgV7IRGUOIM"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ---- CONVERSATION STATES ----
(
    OMBOR_NAME, OMBOR_PRICE, OMBOR_QTY,
    SALE_ITEM, SALE_QTY, SALE_PRICE, SALE_DATE,
    EXPENSE_DESC, EXPENSE_AMOUNT,
    CASH_IN_AMOUNT, CASH_OUT_AMOUNT,
    RECURRING_AMOUNT,
    REPORT_CUSTOM_DATE,
) = range(13)


def get_lang(context):
    return context.user_data.get("lang", "uz_latin")


def is_cancel(text, lang):
    return text == t("cancel", lang)


def owner_id(update: Update):
    return update.effective_user.id


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


def parse_flexible_date(text):
    """'14.06.2026', '5.6.2026', '14/06/2026' kabi turli formatlarni tushunadi."""
    text = text.strip()
    for sep in [".", "/", "-"]:
        parts = text.split(sep)
        if len(parts) == 3:
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                return date(y, m, d)
            except (ValueError, IndexError):
                continue
    return None


# ---------------- START ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    await update.message.reply_text(
        t("welcome", lang, name=update.effective_user.first_name),
        reply_markup=main_menu_keyboard(lang),
    )


# ---------------- OMBOR (RO'YXAT) ----------------

async def ombor_list_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    items = db.get_items(owner_id(update))
    if not items:
        await update.message.reply_text(t("ombor_list_empty", lang))
        return
    lines = [t("ombor_list_header", lang), ""]
    grand_total = 0
    for item in items:
        line_total = item["quantity"] * item["purchase_price"]
        grand_total += line_total
        lines.append(
            f"• {item['name']} — {fmt(item['quantity'])} {item['unit']}, "
            f"tannarx: {fmt(item['purchase_price'])} so'm/{item['unit']}, "
            f"jami: {fmt(line_total)} so'm"
        )
    lines.append("")
    lines.append(f"💰 <b>Ombordagi umumiy qiymat: {fmt(grand_total)} so'm</b>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
    await update.message.reply_text(
        t("ombor_delete_hint", lang), reply_markup=items_delete_inline_keyboard(items)
    )


async def ombor_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split("_")[1])
    db.delete_item(owner_id(update), item_id)
    await query.message.reply_text(t("ombor_deleted", get_lang(context)))


async def ombor_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    items = db.get_items(owner_id(update))
    if not items:
        await update.message.reply_text(t("ombor_list_empty", lang))
        return
    await update.message.reply_text(t("generating", lang))
    path = generate_items_pdf(items)
    with open(path, "rb") as f:
        await update.message.reply_document(f, caption=t("ombor_pdf_ready", lang))


# ---------------- MAHSULOT QO'SHISH ----------------

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
    db.add_item(owner_id(update), name, price, qty)

    await update.message.reply_text(
        t("ombor_added", lang, name=name, qty=qty, price=price),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


# ---------------- SOTISH ----------------

async def sale_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    items = db.get_items(owner_id(update))
    items = [i for i in items if i["quantity"] > 0]
    if not items:
        await update.message.reply_text(t("sale_no_items", lang), reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END
    await update.message.reply_text(t("sale_choose_item", lang), reply_markup=items_inline_keyboard(items))
    return SALE_ITEM


async def sale_item_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    query = update.callback_query
    await query.answer()
    item_id = int(query.data.split("_")[1])
    item = db.get_item(owner_id(update), item_id)
    if not item:
        await query.message.reply_text(t("sale_no_items", lang), reply_markup=main_menu_keyboard(lang))
        return ConversationHandler.END
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

    context.user_data["sale_price"] = price
    await update.message.reply_text(t("sale_choose_date", lang), reply_markup=date_choice_keyboard())
    return SALE_DATE


async def finalize_sale(message, context, oid, sale_date_iso=None):
    lang = get_lang(context)
    item = context.user_data["sale_item"]
    qty = context.user_data["sale_qty"]
    price = context.user_data["sale_price"]

    total, profit = db.add_sale(oid, item["id"], item["name"], qty, price, item["purchase_price"], sale_date_iso)
    db.update_stock(oid, item["id"], item["quantity"] - qty)
    db.cash_add(oid, total, note=f"Sotuv: {item['name']}")

    date_line = f"\n📅 Sana: {sale_date_iso}" if sale_date_iso else ""
    await message.reply_text(
        t("sale_done", lang, name=item["name"], qty=qty, price=price, total=total, profit=profit) + date_line,
        reply_markup=main_menu_keyboard(lang),
    )
    context.user_data.pop("sale_item", None)
    context.user_data.pop("sale_qty", None)
    context.user_data.pop("sale_price", None)


async def sale_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    oid = owner_id(update)
    if query.data == "date_today":
        await finalize_sale(query.message, context, oid, None)
        return ConversationHandler.END
    else:
        await query.message.reply_text(
            "Sanani kiriting (KK.OO.YYYY), masalan: 14.06.2026",
            reply_markup=cancel_keyboard(get_lang(context)),
        )
        return SALE_DATE


async def sale_date_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    parsed = parse_flexible_date(update.message.text)
    if not parsed:
        await update.message.reply_text(t("invalid_date_single", lang))
        return SALE_DATE
    await finalize_sale(update.message, context, owner_id(update), parsed.isoformat())
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
    oid = owner_id(update)
    db.add_expense(oid, desc, amount)
    db.cash_add(oid, -amount, note=f"Chiqim: {desc}")
    await update.message.reply_text(
        t("expense_done", lang, desc=desc, amount=amount),
        reply_markup=main_menu_keyboard(lang),
    )
    return ConversationHandler.END


# ---------------- KASSA ----------------

async def cash_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    oid = owner_id(update)
    balance = db.get_cash_balance(oid)
    recent = db.get_cash_ledger(oid, limit=5)

    lines = [t("cash_balance", lang, balance=fmt(balance))]
    if recent:
        lines.append("")
        lines.append(t("cash_recent", lang))
        for r in recent:
            sign = "+" if r["amount"] >= 0 else ""
            when = r["created_at"][:16].replace("T", " ")
            lines.append(f"{sign}{fmt(r['amount'])} so'm — {r['note']} ({when})")

    await update.message.reply_text("\n".join(lines), reply_markup=cash_actions_keyboard())


async def cash_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    if query.data == "cash_in":
        await query.message.reply_text(t("cash_in_prompt", lang), reply_markup=cancel_keyboard(lang))
        return CASH_IN_AMOUNT
    else:
        await query.message.reply_text(t("cash_out_prompt", lang), reply_markup=cancel_keyboard(lang))
        return CASH_OUT_AMOUNT


async def cash_in_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return CASH_IN_AMOUNT
    db.cash_add(owner_id(update), amount, note="Qo'lda kirim")
    await update.message.reply_text(t("cash_updated", lang), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


async def cash_out_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return CASH_OUT_AMOUNT
    db.cash_add(owner_id(update), -amount, note="Qo'lda chiqim")
    await update.message.reply_text(t("cash_updated", lang), reply_markup=main_menu_keyboard(lang))
    return ConversationHandler.END


# ---------------- DOIMIY XARAJAT (IJARA / YUK) ----------------

async def recurring_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    oid = owner_id(update)
    current = db.get_recurring_costs(oid)
    ijara = current.get("ijara", 0)
    yuk = current.get("yuk", 0)
    await update.message.reply_text(
        t("recurring_current", lang, ijara=fmt(ijara), yuk=fmt(yuk)),
        reply_markup=recurring_cost_keyboard(),
    )


async def recurring_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = get_lang(context)
    category = "ijara" if query.data == "rec_ijara" else "yuk"
    context.user_data["recurring_category"] = category
    prompt = t("recurring_ijara_prompt", lang) if category == "ijara" else t("recurring_yuk_prompt", lang)
    await query.message.reply_text(prompt, reply_markup=cancel_keyboard(lang))
    return RECURRING_AMOUNT


async def recurring_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)
    try:
        amount = float(update.message.text.replace(",", "."))
    except ValueError:
        await update.message.reply_text(t("invalid_number", lang))
        return RECURRING_AMOUNT

    category = context.user_data.get("recurring_category", "ijara")
    db.set_recurring_cost(owner_id(update), category, amount)
    await update.message.reply_text(
        t("recurring_saved", lang, amount=fmt(amount)),
        reply_markup=main_menu_keyboard(lang),
    )
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
    await send_report(query.message, context, owner_id(update), start_iso, end_iso, label, lang)
    return ConversationHandler.END


# Bitta sana ("14.06.2026") yoki oraliq ("14.06.2026-20.06.2026" / "14.06.2026 - 20.06.2026")
DATE_RANGE_RE = re.compile(
    r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})"
    r"(?:\s*-\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4}))?"
)


async def report_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = get_lang(context)
    if is_cancel(update.message.text, lang):
        return await cancel(update, context)

    match = DATE_RANGE_RE.match(update.message.text.strip())
    if not match:
        await update.message.reply_text(t("invalid_date", lang))
        return REPORT_CUSTOM_DATE

    d1, m1, y1, d2, m2, y2 = match.groups()
    try:
        start = datetime(int(y1), int(m1), int(d1))
        if d2 and m2 and y2:
            end = datetime(int(y2), int(m2), int(d2), 23, 59, 59)
        else:
            end = start.replace(hour=23, minute=59, second=59)
    except ValueError:
        await update.message.reply_text(t("invalid_date", lang))
        return REPORT_CUSTOM_DATE

    if end < start:
        start, end = end.replace(hour=0, minute=0, second=0), start.replace(hour=23, minute=59, second=59)

    label = f"{start.strftime('%d.%m.%Y')} - {end.strftime('%d.%m.%Y')}"
    await send_report(update.message, context, owner_id(update), start.isoformat(), end.isoformat(), label, lang)
    return ConversationHandler.END


async def send_report(message, context, oid, start_iso, end_iso, label, lang):
    report = db.get_report(oid, start_iso, end_iso)
    context.user_data["last_report"] = report
    context.user_data["last_report_label"] = label

    result_label = t("profit_label", lang) if report["net_profit"] >= 0 else t("loss_label", lang)
    text = t(
        "report_text", lang,
        period=label,
        income=fmt(report["total_income"]),
        expenses=fmt(report["total_expenses"]),
        recurring=fmt(report["recurring_for_period"]),
        gross_profit=fmt(report["total_gross_profit"]),
        result_label=result_label,
        net_profit=fmt(report["net_profit"]),
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
            f"chiqim {report['total_expenses_all']:.0f} so'm (shundan doimiy xarajat ulushi "
            f"{report['recurring_for_period']:.0f} so'm), "
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

    # Ombor ro'yxati va PDF
    app.add_handler(MessageHandler(filters.Regex("^📦 Ombor$"), ombor_list_show))
    app.add_handler(MessageHandler(filters.Regex("^📄 Ombor PDF$"), ombor_pdf))
    app.add_handler(CallbackQueryHandler(ombor_delete_callback, pattern="^delitem_"))

    # Mahsulot qo'shish
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ Mahsulot qo'shish$"), ombor_start)],
        states={
            OMBOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ombor_name)],
            OMBOR_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ombor_price)],
            OMBOR_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ombor_qty)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

    # Sotish (mahsulot -> son -> narx -> sana)
    app.add_handler(ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💰 Sotish$"), sale_start)],
        states={
            SALE_ITEM: [CallbackQueryHandler(sale_item_chosen, pattern="^item_")],
            SALE_QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_qty)],
            SALE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sale_price)],
            SALE_DATE: [
                CallbackQueryHandler(sale_date_callback, pattern="^date_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sale_date_text),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

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
    app.add_handler(MessageHandler(filters.Regex("^💵 Kassa$"), cash_show))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(cash_action_callback, pattern="^cash_")],
        states={
            CASH_IN_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_in_amount)],
            CASH_OUT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cash_out_amount)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌"), cancel)],
    ))

    # Doimiy xarajat (ijara / yuk)
    app.add_handler(MessageHandler(filters.Regex("^⚙️ Doimiy xarajat$"), recurring_start))
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(recurring_category_callback, pattern="^rec_")],
        states={
            RECURRING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recurring_amount)],
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
