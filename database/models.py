from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, BigInteger, Text
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
    buyer_ton_address = Column(String(48), nullable=True, default="")  # ← ИСПРАВЛЕНО: nullable=True
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

class SellerRating(Base):
    """Модель для хранения рейтинга продавцов"""
    __tablename__ = "seller_ratings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_name = Column(String(100), nullable=False, index=True)
    platform = Column(String(20), nullable=False)  # avito, yula, telegram
    total_deals = Column(Integer, default=0)
    successful_deals = Column(Integer, default=0)
    failed_deals = Column(Integer, default=0)
    total_volume_rub = Column(Float, default=0.0)
    avg_response_time = Column(Integer, default=0)  # секунды
    trust_score = Column(Float, default=50.0)  # 0-100
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_seller_platform', 'seller_name', 'platform'),
    )

class SellerReview(Base):
    """Отзывы о продавцах"""
    __tablename__ = "seller_reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    seller_name = Column(String(100), nullable=False, index=True)
    deal_id = Column(Integer, nullable=False)
    user_id = Column(BigInteger, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 звезд
    review_text = Column(Text, nullable=True)
    is_scam = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        Index('ix_reviews_seller', 'seller_name'),
        Index('ix_reviews_deal', 'deal_id'),
    )