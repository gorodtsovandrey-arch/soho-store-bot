from aiocryptopay import AioCryptoPay, Networks
from app.config import CRYPTOBOT_TOKEN

cryptobot = AioCryptoPay(token=CRYPTOBOT_TOKEN, network=Networks.MAIN_NET) if CRYPTOBOT_TOKEN else None
