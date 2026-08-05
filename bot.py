import asyncio
import logging

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
BOT_TOKEN = "SIZNING_BOT_TOKENINGIZ"  # @BotFather dan olingan tokenni shu yerga qo'ying

logging.basicConfig(level=logging.INFO)

router = Router()

# ==== ASOSIY MENYU ====
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🛒 Yangi buyurtma")],
        [KeyboardButton(text="📦 Mahsulotlar"), KeyboardButton(text="➕ Mahsulot qo'shish")],
        [KeyboardButton(text="📜 Buyurtmalar tarixi"), KeyboardButton(text="📊 Statistika")],
    ],
    resize_keyboard=True,
)

cancel_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
    resize_keyboard=True,
)


# ==== HOLATLAR (FSM) ====
class AddProduct(StatesGroup):
    name = State()
    price = State()


class NewOrder(StatesGroup):
    choosing = State()
    quantity = State()


# ==== /start ====
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 👋\n\n"
        "Bu bot orqali do'koningiz uchun mahsulotlarni qo'shishingiz, "
        "buyurtma yaratishingiz va umumiy summani avtomatik hisoblashingiz mumkin.\n\n"
        "Quyidagi menyudan kerakli bo'limni tanlang 👇",
        reply_markup=main_menu,
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=main_menu)


# ==== MAHSULOT QO'SHISH ====
@router.message(F.text == "➕ Mahsulot qo'shish")
async def add_product_start(message: Message, state: FSMContext):
    await state.set_state(AddProduct.name)
    await message.answer("Mahsulot nomini kiriting:", reply_markup=cancel_menu)


@router.message(AddProduct.name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddProduct.price)
    await message.answer("Mahsulot narxini kiriting (so'mda, faqat raqam):")


@router.message(AddProduct.price)
async def add_product_price(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", "").replace(" ", "")
    if not text.replace(".", "", 1).isdigit():
        await message.answer("Iltimos, narxni faqat raqamda kiriting. Masalan: 25000")
        return

    data = await state.get_data()
    price = float(text)
    await db.add_product(message.from_user.id, data["name"], price)
    await state.clear()
    await message.answer(
        f"✅ Mahsulot qo'shildi:\n<b>{data['name']}</b> — {price:,.0f} so'm".replace(",", " "),
        parse_mode="HTML",
        reply_markup=main_menu,
    )


# ==== MAHSULOTLAR RO'YXATI ====
@router.message(F.text == "📦 Mahsulotlar")
async def list_products(message: Message):
    products = await db.get_products(message.from_user.id)
    if not products:
        await message.answer("Hozircha mahsulotlar yo'q. Avval mahsulot qo'shing.")
        return

    text = "📦 <b>Mahsulotlar ro'yxati:</b>\n\n"
    for p in products:
        text += f"• {p['name']} — {p['price']:,.0f} so'm\n".replace(",", " ")
    await message.answer(text, parse_mode="HTML")


# ==== YANGI BUYURTMA ====
@router.message(F.text == "🛒 Yangi buyurtma")
async def new_order_start(message: Message, state: FSMContext):
    products = await db.get_products(message.from_user.id)
    if not products:
        await message.answer("Avval mahsulot qo'shishingiz kerak (➕ Mahsulot qo'shish).")
        return

    await state.set_state(NewOrder.choosing)
    await state.update_data(cart=[])
    await message.answer(
        "Buyurtma uchun mahsulotni tanlang:",
        reply_markup=build_products_keyboard(products),
    )


def build_products_keyboard(products):
    buttons = [
        [InlineKeyboardButton(text=f"{p['name']} — {p['price']:,.0f} so'm".replace(",", " "),
                               callback_data=f"pick_{p['id']}")]
        for p in products
    ]
    buttons.append([InlineKeyboardButton(text="✅ Buyurtmani yakunlash", callback_data="finish_order")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(NewOrder.choosing, F.data.startswith("pick_"))
async def pick_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product_by_id(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi.")
        return

    await state.update_data(current_product=product)
    await state.set_state(NewOrder.quantity)
    await callback.message.answer(
        f"<b>{product['name']}</b> dan nechta olasiz? (sonini kiriting)",
        parse_mode="HTML",
        reply_markup=cancel_menu,
    )
    await callback.answer()


@router.message(NewOrder.quantity)
async def set_quantity(message: Message, state: FSMContext):
    if not message.text.strip().isdigit() or int(message.text.strip()) <= 0:
        await message.answer("Iltimos, musbat butun son kiriting. Masalan: 3")
        return

    quantity = int(message.text.strip())
    data = await state.get_data()
    product = data["current_product"]
    cart = data.get("cart", [])

    subtotal = product["price"] * quantity
    cart.append({
        "name": product["name"],
        "price": product["price"],
        "quantity": quantity,
        "subtotal": subtotal,
    })

    await state.update_data(cart=cart)
    await state.set_state(NewOrder.choosing)

    products = await db.get_products(message.from_user.id)
    await message.answer(
        f"✅ Qo'shildi: {product['name']} x {quantity} = {subtotal:,.0f} so'm\n\n"
        "Yana mahsulot qo'shasizmi yoki buyurtmani yakunlaysizmi?".replace(",", " "),
        reply_markup=build_products_keyboard(products),
    )


@router.callback_query(NewOrder.choosing, F.data == "finish_order")
async def finish_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cart = data.get("cart", [])

    if not cart:
        await callback.answer("Savat bo'sh!", show_alert=True)
        return

    total = sum(item["subtotal"] for item in cart)
    await db.create_order(callback.from_user.id, cart, total)

    text = "🧾 <b>Buyurtma yakunlandi:</b>\n\n"
    for item in cart:
        text += (
            f"• {item['name']} x {item['quantity']} = "
            f"{item['subtotal']:,.0f} so'm\n".replace(",", " ")
        )
    text += f"\n💰 <b>Umumiy summa: {total:,.0f} so'm</b>".replace(",", " ")

    await state.clear()
    await callback.message.answer(text, parse_mode="HTML", reply_markup=main_menu)
    await callback.answer()


# ==== BUYURTMALAR TARIXI ====
@router.message(F.text == "📜 Buyurtmalar tarixi")
async def order_history(message: Message):
    orders = await db.get_orders(message.from_user.id, limit=10)
    if not orders:
        await message.answer("Hozircha buyurtmalar yo'q.")
        return

    text = "📜 <b>Oxirgi buyurtmalar:</b>\n\n"
    for o in orders:
        text += f"№{o['id']} | {o['created_at']} | {o['total']:,.0f} so'm\n".replace(",", " ")
    await message.answer(text, parse_mode="HTML")


# ==== STATISTIKA ====
@router.message(F.text == "📊 Statistika")
async def stats(message: Message):
    s = await db.get_stats(message.from_user.id)
    await message.answer(
        f"📊 <b>Statistika:</b>\n\n"
        f"Jami buyurtmalar soni: {s['count']}\n"
        f"Jami tushum: {s['total_sum']:,.0f} so'm".replace(",", " "),
        parse_mode="HTML",
    )


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
