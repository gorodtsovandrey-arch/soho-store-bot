from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.database import db
from app.keyboards.common import shop_products_kb, payment_method_kb, back_menu_kb

router = Router()


class PurchaseForm(StatesGroup):
    waiting_for_payment = State()


async def safe_edit_or_send(callback: types.CallbackQuery, text: str, reply_markup, parse_mode="Markdown"):
    """Безопасное редактирование - если не получается, удаляем и отправляем новое."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


@router.callback_query(F.data == "menu_buy")
async def buy_cb(callback: types.CallbackQuery):
    products = await db.get_all_products()
    if not products:
        await safe_edit_or_send(callback, "🛒 Товаров пока нет.", back_menu_kb())
        return
    text = "🛒 **Доступные товары:**\n"
    for p in products:
        stock = f"✅ {p['stock']} шт" if p['stock'] > 0 else "❌ нет"
        text += f"\n📦 **{p['name']}** — {p['price']:.2f}$\n📝 {p['description']}\n📊 {stock}\n"
    await safe_edit_or_send(callback, text, shop_products_kb(products))


@router.callback_query(F.data.startswith("buy_"))
async def buy_product_cb(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    if product["stock"] <= 0:
        await callback.answer("❌ Товар закончился", show_alert=True)
        return

    await state.set_state(PurchaseForm.waiting_for_payment)
    await state.update_data(product_id=product_id, amount=product["price"])

    user = await db.get_user(callback.from_user.id)
    balance = user["balance"] if user else 0

    text = (
        f"📦 **{product['name']}**\n\n"
        f"💵 Цена: {product['price']:.2f}$\n"
        f"📊 В наличии: {product['stock']} шт\n\n"
        f"Выберите способ оплаты:"
    )
    await safe_edit_or_send(callback, text, payment_method_kb(balance))


@router.callback_query(F.data == "back_to_shop")
async def back_to_shop_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await buy_cb(callback)
