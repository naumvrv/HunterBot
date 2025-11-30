from loguru import logger

def format_deal_notification(deal, profit_percent, market_price):
    """Форматирует текст уведомления"""
    return f"""
🔥 ВЫГОДНАЯ СДЕЛКА! Экономия {profit_percent:.1f}%

📦 {deal.ton_amount} TON
💰 {deal.price_rub:,} ₽ ({deal.price_rub / deal.ton_amount:.1f} ₽/TON)
📈 Рынок: {market_price:.1f} ₽

Купить: /deal_{deal.id}
Ссылка: {deal.avito_url}
    """.strip()