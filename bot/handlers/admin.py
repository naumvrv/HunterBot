from aiogram import Router, F
from aiogram.types import Message
from database.db import AsyncSessionLocal
from database.models import Deal, User
from config import ADMIN_ID
from loguru import logger
import asyncio

router = Router()

@router.message(F.text == "/admin")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Доступ запрещён")
        return

    async with AsyncSessionLocal() as db:
        # Исправлено для SQLAlchemy 2.x
        result = await db.execute(
            "SELECT id, ton_amount, price_rub, status FROM deals ORDER BY id DESC LIMIT 20"
        )
        deals = result.fetchall()

        text = "👨‍💼 <b>АДМИН-ПАНЕЛЬ NaumHunterBot</b>\n\n"
        total_earned = 0
        
        for deal_row in deals:
            deal_id, ton_amount, price_rub, status = deal_row
            if status == "completed":
                commission = price_rub * 0.019  # 1.9%
                total_earned += commission
            text += f"#{deal_id} | {ton_amount} TON | {price_rub:,.0f}₽ | {status}\n"

        text += f"\n💰 <b>Заработано сегодня:</b> {total_earned:,.0f} ₽"

        await message.answer(text, parse_mode="HTML")

@router.message(F.text.startswith("/broadcast"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
        
    text = message.text.replace("/broadcast ", "", 1)
    if not text:
        await message.answer("❌ Укажи текст для рассылки")
        return
        
    async with AsyncSessionLocal() as db:
        result = await db.execute("SELECT id FROM users")
        users = result.fetchall()
        
    sent = 0
    for user_row in users:
        user_id = user_row[0]
        try:
            await message.bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.05)  # Rate limit
        except:
            continue
            
    await message.answer(f"✅ Рассылка завершена. Отправлено: {sent} сообщений")