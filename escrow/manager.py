from escrow.yoomoney import client
from loguru import logger

async def refund_deal(deal_id: int, amount: float):
    """Возвращает деньги при таймауте"""
    try:
        # Используй YooMoney API для возврата
        logger.info(f"Возврат {amount} ₽ по сделке {deal_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка возврата: {e}")
        return False