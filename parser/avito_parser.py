import aiohttp
import re
import asyncio
from loguru import logger
from database.models import Deal, User
from database.db import AsyncSessionLocal
from parser.ton_price import get_ton_price_rub
from aiogram import Bot
from datetime import datetime, timezone

PROXY = "http://user:pass@proxy.soax.com:9000"  # ← ЗАМЕНИ НА СВОЙ

async def parse_avito_once(bot: Bot):
    """Парсит Avito один раз"""
    try:
        market_price = await get_ton_price_rub()
        search_queries = [
            "продам ton", "ton за сбп", "ton за тинькофф", 
            "toncoin", "ton usdt", "продаю ton"
        ]

        async with aiohttp.ClientSession() as session:
            for query in search_queries:
                url = "https://www.avito.ru/web/1"
                params = {
                    "q": query,
                    "pmin": "",
                    "pmax": "",
                    "cd": "1"
                }

                try:
                    async with session.get(
                        url, 
                        params=params, 
                        proxy=PROXY if PROXY else None,
                        timeout=aiohttp.ClientTimeout(total=15),
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    ) as resp:
                        if resp.status != 200:
                            continue
                            
                        # Парсим HTML (упрощенная версия для MVP)
                        text = await resp.text()
                        items = re.findall(
                            r'data-marker="item"\s+[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*data-price="([^"]+)"',
                            text
                        )

                        for item_url, title, price_str in items[:5]:  # Лимит 5 на запрос
                            title_lower = title.lower()
                            price_rub = float(price_str.replace(" ", "").replace("₽", ""))
                            
                            # Ищем TON в заголовке
                            ton_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(ton|тон|toncoin)', title_lower)
                            if not ton_match:
                                continue

                            ton_amount = float(ton_match.group(1).replace(",", "."))
                            if ton_amount < 10:
                                continue

                            price_per_ton = price_rub / ton_amount
                            profit_percent = ((market_price - price_per_ton) / price_per_ton) * 100

                            if profit_percent < 4.0:
                                continue

                            # Проверяем уникальность
                            full_url = f"https://www.avito.ru{item_url}"
                            async with AsyncSessionLocal() as db:
                                exists = await db.execute(
                                    "SELECT id FROM deals WHERE avito_url = :url",
                                    {"url": full_url}
                                )
                                if exists.scalar():
                                    continue

                                # Создаем сделку
                                new_deal = Deal(
                                    avito_url=full_url,
                                    avito_item_id=item_url.split("/")[-1],
                                    seller_name="Avito Seller",  # Парсинг имени сложный, пока заглушка
                                    price_rub=price_rub,
                                    ton_amount=ton_amount,
                                    profit_percent=round(profit_percent, 1)
                                )
                                db.add(new_deal)
                                await db.commit()

                                # Рассылка
                                users_result = await db.execute("SELECT id FROM users")
                                user_ids = [row[0] for row in users_result.fetchall()]

                                deal_text = (
                                    f"🔥 <b>ВЫГОДНАЯ СДЕЛКА!</b> Экономия <b>{profit_percent:.1f}%</b>\n\n"
                                    f"📦 Объём: <b>{ton_amount} TON</b>\n"
                                    f"💰 Цена: <b>{price_rub:,.0f} ₽</b>\n"
                                    f"📈 За 1 TON: <b>{price_per_ton:.0f} ₽</b>\n"
                                    f"💎 Рынок: <b>{market_price:.0f} ₽</b>\n\n"
                                    f"🛒 <b>Купить через гарант:</b> <code>/deal_{new_deal.id}</code>\n"
                                    f"🔗 <a href='{full_url}'>Перейти на Avito</a>"
                                )

                                for user_id in user_ids[:50]:  # Лимит 50 для теста
                                    try:
                                        await bot.send_message(
                                            user_id, 
                                            deal_text, 
                                            parse_mode="HTML",
                                            disable_web_page_preview=True
                                        )
                                    except:
                                        pass

                                logger.success(f"✅ Найдена сделка: {profit_percent:.1f}% ({ton_amount} TON)")

                except Exception as e:
                    logger.error(f"Ошибка парсинга '{query}': {e}")
                
                await asyncio.sleep(3)  # Антибан

    except Exception as e:
        logger.error(f"Критическая ошибка парсера Avito: {e}")

async def start_avito_parser(bot: Bot):
    """Запускает бесконечный парсинг"""
    while True:
        await parse_avito_once(bot)
        await asyncio.sleep(180)  # 3 минуты