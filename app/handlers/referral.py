from aiogram import Router, F, types

from app.db.database import db
from app.keyboards.common import referral_kb

router = Router()


@router.callback_query(F.data == "profile_referral")
async def referral_cb(callback: types.CallbackQuery):
    await db.ensure_user(
        callback.from_user.id,
        callback.from_user.username or "",
        callback.from_user.first_name or "",
    )

    ref_count = await db.get_referral_count(callback.from_user.id)
    ref_earnings = await db.get_referral_earnings(callback.from_user.id)
    ref_pct = await db.get_referral_percent()

    bot_me = await callback.bot.get_me()
    ref_link = f"https://t.me/{bot_me.username}?start={callback.from_user.id}"

    text = (
        f"👥 **РЕФЕРАЛЬНАЯ СИСТЕМА**\n\n"
        f"👤 Ваши рефералы: {ref_count}\n"
        f"💰 Заработано: {ref_earnings:.2f}$\n"
        f"📊 Бонус: {ref_pct:.0f}% от каждой оплаты реферала\n\n"
        f"Ваша ссылка:\n`{ref_link}`\n\n"
        f"Бонус начисляется автоматически после оплаты реферала."
    )
    await callback.message.edit_text(text, reply_markup=referral_kb(ref_link), parse_mode="Markdown")
