from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Index
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), nullable=True)
    city = Column(String(50), default="Москва")
    payment_methods = Column(String(200), default="СБП,Тинькофф")
    min_profit_percent = Column(Float, default=4.0)
    is_premium = Column(Boolean, default=False)
    balance_rub = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    avito_url = Column(String(500), unique=True, nullable=False)
    avito_item_id = Column(String(50), unique=True)
    seller_name = Column(String(100))  # ← ДОБАВЛЕНО!
    buyer_ton_address = Column(String(48), nullable=False, default="")  # ← ИСПРАВЛЕНО
    price_rub = Column(Float, nullable=False)
    ton_amount = Column(Float, nullable=False)
    commission_rub = Column(Float, default=0.0)
    profit_percent = Column(Float, nullable=False)
    status = Column(String(20), default="new", index=True)
    yoomoney_payment_id = Column(String(100))
    ton_tx_hash = Column(String(100))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Индексы для производительности
    __table_args__ = (
        Index('ix_deals_status', 'status'),
        Index('ix_deals_user_id', 'user_id'),
    )