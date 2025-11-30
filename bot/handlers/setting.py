from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.db import AsyncSessionLocal
from database.models import User
from loguru import logger

router = Router()

class SettingsStates(StatesGroup):
    waiting_for_city = State()
    waiting_for_profit = State()
    waiting_for_payment = State()

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

@router.callback_query(F.data == "set_city")
async def set_city_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏙 Введи свой город (например: Москва, Санкт-Петербург, Екатеринбург):")
    await state.set_state(SettingsStates.waiting_for_city)
    await callback.answer()

@router.message(SettingsStates.waiting_for_city)
async def process_city(message: Message, state: FSMContext):
    city = message.text.strip()
    async with AsyncSessionLocal() as db:
        user = await db.get(User, message.from_user.id)
        if user:
            user.city = city
            await db.commit()
            await message.answer(f"✅ Город изменён на: {city}")
    await state.clear()

@router.callback_query(F.data == "set_profit")
async def set_profit_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("💰 Введи минимальный процент выгоды (например: 5):")
    await state.set_state(SettingsStates.waiting_for_profit)
    await callback.answer()

@router.message(SettingsStates.waiting_for_profit)
async def process_profit(message: Message, state: FSMContext):
    try:
        profit = float(message.text.strip())
        if profit < 0 or profit > 50:
            await message.answer("❌ Укажи процент от 0 до 50")
            return
        
        async with AsyncSessionLocal() as db:
            user = await db.get(User, message.from_user.id)
            if user:
                user.min_profit_percent = profit
                await db.commit()
                await message.answer(f"✅ Минимальная выгода установлена: {profit}%")
    except ValueError:
        await message.answer("❌ Введи число (например: 5)")
        return
    await state.clear()

@router.callback_query(F.data == "set_payment")
async def set_payment_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "💳 Введи способы оплаты через запятую\n"
        "Например: СБП,Тинькофф,Сбербанк,Qiwi"
    )
    await state.set_state(SettingsStates.waiting_for_payment)
    await callback.answer()

@router.message(SettingsStates.waiting_for_payment)
async def process_payment(message: Message, state: FSMContext):
    payment_methods = message.text.strip()
    async with AsyncSessionLocal() as db:
        user = await db.get(User, message.from_user.id)
        if user:
            user.payment_methods = payment_methods
            await db.commit()
            await message.answer(f"✅ Методы оплаты обновлены: {payment_methods}")
    await state.clear()