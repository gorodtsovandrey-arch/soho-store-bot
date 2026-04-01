import json
import io
from aiogram import Router, F, types
from aiogram.types import BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.db.database import db
from app.services.cryptobot import cryptobot
from app.keyboards.common import (
    topup_amount_kb, payment_method_kb, payment_confirm_kb, back_profile_kb,
)

router = Router()


class PromoForm(StatesGroup):
    waiting_for_code = State()


async def _pay_referral_bonus(bot, user_id: int, payment_amount: float):
    """Начислить реферальный бонус рефереру после оплаты."""
    user = await db.get_user(user_id)
    if not user or not user["referrer_id"]:
        return
    referrer_id = user["referrer_id"]
    pct = await db.get_referral_percent()
    bonus = payment_amount * pct / 100.0
    if bonus <= 0:
        return
    await db.update_balance(referrer_id, bonus)
    await db.add_referral_bonus(referrer_id, user_id, bonus)
    try:
        await bot.send_message(
            referrer_id,
            f"💰 Реферальный бонус +{bonus:.2f}$ ({pct:.0f}% от {payment_amount:.2f}$)",
        )
    except Exception:
        pass


async def _complete_purchase(callback: types.CallbackQuery, state: FSMContext, amount: float):
    """Завершить покупку товара или пополнение."""
    data = await state.get_data()
    product_id = data.get("product_id")

    if product_id:
        product = await db.get_product(product_id)
        if product:
            # Получаем товар из базы
            item = await db.get_available_item(product_id)
            if not item:
                await callback.message.edit_text(
                    "❌ Товар закончился.\n\n"
                    "К сожалению, все товары этого типа были проданы."
                )
                await state.clear()
                return
            
            # Отмечаем товар как проданный и уменьшаем сток
            await db.mark_item_sold(item["id"], callback.from_user.id)
            await db.decrement_stock(product_id)
            await db.add_order(callback.from_user.id, product["name"], 1, product["price"], amount)
            
            await callback.message.edit_text(
                f"✅ **Покупка успешна!**\n\n"
                f"Товар: {product['name']}\n"
                f"Сумма: {amount:.2f}$\n\n"
                f"Товар отправлен в ЛС!"
            )
            
            # Отправляем товар из базы данных
            item_data = item["item_data"]
            
            # Проверяем, является ли товар JSON (cookies)
            is_json = False
            try:
                json.loads(item_data)
                is_json = True
            except (json.JSONDecodeError, TypeError):
                pass
            
            if is_json:
                # Отправляем JSON как файл
                file_bytes = item_data.encode('utf-8')
                file = BufferedInputFile(file_bytes, filename=f"cookies_{product['name'].replace(' ', '_')}.json")
                await callback.bot.send_document(
                    callback.from_user.id,
                    document=file,
                    caption=f"📦 **Ваш товар:** {product['name']}",
                    parse_mode="Markdown",
                )
            else:
                # Обычный текстовый товар
                await callback.bot.send_message(
                    callback.from_user.id,
                    f"📦 **Ваш товар:** {product['name']}\n\n"
                    f"`{item_data}`",
                    parse_mode="Markdown",
                )
            await _pay_referral_bonus(callback.bot, callback.from_user.id, amount)
    else:
        await db.update_balance(callback.from_user.id, amount)
        updated = await db.get_user(callback.from_user.id)
        await callback.message.edit_text(
            f"✅ **Баланс пополнен на {amount:.2f}$**\n\n"
            f"Новый баланс: {updated['balance']:.2f}$"
        )
        await _pay_referral_bonus(callback.bot, callback.from_user.id, amount)

    await state.clear()


# ── Пополнение баланса ──

@router.callback_query(F.data == "profile_topup")
async def topup_cb(callback: types.CallbackQuery):
    await callback.message.edit_text("Выберите сумму пополнения:", reply_markup=topup_amount_kb())


@router.callback_query(F.data.startswith("topup_"))
async def topup_amount_cb(callback: types.CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    user = await db.get_user(callback.from_user.id)

    await state.update_data(amount=amount)

    text = (
        f"💰 **ПОПОЛНЕНИЕ БАЛАНСА**\n\n"
        f"Сумма: {amount}$\n\n"
        f"Выберите способ оплаты:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=payment_method_kb(user["balance"] if user else 0),
    )


# ── Оплата с баланса ──

@router.callback_query(F.data == "pay_from_balance")
async def pay_balance_cb(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount", 0)

    user = await db.get_user(callback.from_user.id)
    if not user or user["balance"] < amount:
        await callback.answer("❌ Недостаточно средств на балансе", show_alert=True)
        return

    await db.deduct_balance(callback.from_user.id, amount)
    await _complete_purchase(callback, state, amount)


# ── Оплата через CryptoBot ──

@router.callback_query(F.data == "pay_cryptobot")
async def pay_cryptobot_cb(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("amount", 0)

    if not cryptobot:
        await callback.answer("❌ CryptoBot не настроен", show_alert=True)
        return

    try:
        invoice = await cryptobot.create_invoice(
            asset="USDT",
            amount=float(amount),
            description="Оплата Soho Store",
            payload=str(callback.from_user.id),
        )
        await state.update_data(cryptobot_invoice_id=invoice.invoice_id)
        await callback.message.edit_text(
            f"🤖 **CryptoBot Оплата**\n\n"
            f"**Сумма:** {amount} USDT\n\n"
            f"Нажмите 'Оплатить', затем 'Проверить оплату':",
            reply_markup=payment_confirm_kb(invoice.bot_invoice_url),
        )
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка: {e}\n\nПопробуйте другой способ оплаты.",
            reply_markup=back_profile_kb(),
        )


@router.callback_query(F.data == "check_cryptobot_payment")
async def check_payment_cb(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    invoice_id = data.get("cryptobot_invoice_id")
    amount = data.get("amount", 0)

    if not invoice_id or not cryptobot:
        await callback.answer("❌ Инвойс не найден", show_alert=True)
        return

    try:
        invoices = await cryptobot.get_invoices(invoice_ids=[invoice_id])
        if not invoices:
            await callback.answer("❌ Инвойс не найден", show_alert=True)
            return

        invoice = invoices[0]

        if invoice.status == "paid":
            await _complete_purchase(callback, state, amount)
        elif invoice.status == "expired":
            await callback.message.edit_text(
                "❌ Инвойс истёк.", reply_markup=back_profile_kb(),
            )
            await state.clear()
        else:
            await callback.answer("⏳ Оплата ещё не поступила.", show_alert=True)
    except Exception as e:
        await callback.answer(f"❌ Ошибка: {e}", show_alert=True)


# ── Отмена ──

@router.callback_query(F.data == "payment_cancel")
async def payment_cancel_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Оплата отменена", reply_markup=back_profile_kb())


# ── Промокод ──

@router.callback_query(F.data == "use_promocode")
async def use_promocode_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PromoForm.waiting_for_code)
    await callback.message.edit_text("Введите промокод:")
    await callback.answer()


@router.message(PromoForm.waiting_for_code)
async def process_promocode(message: types.Message, state: FSMContext):
    code = message.text.strip()
    promo = await db.get_promo_code(code)

    if not promo:
        await message.answer("❌ Промокод не найден. Попробуйте ещё:")
        return
    if promo["is_used"]:
        await message.answer("❌ Промокод уже использован.")
        return

    await db.use_promo_code(code, message.from_user.id)
    await db.update_balance(message.from_user.id, promo["amount"])
    await message.answer(f"✅ Промокод активирован! +{promo['amount']}$ к балансу")
    await state.clear()
