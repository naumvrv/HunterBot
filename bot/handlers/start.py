from aiogram import Router
from aiogram.types import Message

router = Router()

@router.message()
async def catch_all(message: Message):
    # Редирект в deals.py /start
    await message.answer("Используй /start для начала работы")