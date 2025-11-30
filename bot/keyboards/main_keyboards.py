"""
Клавиатуры для Telegram бота HunterBot
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главная клавиатура"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Мои сделки"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="💎 Премиум"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_deal_keyboard(deal_id: int, payment_url: str) -> InlineKeyboardMarkup:
    """Клавиатура для сделки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{deal_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{deal_id}")]
    ])
    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админская клавиатура"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")]
    ])
    return keyboard

