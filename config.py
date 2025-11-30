from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")
YOOMONEY_TOKEN = os.getenv("YOOMONEY_TOKEN")
YOOMONEY_WALLET = os.getenv("YOOMONEY_WALLET")
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
MNEMONIC = os.getenv("MNEMONIC", "")  # ← ПЕРЕНЕСЕН ИЗ TON_WALLET