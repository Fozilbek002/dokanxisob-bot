import asyncio
import logging
from datetime import date, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import database as db

# ==== SOZLAMALAR ====
BOT_TOKEN = "8612572282:AAGbr5bw9u7hIAw9DOTegr6aTTvWRJ8t0WA"

logging.basicConfig(level=logging.INFO)

router = Router()


def fmt(n):
    """Sonni 15 000 kabi formatlab beradi."""
    return f"{n:,.0f}".replace(",", " ")


# ==== ASOSIY MENYU ====
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📥 Mahsulot kiritish"), KeyboardButton(text="💰 Sotish")],
        [KeyboardButton(text="💸 Chiqim qo'shish"), KeyboardButton(text="📦 Ombor")],
        [KeyboardButton(text="📜 Sotuvlar tarixi"), KeyboardButton(text="📊 Statistika")],
    ],
    resize_keyboard=True,
)

period_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📆 Bugun", callback_data="period_today"),
            InlineKeyboardButton(text="🗓 Bu hafta", callback_data="period_week"),
        ],
        [
            InlineKeyboardButton(text="📅 Bu oy", callback_data="period_month"),
            InlineKeyboardButton(text="📅 Bu yil", callback_data="period_year"),
        ],
        [InlineKeyboardButton(text="🔎 Sana oralig'ini kiritish", callback_data="period_custom")],
        [InlineKeyboardButton(text="♾ Hammasi (boshidan)", callback_data="period_all")],
    ]
)

cancel_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
    resize_keyboard=True,
)


# ==== HOLATLAR (FSM) ====
class AddProduct(StatesGroup):
    name = State()
    quantity = State()
    price = State()


class SellProduct(StatesGroup):
    quantity = State()
    price = State()


class AddExpense(StatesGroup):
    name = State()
    amount = State()


class CustomPeriod(StatesGroup):
    date_from = State()
    date_to = State()


def parse_date(text: str):
    """KK.OO.YYYY formatidagi sanani date obyektiga aylantiradi."""
    text = text.strip()
    for sep in [".", "/", "-"]:
        parts = text.split(sep)
        if len(parts) == 3:
            try:
                day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                return date(year, month, day)
            except (ValueError, IndexError):
                continue
    return None


def parse_number(text: str):
    """'1000', '1 000', '1000.5' kabi kiritilgan matnni songa aylantiradi."""
    cleaned = text.strip().replace(" ", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


# ==== /start ====
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Bu bot orqali:\n"
        "• Mahsulot kirimini (necha pulga olganingizni) yozasiz\n"
        "• Sotganingizni qayd qilasiz\n"
        "• Bot avtomatik <b>foyda yoki zararni</b> hisoblab beradi\n\n"
        "Quyidagi menyudan tanlang 👇",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu)


# ==== MAHSULOT KIRITISH (KIRIM) ====
@router.message(F.text == "📥 Mahsulot kiritish")
async def add_product_start(message: Message, state: FSMContext):
    await state.set_state(AddProduct.name)
    await message.answer(
        "Mahsulot nomini kiriting (masalan: Ruchka):",
        reply_markup=cancel_menu,
    )


@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.quantity)
    await message.answer("Nechta dona oldingiz?")


@router.message(AddProduct.quantity)
async def add_product_quantity(message: Message, state: FSMContext):
    qty = parse_number(message.text)
    if qty is None or qty <= 0:
        await message.answer("Iltimos, musbat son kiriting. Masalan: 10")
        return
    await state.update_data(quantity=qty)
    await state.set_state(AddProduct.price)
    await message.answer("Har birini necha so'mdan oldingiz? (tannarx)")


