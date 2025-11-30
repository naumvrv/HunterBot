"""
Централизованная система обработки ошибок для HunterBot
"""
import functools
from typing import Callable
from loguru import logger
from aiogram import Bot
from aiogram.types import Message
from config import ADMIN_ID


class BotError(Exception):
    """Базовый класс для ошибок бота"""
    pass


class DatabaseError(BotError):
    """Ошибки базы данных"""
    pass


class PaymentError(BotError):
    """Ошибки платежной системы"""
    pass


class TONError(BotError):
    """Ошибки TON blockchain"""
    pass


class ParsingError(BotError):
    """Ошибки парсинга"""
    pass


def handle_errors(fallback_value=None, notify_admin=False):
    """
    Декоратор для обработки ошибок в async функциях
    
    Args:
        fallback_value: Значение, которое вернется при ошибке
        notify_admin: Отправлять ли уведомление админу
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except DatabaseError as e:
                logger.error(f"❌ Database error in {func.__name__}: {e}")
                if notify_admin:
                    await notify_admin_about_error(f"Database Error in {func.__name__}", str(e))
                return fallback_value
            except PaymentError as e:
                logger.error(f"❌ Payment error in {func.__name__}: {e}")
                if notify_admin:
                    await notify_admin_about_error(f"Payment Error in {func.__name__}", str(e))
                return fallback_value
            except TONError as e:
                logger.error(f"❌ TON error in {func.__name__}: {e}")
                if notify_admin:
                    await notify_admin_about_error(f"TON Error in {func.__name__}", str(e))
                return fallback_value
            except ParsingError as e:
                logger.error(f"❌ Parsing error in {func.__name__}: {e}")
                return fallback_value
            except Exception as e:
                logger.exception(f"❌ Unexpected error in {func.__name__}: {e}")
                if notify_admin:
                    await notify_admin_about_error(f"Critical Error in {func.__name__}", str(e))
                return fallback_value
        return wrapper
    return decorator


async def notify_admin_about_error(title: str, error_message: str):
    """
    Отправляет уведомление админу об ошибке
    
    Args:
        title: Заголовок ошибки
        error_message: Сообщение об ошибке
    """
    try:
        from main import bot  # Импорт внутри функции во избежание циклических зависимостей
        
        if ADMIN_ID and ADMIN_ID > 0:
            text = f"🚨 <b>{title}</b>\n\n<code>{error_message[:500]}</code>"
            await bot.send_message(ADMIN_ID, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление админу: {e}")


async def safe_send_message(bot: Bot, user_id: int, text: str, **kwargs) -> bool:
    """
    Безопасная отправка сообщения с обработкой ошибок
    
    Args:
        bot: Экземпляр бота
        user_id: ID пользователя
        text: Текст сообщения
        **kwargs: Дополнительные параметры
        
    Returns:
        True если успешно, False если ошибка
    """
    try:
        await bot.send_message(user_id, text, **kwargs)
        return True
    except Exception as e:
        logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        return False


async def safe_edit_message(message: Message, text: str, **kwargs) -> bool:
    """
    Безопасное редактирование сообщения
    
    Args:
        message: Объект сообщения
        text: Новый текст
        **kwargs: Дополнительные параметры
        
    Returns:
        True если успешно, False если ошибка
    """
    try:
        await message.edit_text(text, **kwargs)
        return True
    except Exception as e:
        logger.warning(f"Не удалось отредактировать сообщение: {e}")
        return False


def validate_env_variables():
    """
    Проверяет наличие всех необходимых переменных окружения
    
    Raises:
        ValueError: Если отсутствуют критичные переменные
    """
    from config import BOT_TOKEN, DB_URL, ADMIN_ID
    
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN не установлен")
    
    if not DB_URL:
        errors.append("DB_URL не установлен")
    
    if not ADMIN_ID or ADMIN_ID == 0:
        errors.append("ADMIN_ID не установлен")
    
    if errors:
        error_text = "\n".join([f"  - {err}" for err in errors])
        raise ValueError(f"Отсутствуют критичные переменные окружения:\n{error_text}")
    
    logger.info("✅ Все критичные переменные окружения установлены")


class RetryMechanism:
    """Механизм повторных попыток для нестабильных операций"""
    
    @staticmethod
    async def retry_async(func: Callable, max_attempts: int = 3, delay: float = 1.0):
        """
        Повторяет async функцию при ошибках
        
        Args:
            func: Функция для выполнения
            max_attempts: Максимум попыток
            delay: Задержка между попытками (секунды)
            
        Returns:
            Результат функции или None
        """
        import asyncio
        
        for attempt in range(1, max_attempts + 1):
            try:
                return await func()
            except Exception as e:
                if attempt == max_attempts:
                    logger.error(f"Все {max_attempts} попытки провалились: {e}")
                    return None
                
                logger.warning(f"Попытка {attempt}/{max_attempts} провалилась: {e}. Повтор через {delay}с...")
                await asyncio.sleep(delay)
        
        return None

