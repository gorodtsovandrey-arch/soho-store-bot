from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💸 Купить", callback_data="menu_buy")
    b.button(text="🥂 Профиль", callback_data="menu_profile")
    b.button(text="🩶 Поддержка", callback_data="menu_support")
    b.button(text="📄 Правила", callback_data="menu_rules")
    b.adjust(2, 2)
    return b.as_markup()


def profile_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💰 Пополнить баланс", callback_data="profile_topup")
    b.button(text="📦 История заказов", callback_data="profile_orders")
    b.button(text="👥 Реферальная ссылка", callback_data="profile_referral")
    b.button(text="🔙 Назад", callback_data="back_to_menu")
    b.adjust(1)
    return b.as_markup()


def shop_products_kb(products) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        stock_txt = f"({p['stock']} шт)" if p['stock'] > 0 else "(нет в наличии)"
        b.button(
            text=f"📦 {p['name']} — {p['price']:.2f}$ {stock_txt}",
            callback_data=f"buy_{p['id']}",
        )
    b.button(text="🔙 Назад", callback_data="back_to_menu")
    b.adjust(1)
    return b.as_markup()


def back_menu_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data="back_to_menu")
    return b.as_markup()


def back_profile_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data="back_to_profile")
    return b.as_markup()


def subscription_kb(channel_username: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📢 Подписаться", url=f"https://t.me/{channel_username}")
    b.button(text="✅ Проверить подписку", callback_data="check_subscription")
    b.adjust(1)
    return b.as_markup()


def topup_amount_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for v in (1, 5, 10, 25, 50, 100):
        b.button(text=f"💰 {v}$", callback_data=f"topup_{v}")
    b.button(text="🔙 Назад", callback_data="back_to_profile")
    b.adjust(3, 3, 1)
    return b.as_markup()


def payment_method_kb(balance: float) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text=f"💳 С баланса ({balance:.2f}$)", callback_data="pay_from_balance")
    b.button(text="🤖 CryptoBot", callback_data="pay_cryptobot")
    b.button(text="🎫 Промокод", callback_data="use_promocode")
    b.button(text="🔙 Назад", callback_data="back_to_profile")
    b.adjust(1)
    return b.as_markup()


def payment_confirm_kb(invoice_url: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💳 Оплатить", url=invoice_url)
    b.button(text="✅ Проверить оплату", callback_data="check_cryptobot_payment")
    b.button(text="❌ Отмена", callback_data="payment_cancel")
    b.adjust(1)
    return b.as_markup()


def referral_kb(link: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📋 Скопировать ссылку", url=link)
    b.button(text="🔙 Назад", callback_data="back_to_profile")
    b.adjust(1)
    return b.as_markup()


# ── Admin ──

def admin_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="📦 Товары", callback_data="admin_products")
    b.button(text="📊 Статистика", callback_data="admin_stats")
    b.button(text="📢 Рассылка", callback_data="admin_broadcast")
    b.button(text="🎫 Промокод", callback_data="admin_promo")
    b.button(text="💰 Реф. процент", callback_data="admin_ref_percent")
    b.adjust(2, 2, 1)
    return b.as_markup()


def admin_product_list_kb(products) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for p in products:
        b.button(text=f"📦 {p['name']} ({p['stock']} шт)", callback_data=f"admin_prod_{p['id']}")
    b.button(text="➕ Добавить товар", callback_data="admin_add_product")
    b.button(text="🔙 Назад", callback_data="admin_back")
    b.adjust(1)
    return b.as_markup()


def admin_product_edit_kb(product_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✏️ Изменить", callback_data=f"admin_edit_{product_id}")
    b.button(text="📥 Загрузить товары", callback_data=f"admin_upload_{product_id}")
    b.button(text="📋 Просмотр товаров", callback_data=f"admin_view_items_{product_id}")
    b.button(text="🗑 Удалить", callback_data=f"admin_del_{product_id}")
    b.button(text="🔙 Назад", callback_data="admin_products")
    b.adjust(1)
    return b.as_markup()
