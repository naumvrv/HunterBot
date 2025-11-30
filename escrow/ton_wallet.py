from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.utils import to_nano
from pytonlib import TonlibClient  # Используем pytonlib для отправки
from config import TONCENTER_API_KEY, MNEMONIC  # MNEMONIC из .env
from loguru import logger
import requests
from pathlib import Path

# Инициализация tonlib (глобально)
ton_config = requests.get('https://ton.org/global.config.json').json()
keystore_dir = Path('./keystore')
keystore_dir.mkdir(exist_ok=True)

ton_client = TonlibClient(
    config=ton_config,
    keystore=str(keystore_dir),
    ls_index=0
)

# Кошелёк из MNEMONIC
if MNEMONIC:
    mnemonics, pubkey, privkey, wallet = Wallets.from_mnemonics(
        MNEMONIC.split(), WalletVersionEnum.v4r2, ""
    )
    BOT_WALLET_ADDRESS = wallet.address.to_string(True, True, True)
    logger.info(f"✅ Кошелёк: {BOT_WALLET_ADDRESS}")
else:
    BOT_WALLET_ADDRESS = "EQ_ERROR_NO_MNEMONIC"
    logger.error("❌ MNEMONIC не задан!")

async def send_ton(to_address: str, amount_ton: float, comment: str = "NaumHunterBot"):
    """Отправляет TON через pytonlib"""
    if BOT_WALLET_ADDRESS.startswith("EQ_ERROR"):
        logger.error("❌ Невозможно отправить: нет MNEMONIC")
        return False
    
    try:
        await ton_client.init()
        amount_nano = to_nano(amount_ton)
        
        # Создаём внешнее сообщение для отправки
        ext_msg = wallet.create_transfer_message(
            to_addr=to_address,
            amount=amount_nano,
            seqno=await ton_client.get_seqno(BOT_WALLET_ADDRESS),
            payload=comment.encode()
        ).sign(privkey)
        
        # Отправляем
        await ton_client.send_message(ext_msg)
        logger.info(f"💸 Отправлено {amount_ton} TON на {to_address}")
        await ton_client.close()
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки TON: {e}")
        return False
        