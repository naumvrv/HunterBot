import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger
from config import BOT_TOKEN
from database.db import engine, Base
from parser.avito_parser import start_avito_parser
from escrow.monitor import check_incoming_ton
from bot.handlers.admin import router as admin_router
from bot.handlers.deals import router as deals_router
from bot.handlers.premium import router as premium_router
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def on_startup():
    logger.info("🚀 NaumHunterBot запускается...")
    
    # Создание таблиц БД
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ База данных готова")
    
    # Планировщик парсинга
    scheduler = AsyncIOScheduler()
    scheduler.add_job(start_avito_parser, "interval", minutes=3, args=[bot])
    scheduler.start()
    logger.info("✅ Парсер Avito запущен (каждые 3 мин)")
    
    # Мониторинг TON
    asyncio.create_task(check_incoming_ton(bot))
    logger.info("✅ Мониторинг TON запущен")
    
    logger.info("✅ Бот полностью готов к работе!")

async def main():
    # Подключаем роутеры
    dp.include_router(deals_router)
    dp.include_router(admin_router)
    dp.include_router(premium_router)
    
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())