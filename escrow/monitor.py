import asyncio
from pytonlib import TonlibClient
from database.db import AsyncSessionLocal
from database.models import Deal
from escrow.ton_wallet import send_ton
from loguru import logger
from config import TONCENTER_API_KEY  # Не используется, но для совместимости
from datetime import datetime, timezone
import requests
from pathlib import Path

# Инициализация TonlibClient (один раз)
ton_config = requests.get('https://ton.org/global.config.json').json()
keystore_dir = Path('./keystore')
keystore_dir.mkdir(exist_ok=True)

client = TonlibClient(
    config=ton_config,
    keystore=str(keystore_dir),
    ls_index=0  # LiteServer index
)

async def check_incoming_ton(bot):
    """Мониторит входящие TON каждые 15 секунд с pytonlib"""
    await client.init()  # Инициализация tonlib
    logger.info("🔍 TonlibClient запущен для мониторинга")
    
    while True:
        try:
            # Получаем транзакции для BOT_WALLET_ADDRESS (из ton_wallet)
            from escrow.ton_wallet import BOT_WALLET_ADDRESS
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
    
    await client.close()