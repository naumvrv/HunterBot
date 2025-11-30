"""
Настройка системы логирования для HunterBot
"""
import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


def setup_logging():
    """
    Настраивает систему логирования с ротацией файлов
    """
    # Удаляем стандартный handler
    logger.remove()
    
    # Добавляем красивый вывод в консоль
    logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Создаем директорию для логов
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Логи общих событий
    logger.add(
        logs_dir / "bot_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Новый файл каждый день
        retention="30 days",  # Хранить 30 дней
        compression="zip",  # Сжимать старые логи
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
    )
    
    # Отдельные логи для ошибок
    logger.add(
        logs_dir / "errors_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="60 days",  # Ошибки хранить дольше
        compression="zip",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}"
    )
    
    # Логи парсинга
    logger.add(
        logs_dir / "parsing_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="14 days",
        compression="zip",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: "parser" in record["name"]
    )
    
    # Логи сделок
    logger.add(
        logs_dir / "deals_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",  # Сделки хранить 3 месяца
        compression="zip",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        filter=lambda record: "deal" in record["message"].lower() or "сделка" in record["message"].lower()
    )
    
    logger.info("✅ Система логирования настроена")


def log_deal_created(deal_id: int, ton_amount: float, price_rub: float, profit_percent: float):
    """Логирует создание сделки"""
    logger.info(f"📝 DEAL_CREATED | ID: {deal_id} | TON: {ton_amount} | Price: {price_rub}₽ | Profit: {profit_percent:.1f}%")


def log_deal_status_changed(deal_id: int, old_status: str, new_status: str):
    """Логирует изменение статуса сделки"""
    logger.info(f"🔄 DEAL_STATUS_CHANGED | ID: {deal_id} | {old_status} → {new_status}")


def log_payment_received(deal_id: int, amount: float):
    """Логирует получение платежа"""
    logger.info(f"💰 PAYMENT_RECEIVED | Deal: {deal_id} | Amount: {amount}₽")


def log_ton_sent(deal_id: int, address: str, amount: float):
    """Логирует отправку TON"""
    logger.info(f"💸 TON_SENT | Deal: {deal_id} | To: {address} | Amount: {amount} TON")


def log_parser_found(source: str, ton_amount: float, price: float, profit: float):
    """Логирует найденное объявление"""
    logger.debug(f"🔍 FOUND | Source: {source} | TON: {ton_amount} | Price: {price}₽ | Profit: {profit:.1f}%")


def log_user_registered(user_id: int, username: str):
    """Логирует регистрацию нового пользователя"""
    logger.info(f"👤 NEW_USER | ID: {user_id} | Username: @{username if username else 'None'}")


def log_premium_activated(user_id: int):
    """Логирует активацию премиума"""
    logger.info(f"💎 PREMIUM_ACTIVATED | User: {user_id}")

