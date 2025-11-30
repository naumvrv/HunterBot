from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StateFilter
from database.db import AsyncSessionLocal
from database.models import Deal, User
from escrow.yoomoney import create_payment, check_payment
from escrow.ton_wallet import BOT_WALLET_ADDRESS
from bot.states import DealStates
from datetime import datetime, timedelta
from loguru import logger
import re

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    async with AsyncSessionLocal() as db:
        user = await db.get(User, message.from_user.id)
        if not user:
            user = User(
                id=message.from_user.id, 
                username=message.from_user.username
            )
            db.add(user)
            await db.commit()
            logger.info(f"Новый пользователь: {message.from_user.id}")
    
    await message.answer(
        "🚀 <b>NaumHunterBot</b> — самый безопасный P2P-гарант TON в России\n\n"
        "✅ Автоматический поиск выгодных сделок на Avito\n"
        "🛡️ Полная защита через escrow\n"
        "💰 Комиссия всего 1.9%\n\n"
        "Сейчас ищу свежие объявления...\n\n"
        "<i>Команды:</i>\n"
        "/admin — админ-панель\n"
        "Премиум за 299 ₽/мес — без комиссии + приоритет"
    )

@router.message(F.text.regexp(r"^/deal_(\d+)"))
async def start_deal(message: Message):
    deal_id = int(message.text.split("_")[1])
    
    async with AsyncSessionLocal() as db:
        deal = await db.get(Deal, deal_id)
        if not deal or deal.status != "new":
            await message.answer("❌ Сделка уже занята или завершена")
            return

        # Резервируем сделку
        deal.user_id = message.from_user.id
        deal.status = "waiting_payment"
        await db.commit()

        # Создаем оплату с комиссией 1.9%
        commission = deal.price_rub * 0.019
        total_amount = deal.price_rub + commission
        
        payment = create_payment(total_amount, deal.id)
        deal.yoomoney_payment_id = payment["payment_id"]
        await db.commit()

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💳 Оплатить {total_amount:,.0f} ₽", 
                url=payment["url"]
            )],
            [InlineKeyboardButton(
                text="✅ Я оплатил", 
                callback_data=f"paid_{deal.id}"
            )]
        ])

        await message.answer(
            f"🛒 <b>СДЕЛКА НАЧАТА #{deal.id}</b>\n\n"
            f"📦 Объём: <b>{deal.ton_amount} TON</b>\n"
            f"💰 Цена: <b>{deal.price_rub:,.0f} ₽</b>\n"
            f"💎 Комиссия: <b>{commission:,.0f} ₽ (1.9%)</b>\n"
            f"💳 Итого к оплате: <b>{total_amount:,.0f} ₽</b>\n\n"
            f"⚠️ Деньги замораживаются до получения TON от продавца",
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("paid_"))
async def user_paid(callback: CallbackQuery):
    deal_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as db:
        deal = await db.get(Deal, deal_id)
        if not deal or deal.status != "waiting_payment":
            await callback.answer("❌ Ошибка сделки")
            return

        await callback.message.edit_text("🔄 Проверяю оплату...")
        
        if check_payment(deal.yoomoney_payment_id):
            deal.status = "waiting_ton"
            deal.expires_at = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()
            
            await callback.message.edit_text(
                f"✅ <b>ОПЛАТА ПОЛУЧЕНА!</b>\n\n"
                f"📱 Попроси продавца перевести <b>{deal.ton_amount} TON</b>\n"
                f"💼 На кошелёк бота:\n"
                f"<code>{BOT_WALLET_ADDRESS}</code>\n\n"
                f"⏰ Время на сделку: <b>30 минут</b>\n"
                f"📊 Статус: /status_{deal.id}",
                parse_mode="HTML"
            )
            await callback.answer()
        else:
            await callback.answer("⏳ Платёж ещё не прошёл. Подожди 10–30 секунд.", show_alert=True)

@router.message(StateFilter(DealStates.waiting_for_ton_address))
async def get_ton_address(message: Message, state: FSMContext):
    address = message.text.strip()
    
    # Валидация TON адреса
    if not (address.startswith("EQ") or address.startswith("UQ")) or len(address) != 48:
        await message.answer(
            "❌ Неверный формат TON-адреса!\n\n"
            "✅ Правильные примеры:\n"
            "• <code>EQABC...xyz123</code>\n"
            "• <code>UQDEF...abc456</code>\n\n"
            "Попробуй ещё раз:",
            parse_mode="HTML"
        )
        return

    data = await state.get_data()
    deal_id = data["deal_id"]

    async with AsyncSessionLocal() as db:
        deal = await db.get(Deal, deal_id)
        if not deal:
            await message.answer("❌ Сделка не найдена")
            await state.clear()
            return
            
        deal.buyer_ton_address = address
        await db.commit()

    await message.answer(
        f"✅ <b>Адрес сохранён!</b>\n\n"
        f"💼 TON-адрес: <code>{address}</code>\n\n"
        f"⏰ Ждём {deal.ton_amount} TON от продавца\n"
        f"📊 Статус: /status_{deal.id}",
        parse_mode="HTML"
    )
    await state.clear()

@router.message(Command("status"))
async def deal_status(message: Message):
    # Парсим /status_123
    if "_" in message.text:
        deal_id = int(message.text.split("_")[1])
        async with AsyncSessionLocal() as db:
            deal = await db.get(Deal, deal_id)
            if deal and deal.user_id == message.from_user.id:
                status_emojis = {
                    "new": "🆕",
                    "waiting_payment": "💳", 
                    "waiting_ton": "⏳",
                    "completed": "✅",
                    "timeout": "⏰",
                    "refunded": "💸"
                }
                emoji = status_emojis.get(deal.status, "❓")
                
                await message.answer(
                    f"{emoji} <b>Сделка #{deal.id}</b>\n\n"
                    f"📦 {deal.ton_amount} TON\n"
                    f"💰 {deal.price_rub:,.0f} ₽\n"
                    f"📊 Статус: <b>{deal.status}</b>",
                    parse_mode="HTML"
                )