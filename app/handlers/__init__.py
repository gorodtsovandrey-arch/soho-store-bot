from app.handlers.start import router as start_router
from app.handlers.menu import router as menu_router
from app.handlers.profile import router as profile_router
from app.handlers.shop import router as shop_router
from app.handlers.payment import router as payment_router
from app.handlers.referral import router as referral_router
from app.handlers.admin import router as admin_router

all_routers = [
    start_router,
    admin_router,
    menu_router,
    profile_router,
    shop_router,
    payment_router,
    referral_router,
]
