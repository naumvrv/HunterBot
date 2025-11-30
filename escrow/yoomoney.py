from yoomoney import Client
from config import YOOMONEY_TOKEN
from loguru import logger

if YOOMONEY_TOKEN:
    client = Client(YOOMONEY_TOKEN)
else:
    logger.error("❌ YOOMONEY_TOKEN не настроен!")
    client = None

def create_payment(amount: float, deal_id: int) -> dict:
    """Создает платежную ссылку"""
    if not client:
        return {"url": "", "payment_id": f"error_{deal_id}"}
        
    try:
        from config import YOOMONEY_WALLET
        payment = client.create_payment(
            to=YOOMONEY_WALLET,  # Используй кошелек из .env
            amount=amount,
            label=f"deal_{deal_id}",
            quickpay_form="shop",
            targets="Покупка TON через NaumHunterBot",
            successURL="https://t.me/NaumHunterBot",
            payment_type="PC"
        )
        logger.info(f"💳 Создана оплата #{deal_id}: {amount} ₽")
        return {
            "url": payment.confirmation.confirmation_url,
            "payment_id": payment.id
        }
    except Exception as e:
        logger.error(f"❌ Ошибка создания платежа: {e}")
        return {"url": "", "payment_id": f"error_{deal_id}"}

def check_payment(payment_id: str) -> bool:
    """Проверяет статус платежа"""
    if not client:
        return False
        
    try:
        deal_id = payment_id.split('_')[-1] if '_' in payment_id else payment_id
        history = client.operation_history(label=f"deal_{deal_id}")
        
        for operation in history.operations:
            if operation.status == "success":
                logger.info(f"✅ Платеж #{deal_id} подтвержден")
                return True
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка проверки платежа {payment_id}: {e}")
        return False