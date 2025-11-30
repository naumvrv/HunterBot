import asyncio
from database.db import AsyncSessionLocal
from database.models import Deal
from escrow.ton_wallet import send_ton, get_ton_client, close_ton_client, BOT_WALLET_ADDRESS
from loguru import logger
from config import TONCENTER_API_KEY  # Не используется, но для совместимости
from datetime import datetime, timezone

async def check_incoming_ton(bot):
    """Мониторит входящие TON каждые 15 секунд с pytonlib"""
    client = await get_ton_client()
    if not client:
        logger.error("❌ Не удалось инициализировать TON client для мониторинга")
        return
    
    logger.info("🔍 TonlibClient запущен для мониторинга")
    
    try:
        while True:
        try:
            # Получаем транзакции для BOT_WALLET_ADDRESS (из ton_wallet)
            from escrow.ton_wallet import BOT_WALLET_ADDRESS
            
            if BOT_WALLET_ADDRESS.startswith("EQ_ERROR"):
                logger.warning("⚠️ TON wallet недоступен, мониторинг пропущен")
                await asyncio.sleep(60)
                continue
            
            transactions = await client.get_transactions(
                address=BOT_WALLET_ADDRESS,
                limit=30
            )
            
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    "SELECT id, buyer_ton_address, ton_amount, user_id FROM deals "
                    "WHERE status = 'waiting_ton' AND expires_at > NOW()"
                )
                active_deals = result.fetchall()
                
                for deal_row in active_deals:
                    deal_id, buyer_address, ton_amount, user_id = deal_row
                    
                    for tx in transactions:
                        if tx.get('in_msg', {}).get('value') and not tx.get('ton_tx_hash'):
                            incoming_ton = int(tx['in_msg']['value']) / 1_000_000_000
                            if abs(incoming_ton - ton_amount) < 0.05:
                                # Совпадение!
                                await db.execute(
                                    "UPDATE deals SET status = 'completed', ton_tx_hash = :tx_hash "
                                    "WHERE id = :deal_id",
                                    {"tx_hash": tx['utime'], "deal_id": deal_id}
                                )
                                await db.commit()
                                
                                # Отправляем TON покупателю (минус комиссия)
                                commission_ton = ton_amount * 0.01
                                success = await send_ton(buyer_address, ton_amount - commission_ton)
                                
                                await bot.send_message(
                                    user_id,
                                    f"✅ <b>Сделка #{deal_id} завершена!</b>\n"
                                    f"💰 Получено: {ton_amount - commission_ton:.3f} TON\n"
                                    f"💎 Комиссия: {commission_ton:.3f} TON",
                                    parse_mode="HTML"
                                )
                                logger.success(f"Сделка {deal_id} завершена: +{commission_ton:.3f} TON")
                                break
                
                # Автоотмена
                await db.execute(
                    "UPDATE deals SET status = 'timeout' WHERE status = 'waiting_ton' AND expires_at < NOW()"
                )
                await db.commit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка мониторинга TON: {e}")
        
        await asyncio.sleep(15)
    except KeyboardInterrupt:
        logger.info("Мониторинг TON остановлен")
    finally:
        await close_ton_client()