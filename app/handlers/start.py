from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
import os

from app.db.database import db
from app.config import CHANNEL_USERNAME, ADMIN_IDS
from app.services.subscription import check_subscription
from app.keyboards.common import subscription_kb, main_menu_kb, admin_kb

router = Router()

BANNER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "banner.jpg")


async def show_main_menu(message: types.Message):
    user = await db.ensure_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.first_name or "",
    )
    text = (
        f"🪪 ID: `{message.from_user.id}`\n"
        f"💵 Сумма заказов: `{user['total_orders']:.2f}$`\n"
        f"💰 Баланс: `{user['balance']:.2f}$`"
    )
    if os.path.exists(BANNER_PATH):
        photo = FSInputFile(BANNER_PATH)
        await message.answer_photo(photo=photo, caption=text, reply_markup=main_menu_kb(), parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=main_menu_kb(), parse_mode="Markdown")


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    referrer_id = None
    if message.text and len(message.text.split()) > 1:
        try:
            referrer_id = int(message.text.split()[1])
        except (ValueError, IndexError):
            pass

    await db.add_user(user_id, username, first_name, referrer_id)

    # Сохраняем связь реферала (бонус начислится после оплаты)
    if referrer_id and referrer_id != user_id:
        existing = await db.get_referrals(referrer_id)
        already = any(r["referred_id"] == user_id for r in existing)
        if not already:
            await db.add_referral(referrer_id, user_id)

    is_sub = await check_subscription(message.bot, user_id)
    if not is_sub:
        await message.answer(
            "Для использования бота подпишитесь на канал.",
            reply_markup=subscription_kb(CHANNEL_USERNAME),
        )
        return

    await show_main_menu(message)


@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    ref_pct = await db.get_referral_percent()
    user_count = await db.get_user_count()
    await message.answer(
        f"⚙️ **Админ-панель**\n\n"
        f"👥 Пользователей: {user_count}\n"
        f"💰 Реф. процент: {ref_pct:.0f}%",
        reply_markup=admin_kb(),
    )
