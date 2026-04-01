import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

CHANNEL_ID = os.getenv("CHANNEL_ID", "-1001234567890")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "prada_news")

DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")

CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN", "")

ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",")
ADMIN_IDS = [int(x.strip()) for x in ADMIN_IDS if x.strip()]

REFERRAL_BONUS = float(os.getenv("REFERRAL_BONUS", "1.0"))
