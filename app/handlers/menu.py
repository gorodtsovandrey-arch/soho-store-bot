from aiogram import Router, F, types

from app.config import CHANNEL_USERNAME
from app.services.subscription import check_subscription
from app.keyboards.common import subscription_kb, profile_kb, back_menu_kb, main_menu_kb
from app.db.database import db
from app.handlers.start import show_main_menu

router = Router()


async def safe_edit_or_send(callback: types.CallbackQuery, text: str, reply_markup, parse_mode="Markdown"):
    """Безопасное редактирование - если не получается, удаляем и отправляем новое."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)


@router.callback_query(F.data == "check_subscription")
async def check_sub_cb(callback: types.CallbackQuery):
    ok = await check_subscription(callback.bot, callback.from_user.id)
    if ok:
        await callback.message.delete()
        await show_main_menu(callback.message)
    else:
        await callback.answer("Вы ещё не подписались на канал!", show_alert=True)


@router.callback_query(F.data == "menu_profile")
async def profile_cb(callback: types.CallbackQuery):
    user = await db.ensure_user(
        callback.from_user.id,
        callback.from_user.username or "",
        callback.from_user.first_name or "",
    )
    text = (
        f"🪪 ID: `{callback.from_user.id}`\n"
        f"👤 @{callback.from_user.username or 'нет'}\n\n"
        f"💵 Баланс: `{user['balance']:.2f}$`\n"
        f"💰 Всего пополнено: `{user['total_deposited']:.2f}$`"
    )
    await safe_edit_or_send(callback, text, profile_kb())


@router.callback_query(F.data == "menu_support")
async def support_cb(callback: types.CallbackQuery):
    text = (
        "🩶 **Поддержка**\n\n"
        "🔄 **Замена товара:**\n"
        "Замена производится только при наличии видео,\n"
        "в течение 30 минут после покупки.\n\n"
        "📩 **Связаться с поддержкой:**\n"
        "👤 @SohoHelper\n\n"
        "⏰ Часы работы: 24/7\n"
        "⚡ Среднее время ответа: 5-10 минут"
    )
    await safe_edit_or_send(callback, text, back_menu_kb())


@router.callback_query(F.data == "menu_rules")
async def rules_cb(callback: types.CallbackQuery):
    text = (
        "📄 **ПРАВИЛА МАГАЗИНА**\n\n"
        "1. Замена товара — только при наличии видео распаковки\n"
        "2. Видео должно быть снято в течение 30 мин после покупки\n"
        "3. Возврат средств — только при наличии брака\n"
        "4. Обмен товара — в течение 7 дней\n"
        "5. Гарантия не распространяется на товары со скидкой\n\n"
        "При покупке вы автоматически соглашаетесь с правилами."
    )
    await safe_edit_or_send(callback, text, back_menu_kb())


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_cb(callback: types.CallbackQuery):
    await callback.message.delete()
    await show_main_menu(callback.message)


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile_cb(callback: types.CallbackQuery):
    user = await db.ensure_user(
        callback.from_user.id,
        callback.from_user.username or "",
        callback.from_user.first_name or "",
    )
    text = (
        f"🪪 ID: `{callback.from_user.id}`\n"
        f"👤 @{callback.from_user.username or 'нет'}\n\n"
        f"💵 Баланс: `{user['balance']:.2f}$`\n"
        f"💰 Всего пополнено: `{user['total_deposited']:.2f}$`"
    )
    await safe_edit_or_send(callback, text, profile_kb())
