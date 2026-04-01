from aiogram import Router, F, types

from app.db.database import db
from app.keyboards.common import back_profile_kb

router = Router()


@router.callback_query(F.data == "profile_orders")
async def order_history_cb(callback: types.CallbackQuery):
    orders = await db.get_order_history(callback.from_user.id)
    if not orders:
        await callback.message.edit_text("📦 История заказов пуста", reply_markup=back_profile_kb())
        return
    text = "📦 **ИСТОРИЯ ЗАКАЗОВ**\n\n"
    for o in orders:
        text += (
            f"📦 {o['product_name']}\n"
            f"   Кол-во: {o['quantity']} шт.\n"
            f"   Цена: {o['total_price']}$\n"
            f"   Статус: {o['status']}\n"
            f"   Дата: {o['created_at'][:10]}\n\n"
        )
    await callback.message.edit_text(text, reply_markup=back_profile_kb())
