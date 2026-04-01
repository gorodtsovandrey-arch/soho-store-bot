from aiogram import Bot
from aiogram.enums import ChatMemberStatus

DISABLE_SUBSCRIPTION_CHECK = False


async def check_subscription(bot: Bot, user_id: int) -> bool:
    if DISABLE_SUBSCRIPTION_CHECK:
        return True
    from app.config import CHANNEL_ID
    try:
        member = await bot.get_chat_member(chat_id=int(CHANNEL_ID), user_id=user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR,
        )
    except Exception:
        return False
