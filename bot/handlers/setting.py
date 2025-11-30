from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.db import AsyncSessionLocal
from database.models import User
from loguru import logger

router = Router()

@router.message(F.text == "/settings")
async def settings_cmd(message: Message):
    async with AsyncSessionLocal() as db:
        user = await db.get(User, message.from_user.id)
        if not user:
            await message.answer("❌ Сначала /start")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏙 Город", callback_data="set_city")],
            [InlineKeyboardButton(text="💰 Мин. выгода %", callback_data="set_profit")],
            [InlineKeyboardButton(text="💳 Методы оплаты", callback_data="set_payment")]
        ])
        
        await message.answer(
            f"⚙️ <b>Настройки</b>\n\n"
            f"🏙 Город: {user.city}\n"
            f"💰 Мин. выгода: {user.min_profit_percent}%\n"
            f"💳 Оплата: {user.payment_methods}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

# Добавь callback_query хендлеры для редактирования (FSM аналогично deals)