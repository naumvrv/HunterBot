from aiogram import Router, F
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice
from database.db import AsyncSessionLocal
from database.models import User
from loguru import logger

router = Router()

@router.message(F.text == "Премиум за 299 ₽/мес")
async def premium_buy(message: Message):
    await message.answer_invoice(
        title="NaumHunter Premium",
        description="⚡ Уведомления каждые 30 сек\n💎 0% комиссии\n⭐ Приоритет в сделках",
        payload="premium_month",
        provider_token="TEST:YOUR_PROVIDER_TOKEN",  # ← ЗАМЕНИ НА РЕАЛЬНЫЙ
        currency="RUB",
        prices=[LabeledPrice(label="Премиум на месяц", amount=29900)],
        start_parameter="naumhunter-premium"
    )

@router.pre_checkout_query()
async def pre_checkout(pre_checkout: PreCheckoutQuery):
    await pre_checkout.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message):
    if message.successful_payment.invoice_payload == "premium_month":
        async with AsyncSessionLocal() as db:
            user = await db.get(User, message.from_user.id)
            if user:
                user.is_premium = True
                await db.commit()
        
        await message.answer(
            "🎉 <b>ПРЕМИУМ АКТИВИРОВАН!</b>\n\n"
            "✅ Уведомления каждые 30 секунд\n"
            "✅ 0% комиссии на сделки\n"
            "✅ Приоритет в очередях\n\n"
            "Спасибо за доверие! 🚀",
            parse_mode="HTML"
        )
        logger.info(f"Премиум активирован для {message.from_user.id}")