@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    price = parse_number(message.text)
    if price is None or price <= 0:
        await message.answer("Iltimos, narxni to'g'ri kiriting. Masalan: 1000")
        return

    data = await state.get_data()
    name = data["name"]
    qty = data["quantity"]
    total = price * qty

    await db.add_or_update_product(message.from_user.id, name, price, qty)
    await state.clear()
    await message.answer(
        f"✅ Kirim qo'shildi:\n"
        f"<b>{name}</b> — {fmt(qty)} dona x {fmt(price)} so'm = <b>{fmt(total)} so'm</b>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


# ==== OMBOR (mahsulotlar ro'yxati) ====
@router.message(F.text == "📦 Ombor")
async def list_products(message: Message):
    products = await db.get_products(message.from_user.id)
    if not products:
        await message.answer("Omborda hozircha mahsulot yo'q.")
        return

    text = "📦 <b>Ombordagi mahsulotlar:</b>\n\n"
    for p in products:
        text += (
            f"• {p['name']} — qoldiq: {fmt(p['quantity'])} dona, "
            f"tannarx: {fmt(p['purchase_price'])} so'm\n"
        )
    await message.answer(text, parse_mode="HTML")


# ==== SOTISH ====
@router.message(F.text == "💰 Sotish")
async def sell_start(message: Message, state: FSMContext):
    products = await db.get_products(message.from_user.id, only_in_stock=True)
    if not products:
        await message.answer(
            "Sotish uchun omborda mahsulot yo'q. Avval \"📥 Mahsulot kiritish\" orqali kiriting."
        )
        return

    buttons = [
        [InlineKeyboardButton(
            text=f"{p['name']} (qoldiq: {fmt(p['quantity'])})",
            callback_data=f"sell_{p['id']}",
        )]
        for p in products
    ]
    await message.answer(
        "Qaysi mahsulotni sotdingiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data.startswith("sell_"))
async def sell_pick_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    if not product or product["quantity"] <= 0:
        await callback.answer("Bu mahsulot omborda yo'q.", show_alert=True)
        return

    await state.update_data(product=product)
    await state.set_state(SellProduct.quantity)
    await callback.message.answer(
        f"<b>{product['name']}</b> dan nechta sotdingiz? (qoldiq: {fmt(product['quantity'])})",
        parse_mode="HTML",
        reply_markup=cancel_menu,
    )
    await callback.answer()


@router.message(SellProduct.quantity)
async def sell_quantity(message: Message, state: FSMContext):
    qty = parse_number(message.text)
    data = await state.get_data()
    product = data["product"]

    if qty is None or qty <= 0:
        await message.answer("Iltimos, musbat son kiriting.")
        return
    if qty > product["quantity"]:
        await message.answer(
            f"Omborda faqat {fmt(product['quantity'])} dona bor. Kamroq son kiriting."
        )
        return

    await state.update_data(quantity=qty)
    await state.set_state(SellProduct.price)
    suggested = product["sale_price"] or ""
    hint = f" (oxirgi narx: {fmt(product['sale_price'])})" if product["sale_price"] else ""
    await message.answer(f"Har birini necha so'mdan sotdingiz?{hint}")


@router.message(SellProduct.price)
async def sell_price(message: Message, state: FSMContext):
    price = parse_number(message.text)
    if price is None or price <= 0:
        await message.answer("Iltimos, narxni to'g'ri kiriting. Masalan: 5000")
        return

    data = await state.get_data()
    product = data["product"]
    qty = data["quantity"]

    revenue, cost, profit = await db.record_sale(
        message.from_user.id, product["name"], qty, price, product["purchase_price"]
    )
    await db.decrease_stock(product["id"], qty)
    await db.set_sale_price(product["id"], price)

    if profit >= 0:
        result_line = f"✅ Foyda: <b>{fmt(profit)} so'm</b>"
    else:
        result_line = f"🔴 Zarar: <b>{fmt(abs(profit))} so'm</b>"

    await state.clear()
    await message.answer(
        f"🧾 <b>Sotuv qayd etildi:</b>\n\n"
        f"{product['name']} — {fmt(qty)} dona x {fmt(price)} so'm\n"
        f"Tushum: {fmt(revenue)} so'm\n"
        f"Tannarx: {fmt(cost)} so'm\n"
        f"{result_line}",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


# ==== CHIQIM QO'SHISH ====
@router.message(F.text == "💸 Chiqim qo'shish")
async def add_expense_start(message: Message, state: FSMContext):
    await state.set_state(AddExpense.name)
    await message.answer(
        "Chiqim nomini kiriting (masalan: Ijara, Transport):",
        reply_markup=cancel_menu,
    )


@router.message(AddExpense.name)
async def add_expense_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddExpense.amount)
    await message.answer("Summasini kiriting (so'mda):")


@router.message(AddExpense.amount)
async def add_expense_amount(message: Message, state: FSMContext):
    amount = parse_number(message.text)
    if amount is None or amount <= 0:
        await message.answer("Iltimos, summani to'g'ri kiriting. Masalan: 50000")
        return

    data = await state.get_data()
    name = data["name"]
    await db.add_expense(message.from_user.id, name, amount)
    await state.clear()
    await message.answer(
        f"✅ Chiqim qo'shildi:\n<b>{name}</b> — {fmt(amount)} so'm",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


# ==== SOTUVLAR TARIXI ====
@router.message(F.text == "📜 Sotuvlar tarixi")
async def sales_history(message: Message):
    sales = await db.get_sales(message.from_user.id, limit=15)
    if not sales:
        await message.answer("Hozircha sotuvlar yo'q.")
        return

    text = "📜 <b>Oxirgi sotuvlar:</b>\n\n"
    for s in sales:
        sign = "✅" if s["profit"] >= 0 else "🔴"
        text += (
            f"{sign} {s['product_name']} — {fmt(s['quantity'])} dona, "
            f"foyda: {fmt(s['profit'])} so'm ({s['created_at']})\n"
        )
    await message.answer(text, parse_mode="HTML")


# ==== STATISTIKA (davr tanlash) ====
@router.message(F.text == "📊 Statistika")
async def stats_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Qaysi davr uchun hisobot kerak?", reply_markup=period_menu)


async def send_stats_report(message: Message, owner_id: int, date_from: str, date_to: str, title: str):
    s = await db.get_stats(owner_id, date_from, date_to)
    net = s["net_profit"]
    net_line = (
        f"✅ <b>Sof foyda: {fmt(net)} so'm</b>"
        if net >= 0
        else f"🔴 <b>Sof zarar: {fmt(abs(net))} so'm</b>"
    )

    await message.answer(
        f"📊 <b>Hisobot: {title}</b>\n\n"
        f"Jami sotuvlar soni: {s['sale_count']}\n"
        f"Jami tushum: {fmt(s['total_revenue'])} so'm\n"
        f"Jami tannarx (sotilganlar): {fmt(s['total_cost'])} so'm\n"
        f"Sotuvdan foyda: {fmt(s['total_sales_profit'])} so'm\n"
        f"Qo'shimcha chiqimlar: {fmt(s['total_expenses'])} so'm\n\n"
        f"{net_line}",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


@router.callback_query(F.data.startswith("period_"))
async def period_chosen(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("period_", "")
    today = date.today()
    owner_id = callback.from_user.id

    if choice == "today":
        d_from = d_to = today
        title = f"Bugun ({today.strftime('%d.%m.%Y')})"
    elif choice == "week":
        d_from = today - timedelta(days=today.weekday())  # dushanbadan
        d_to = today
        title = f"Bu hafta ({d_from.strftime('%d.%m.%Y')} — {d_to.strftime('%d.%m.%Y')})"
    elif choice == "month":
        d_from = today.replace(day=1)
        d_to = today
        title = f"Bu oy ({d_from.strftime('%d.%m.%Y')} — {d_to.strftime('%d.%m.%Y')})"
    elif choice == "year":
        d_from = today.replace(month=1, day=1)
        d_to = today
        title = f"Bu yil ({d_from.strftime('%d.%m.%Y')} — {d_to.strftime('%d.%m.%Y')})"
    elif choice == "all":
        await callback.message.delete_reply_markup()
        await send_stats_report(callback.message, owner_id, None, None, "Hammasi (boshidan)")
        await callback.answer()
        return
    elif choice == "custom":
        await state.set_state(CustomPeriod.date_from)
        await callback.message.answer(
            "Boshlang'ich sanani kiriting (KK.OO.YYYY), masalan: 14.06.2026",
            reply_markup=cancel_menu,
        )
        await callback.answer()
        return
    else:
        await callback.answer()
        return

    await callback.message.delete_reply_markup()
    await send_stats_report(
        callback.message, owner_id, d_from.isoformat(), d_to.isoformat(), title
    )
    await callback.answer()


@router.message(CustomPeriod.date_from)
async def custom_period_from(message: Message, state: FSMContext):
    parsed = parse_date(message.text)
    if not parsed:
        await message.answer(
            "Sana formati noto'g'ri. Iltimos, KK.OO.YYYY ko'rinishida kiriting, masalan: 14.06.2026"
        )
        return
    await state.update_data(date_from=parsed)
    await state.set_state(CustomPeriod.date_to)
    await message.answer("Tugash sanasini kiriting (KK.OO.YYYY), masalan: 14.07.2026")


@router.message(CustomPeriod.date_to)
async def custom_period_to(message: Message, state: FSMContext):
    parsed = parse_date(message.text)
    if not parsed:
        await message.answer(
            "Sana formati noto'g'ri. Iltimos, KK.OO.YYYY ko'rinishida kiriting, masalan: 14.07.2026"
        )
        return

    data = await state.get_data()
    d_from = data["date_from"]
    d_to = parsed

    if d_to < d_from:
        d_from, d_to = d_to, d_from

    title = f"{d_from.strftime('%d.%m.%Y')} — {d_to.strftime('%d.%m.%Y')}"
    await state.clear()
    await send_stats_report(message, message.from_user.id, d_from.isoformat(), d_to.isoformat(), title)


# ==== ISHGA TUSHIRISH ====
async def main():
    await db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
