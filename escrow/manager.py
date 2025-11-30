"""
Менеджер эскроу операций для HunterBot
"""
from loguru import logger
from typing import Optional


async def refund_deal(deal_id: int, amount: float) -> bool:
    """
    Возвращает деньги при отмене сделки или таймауте
    
    Args:
        deal_id: ID сделки
        amount: Сумма для возврата
        
    Returns:
        True если успешно, False если ошибка
    """
    try:
        # TODO: Реализовать через YooMoney API возврат средств
        # В реальной системе нужно:
        # 1. Проверить, что платёж действительно был
        # 2. Создать транзакцию возврата через YooMoney
        # 3. Дождаться подтверждения
        
        logger.info(f"💸 Возврат {amount}₽ по сделке {deal_id}")
        logger.warning("⚠️ Реальный возврат YooMoney не реализован, требуется доработка")
        
        # Для MVP возвращаем True (админ должен вручную вернуть)
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка возврата: {e}")
        return False


async def check_deal_timeout(deal_id: int, expires_at) -> bool:
    """
    Проверяет, истекло ли время сделки
    
    Args:
        deal_id: ID сделки
        expires_at: Время истечения
        
    Returns:
        True если истекло, False если ещё есть время
    """
    from datetime import datetime, timezone
    
    if not expires_at:
        return False
    
    now = datetime.now(timezone.utc)
    
    if now > expires_at:
        logger.warning(f"⏰ Сделка {deal_id} истекла")
        return True
    
    return False


async def calculate_commission(amount: float, is_premium: bool = False) -> float:
    """
    Рассчитывает комиссию для сделки
    
    Args:
        amount: Сумма сделки
        is_premium: Премиум пользователь или нет
        
    Returns:
        Сумма комиссии
    """
    if is_premium:
        return 0.0  # Премиум без комиссии
    
    return amount * 0.019  # 1.9% для обычных пользователей
