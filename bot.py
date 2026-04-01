import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import BOT_TOKEN
from app.db.database import db
from app.handlers import all_routers

logging.basicConfig(level=logging.INFO)


async def main():
    await db.create_tables()
    await db.sync_all_stocks()  # Синхронизируем stock с реальным количеством товаров

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    dp = Dispatcher()

    for router in all_routers:
        dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
