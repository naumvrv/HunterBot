"""
Оптимизированный модуль для работы с TON кошельком
"""
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.utils import to_nano
from pytonlib import TonlibClient
from config import TONCENTER_API_KEY, MNEMONIC
from loguru import logger
import requests
from pathlib import Path
from typing import Optional

# Глобальные переменные для ленивой инициализации
_ton_client: Optional[TonlibClient] = None
_wallet = None
_privkey = None
BOT_WALLET_ADDRESS = "NOT_INITIALIZED"


def init_wallet_sync():
    """
    Синхронная инициализация кошелька (вызывается при импорте если есть MNEMONIC)
    """
    global _wallet, _privkey, BOT_WALLET_ADDRESS
    
    if not MNEMONIC:
        logger.warning("⚠️ MNEMONIC не задан, TON wallet недоступен")
        BOT_WALLET_ADDRESS = "EQ_ERROR_NO_MNEMONIC"
        return False
    
    try:
        mnemonics, pubkey, _privkey, _wallet = Wallets.from_mnemonics(
            MNEMONIC.split(), WalletVersionEnum.v4r2, ""
        )
        BOT_WALLET_ADDRESS = _wallet.address.to_string(True, True, True)
        logger.info(f"✅ TON Кошелёк инициализирован: {BOT_WALLET_ADDRESS[:10]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации кошелька: {e}")
        BOT_WALLET_ADDRESS = "EQ_ERROR_INIT_FAILED"
        return False


async def get_ton_client() -> Optional[TonlibClient]:
    """
    Получает или создает экземпляр TonlibClient (ленивая инициализация)
    
    Returns:
        TonlibClient или None при ошибке
    """
    global _ton_client
    
    if _ton_client is not None:
        return _ton_client
    
    try:
        # Загружаем конфиг TON
        ton_config = requests.get('https://ton.org/global.config.json', timeout=10).json()
        
        # Создаем директорию для keystore
        keystore_dir = Path('./keystore')
        keystore_dir.mkdir(exist_ok=True)
        
        # Создаем клиент
        _ton_client = TonlibClient(
            config=ton_config,
            keystore=str(keystore_dir),
            ls_index=0
        )
        
        await _ton_client.init()
        logger.info("✅ TonlibClient инициализирован")
        return _ton_client
        
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации TonlibClient: {e}")
        _ton_client = None
        return None


async def close_ton_client():
    """Закрывает соединение TonlibClient"""
    global _ton_client
    
    if _ton_client:
        try:
            await _ton_client.close()
            logger.info("✅ TonlibClient закрыт")
        except Exception as e:
            logger.error(f"Ошибка закрытия TonlibClient: {e}")
        finally:
            _ton_client = None


async def send_ton(to_address: str, amount_ton: float, comment: str = "NaumHunterBot") -> bool:
    """
    Отправляет TON через pytonlib
    
    Args:
        to_address: Адрес получателя
        amount_ton: Количество TON
        comment: Комментарий к переводу
        
    Returns:
        True если успешно, False если ошибка
    """
    global _wallet, _privkey
    
    if BOT_WALLET_ADDRESS.startswith("EQ_ERROR"):
        logger.error("❌ Невозможно отправить: кошелёк не инициализирован")
        return False
    
    if not _wallet or not _privkey:
        logger.error("❌ Wallet или privkey не инициализированы")
        return False
    
    try:
        # Получаем клиент
        client = await get_ton_client()
        if not client:
            logger.error("❌ Не удалось получить TON client")
            return False
        
        # Конвертируем в nano
        amount_nano = to_nano(amount_ton)
        
        # Получаем seqno
        seqno = await client.get_seqno(BOT_WALLET_ADDRESS)
        
        # Создаём сообщение
        ext_msg = _wallet.create_transfer_message(
            to_addr=to_address,
            amount=amount_nano,
            seqno=seqno,
            payload=comment.encode()
        ).sign(_privkey)
        
        # Отправляем
        await client.send_message(ext_msg)
        logger.success(f"💸 Отправлено {amount_ton} TON на {to_address[:10]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки TON: {e}")
        return False


async def get_wallet_balance() -> float:
    """
    Получает баланс кошелька бота
    
    Returns:
        Баланс в TON или 0.0 при ошибке
    """
    if BOT_WALLET_ADDRESS.startswith("EQ_ERROR"):
        return 0.0
    
    try:
        client = await get_ton_client()
        if not client:
            return 0.0
        
        balance_nano = await client.get_balance(BOT_WALLET_ADDRESS)
        balance_ton = balance_nano / 1_000_000_000
        
        return balance_ton
        
    except Exception as e:
        logger.error(f"Ошибка получения баланса: {e}")
        return 0.0


# Инициализируем кошелёк при импорте модуля (синхронно)
init_wallet_sync()
