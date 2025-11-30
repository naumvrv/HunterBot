"""
Система рейтинга продавцов для HunterBot
"""
from database.db import AsyncSessionLocal
from database.models import SellerRating, SellerReview
from loguru import logger
from datetime import datetime, timezone
from typing import Optional, Dict


async def get_seller_rating(seller_name: str, platform: str = "avito") -> Optional[Dict]:
    """
    Получает рейтинг продавца
    
    Args:
        seller_name: Имя продавца
        platform: Платформа (avito, yula, telegram)
        
    Returns:
        Словарь с данными рейтинга или None
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            "SELECT * FROM seller_ratings WHERE seller_name = :name AND platform = :platform",
            {"name": seller_name, "platform": platform}
        )
        rating = result.fetchone()
        
        if not rating:
            return None
        
        return {
            "seller_name": rating[1],
            "platform": rating[2],
            "total_deals": rating[3],
            "successful_deals": rating[4],
            "failed_deals": rating[5],
            "total_volume_rub": rating[6],
            "trust_score": rating[8],
            "success_rate": (rating[4] / rating[3] * 100) if rating[3] > 0 else 0
        }


async def update_seller_rating(
    seller_name: str, 
    platform: str,
    deal_successful: bool,
    deal_volume: float
) -> bool:
    """
    Обновляет рейтинг продавца после сделки
    
    Args:
        seller_name: Имя продавца
        platform: Платформа
        deal_successful: Успешна ли сделка
        deal_volume: Объем сделки в рублях
        
    Returns:
        True если успешно
    """
    try:
        async with AsyncSessionLocal() as db:
            # Ищем существующий рейтинг
            result = await db.execute(
                "SELECT id, total_deals, successful_deals, failed_deals, total_volume_rub, trust_score "
                "FROM seller_ratings WHERE seller_name = :name AND platform = :platform",
                {"name": seller_name, "platform": platform}
            )
            existing = result.fetchone()
            
            if existing:
                # Обновляем существующий
                rating_id, total, successful, failed, volume, trust = existing
                
                new_total = total + 1
                new_successful = successful + (1 if deal_successful else 0)
                new_failed = failed + (0 if deal_successful else 1)
                new_volume = volume + deal_volume
                
                # Рассчитываем новый trust_score
                success_rate = (new_successful / new_total) * 100
                volume_factor = min(new_volume / 100000, 1.0)  # До 100k₽ максимум
                
                new_trust = (success_rate * 0.7) + (volume_factor * 30)
                new_trust = max(0, min(100, new_trust))
                
                await db.execute(
                    "UPDATE seller_ratings SET "
                    "total_deals = :total, successful_deals = :successful, "
                    "failed_deals = :failed, total_volume_rub = :volume, "
                    "trust_score = :trust, last_seen = :now "
                    "WHERE id = :id",
                    {
                        "total": new_total,
                        "successful": new_successful,
                        "failed": new_failed,
                        "volume": new_volume,
                        "trust": new_trust,
                        "now": datetime.now(timezone.utc),
                        "id": rating_id
                    }
                )
            else:
                # Создаем новый
                from database.models import SellerRating
                new_rating = SellerRating(
                    seller_name=seller_name,
                    platform=platform,
                    total_deals=1,
                    successful_deals=1 if deal_successful else 0,
                    failed_deals=0 if deal_successful else 1,
                    total_volume_rub=deal_volume,
                    trust_score=80.0 if deal_successful else 20.0
                )
                db.add(new_rating)
            
            await db.commit()
            logger.info(f"✅ Обновлён рейтинг продавца: {seller_name}")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка обновления рейтинга: {e}")
        return False


async def add_seller_review(
    seller_name: str,
    deal_id: int,
    user_id: int,
    rating: int,
    review_text: str = "",
    is_scam: bool = False
) -> bool:
    """
    Добавляет отзыв о продавце
    
    Args:
        seller_name: Имя продавца
        deal_id: ID сделки
        user_id: ID пользователя
        rating: Оценка 1-5
        review_text: Текст отзыва
        is_scam: Является ли скамом
        
    Returns:
        True если успешно
    """
    try:
        from database.models import SellerReview
        
        async with AsyncSessionLocal() as db:
            review = SellerReview(
                seller_name=seller_name,
                deal_id=deal_id,
                user_id=user_id,
                rating=rating,
                review_text=review_text,
                is_scam=is_scam
            )
            db.add(review)
            await db.commit()
            
            logger.info(f"✅ Добавлен отзыв о продавце {seller_name}: {rating}/5")
            return True
            
    except Exception as e:
        logger.error(f"Ошибка добавления отзыва: {e}")
        return False


async def get_seller_reviews(seller_name: str, limit: int = 10) -> list:
    """
    Получает последние отзывы о продавце
    
    Args:
        seller_name: Имя продавца
        limit: Количество отзывов
        
    Returns:
        Список отзывов
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            "SELECT rating, review_text, is_scam, created_at "
            "FROM seller_reviews WHERE seller_name = :name "
            "ORDER BY created_at DESC LIMIT :limit",
            {"name": seller_name, "limit": limit}
        )
        reviews = result.fetchall()
        
        return [
            {
                "rating": r[0],
                "review_text": r[1],
                "is_scam": r[2],
                "created_at": r[3]
            }
            for r in reviews
        ]


def format_seller_rating(rating_data: Dict) -> str:
    """
    Форматирует данные рейтинга для отображения
    
    Args:
        rating_data: Данные рейтинга
        
    Returns:
        Отформатированная строка
    """
    if not rating_data:
        return "📊 <b>Рейтинг продавца:</b> Нет данных"
    
    trust = rating_data["trust_score"]
    
    if trust >= 80:
        trust_emoji = "✅"
        trust_level = "НАДЁЖНЫЙ"
    elif trust >= 60:
        trust_emoji = "⚠️"
        trust_level = "СРЕДНИЙ"
    else:
        trust_emoji = "❌"
        trust_level = "НИЗКИЙ"
    
    text = f"📊 <b>Рейтинг продавца:</b>\n\n"
    text += f"{trust_emoji} Доверие: <b>{trust:.0f}/100</b> ({trust_level})\n"
    text += f"📈 Успешных сделок: <b>{rating_data['successful_deals']}/{rating_data['total_deals']}</b> "
    text += f"({rating_data['success_rate']:.0f}%)\n"
    text += f"💰 Общий объём: <b>{rating_data['total_volume_rub']:,.0f}₽</b>\n"
    
    return text

