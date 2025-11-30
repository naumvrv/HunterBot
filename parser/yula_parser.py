# Парсер объявлений с Юлы для HunterBot
import aiohttp
import re
import asyncio
from loguru import logger
from database.models import Deal, User
from database.db import AsyncSessionLocal
from parser.ton_price import get_ton_price_rub
from aiogram import Bot
from datetime import datetime, timezone

YULA_BASE_URL = "https://youla.ru"

async def parse_yula_once(bot: Bot):
    """Парсит Юлу один раз"""
    try:
        market_price = await get_ton_price_rub()
        search_queries = [
            "ton крипта", "тонкоин", "продам ton", 
            "ton за рубли", "toncoin продажа"
        ]

        async with aiohttp.ClientSession() as session:
            for query in search_queries:
                url = f"{YULA_BASE_URL}/search"
                params = {
                    "q": query,
                    "attributes[sort]": "date_published"
                }

                try:
                    async with session.get(
                        url, 
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=15),
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8"
                        }
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(f"Юла вернула статус {resp.status} для '{query}'")
                            continue
                            
                        text = await resp.text()
                        
                        # Парсим объявления (упрощенная версия, может требовать адаптации)
                        # Юла использует JSON в data-state
                        json_match = re.search(r'data-state="([^"]+)"', text)
                        if not json_match:
                            logger.warning(f"Не найден data-state для '{query}'")
                            continue
                        
                        import html
                        import json
                        json_data = html.unescape(json_match.group(1))
                        
                        try:
                            data = json.loads(json_data)
                            products = data.get("feed", {}).get("products", [])
                        except:
                            logger.warning(f"Не удалось распарсить JSON для '{query}'")
                            continue

                        for product in products[:5]:  # Лимит 5 на запрос
                            try:
                                title = product.get("name", "").lower()
                                price_rub = float(product.get("price", 0))
                                product_id = product.get("id", "")
                                item_url = f"{YULA_BASE_URL}/product/{product_id}"
                                
                                if price_rub == 0:
                                    continue
                                
                                # Ищем TON в заголовке
                                ton_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(ton|тон|toncoin)', title)
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
                                async with AsyncSessionLocal() as db:
                                    exists = await db.execute(
                                        "SELECT id FROM deals WHERE avito_url = :url",
                                        {"url": item_url}
                                    )
                                    if exists.scalar():
                                        continue

                                    # Создаем сделку
                                    new_deal = Deal(
                                        avito_url=item_url,
                                        avito_item_id=f"yula_{product_id}",
                                        seller_name="Youla Seller",
                                        price_rub=price_rub,
                                        ton_amount=ton_amount,
                                        profit_percent=round(profit_percent, 1)
                                    )
                                    db.add(new_deal)
                                    await db.commit()

                                    # Рассылка
                                    users_result = await db.execute("SELECT id FROM users WHERE is_premium = TRUE OR 1=1")
                                    user_ids = [row[0] for row in users_result.fetchall()]

                                    deal_text = (
                                        f"🔥 <b>ВЫГОДНАЯ СДЕЛКА С ЮЛЫ!</b> Экономия <b>{profit_percent:.1f}%</b>\n\n"
                                        f"📦 Объём: <b>{ton_amount} TON</b>\n"
                                        f"💰 Цена: <b>{price_rub:,.0f} ₽</b>\n"
                                        f"📈 За 1 TON: <b>{price_per_ton:.0f} ₽</b>\n"
                                        f"💎 Рынок: <b>{market_price:.0f} ₽</b>\n\n"
                                        f"🛒 <b>Купить через гарант:</b> <code>/deal_{new_deal.id}</code>\n"
                                        f"🔗 <a href='{item_url}'>Перейти на Юлу</a>"
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

                                    logger.success(f"✅ Найдена сделка на Юле: {profit_percent:.1f}% ({ton_amount} TON)")
                            
                            except Exception as e:
                                logger.error(f"Ошибка обработки продукта: {e}")
                                continue

                except Exception as e:
                    logger.error(f"Ошибка парсинга Юлы '{query}': {e}")
                
                await asyncio.sleep(3)  # Антибан

    except Exception as e:
        logger.error(f"Критическая ошибка парсера Юлы: {e}")

async def start_yula_parser(bot: Bot):
    """Вызывается планировщиком каждые 5 минут"""
    await parse_yula_once(bot)