import aiohttp
from loguru import logger

async def get_ton_price_rub() -> float:
    """Получает актуальный курс TON/RUB"""
    try:
        async with aiohttp.ClientSession() as session:
            # Bybit P2P
            async with session.get(
                "https://api.bybit.com/v5/market/p2p/ticker",
                params={"category": "spot", "symbol": "TONUSDT"},
                timeout=10
            ) as resp:
                data = await resp.json()
                bybit_price = float(data["result"]["list"][0]["lastPrice"]) * 97  # Примерный курс USD/RUB

            # Fallback на фиксированный курс
            final_price = max(bybit_price, 80.0)  # Минимум 80₽
            logger.info(f"📈 Курс TON: {final_price:.2f} ₽")
            return round(final_price, 2)
            
    except Exception as e:
        logger.error(f"Ошибка получения курса TON: {e}")
        return 87.0  # Надежный fallback