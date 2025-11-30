"""
Фильтры для обработчиков HunterBot
"""
from aiogram.filters import Filter
from aiogram.types import Message
from database.db import AsyncSessionLocal
from database.models import User


class IsPremiumFilter(Filter):
    """Проверяет, является ли пользователь премиум"""
    
    async def __call__(self, message: Message) -> bool:
        async with AsyncSessionLocal() as db:
            user = await db.get(User, message.from_user.id)
            return user and user.is_premium


class IsAdminFilter(Filter):
    """Проверяет, является ли пользователь администратором"""
    
    def __init__(self, admin_ids: list):
        self.admin_ids = admin_ids
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in self.admin_ids

