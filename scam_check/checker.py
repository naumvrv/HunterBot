"""
Продвинутая система проверки мошенников для HunterBot
"""
import re
from typing import Dict, Tuple
from loguru import logger

# База данных известных скамеров (в продакшене - использовать PostgreSQL)
BLACKLIST = [
    "scam_user1", "scam_user2", "мошенник", "развод",
    "обман", "кидала", "не платит"
]

# Красные флаги в тексте объявлений
RED_FLAGS = [
    r"только предоплата",
    r"перевод\s+вперед",
    r"срочно\s+продам",
    r"очень\s+выгодно",
    r"гарантия\s+100%",
    r"без\s+посредников",
    r"только\s+наличные",
    r"встреча\s+обязательна",
    r"можно\s+без\s+проверки",
    r"быстрая\s+сделка",
]

# Подозрительные паттерны
SUSPICIOUS_PATTERNS = [
    r"\d{10,}",  # Слишком длинный телефон
    r"telegram[:\s]+@\w+",  # Переадресация в Telegram
    r"whatsapp",  # WhatsApp (подозрительно для крипты)
    r"viber",
]


def check_seller(seller_name: str) -> bool:
    """
    Проверяет продавца по черному списку
    
    Args:
        seller_name: Имя продавца
        
    Returns:
        True если продавец чистый, False если в черном списке
    """
    if not seller_name:
        return True
    
    seller_lower = seller_name.lower()
    for blacklisted in BLACKLIST:
        if blacklisted.lower() in seller_lower:
            logger.warning(f"⚠️ Продавец '{seller_name}' в черном списке!")
            return False
    return True


def analyze_text_for_scam(text: str) -> Tuple[bool, float, list]:
    """
    AI-подобный анализ текста объявления на признаки мошенничества
    
    Args:
        text: Текст объявления
        
    Returns:
        (is_suspicious, risk_score, detected_flags)
        - is_suspicious: True если есть подозрения
        - risk_score: 0-100, где 100 = максимальный риск
        - detected_flags: Список обнаруженных красных флагов
    """
    if not text:
        return (False, 0.0, [])
    
    text_lower = text.lower()
    detected_flags = []
    risk_score = 0.0
    
    # Проверка красных флагов
    for flag in RED_FLAGS:
        if re.search(flag, text_lower):
            detected_flags.append(flag)
            risk_score += 15.0
    
    # Проверка подозрительных паттернов
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text_lower):
            risk_score += 10.0
    
    # Проверка на слишком короткое описание
    if len(text) < 50:
        risk_score += 5.0
    
    # Проверка на отсутствие деталей
    if not re.search(r'(ton|тон|toncoin)', text_lower):
        risk_score += 10.0
    
    # Проверка на CAPS LOCK (крик)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    if caps_ratio > 0.5:
        risk_score += 20.0
        detected_flags.append("СЛИШКОМ МНОГО ЗАГЛАВНЫХ БУКВ")
    
    # Проверка на эмодзи спам
    emoji_count = len(re.findall(r'[\U0001F300-\U0001F9FF]', text))
    if emoji_count > 10:
        risk_score += 15.0
        detected_flags.append("Слишком много эмодзи")
    
    # Ограничиваем risk_score до 100
    risk_score = min(risk_score, 100.0)
    
    is_suspicious = risk_score >= 40.0
    
    if is_suspicious:
        logger.warning(f"⚠️ Подозрительное объявление! Риск: {risk_score:.1f}%")
        logger.warning(f"Красные флаги: {detected_flags}")
    
    return (is_suspicious, risk_score, detected_flags)


def check_price_anomaly(price_per_ton: float, market_price: float) -> Dict[str, any]:
    """
    Проверяет цену на аномальные отклонения
    
    Args:
        price_per_ton: Цена продавца за 1 TON
        market_price: Рыночная цена TON
        
    Returns:
        Словарь с результатами проверки
    """
    deviation = abs((price_per_ton - market_price) / market_price) * 100
    
    result = {
        "is_anomaly": False,
        "deviation_percent": deviation,
        "warning": None
    }
    
    if deviation > 50:
        result["is_anomaly"] = True
        result["warning"] = f"Цена отличается от рынка на {deviation:.1f}%! Возможно мошенничество."
        logger.warning(f"⚠️ Аномальная цена: {price_per_ton}₽ vs рынок {market_price}₽")
    elif deviation > 30:
        result["warning"] = f"Большое отклонение от рынка: {deviation:.1f}%"
    
    return result


async def check_seller_history(seller_name: str, ads_count: int = 0) -> Dict[str, any]:
    """
    Проверяет историю продавца (в будущем - интеграция с внешними API)
    
    Args:
        seller_name: Имя продавца
        ads_count: Количество объявлений за неделю
        
    Returns:
        Словарь с оценкой продавца
    """
    result = {
        "is_trusted": True,
        "trust_score": 50.0,  # 0-100
        "warnings": []
    }
    
    # Проверка на массовую публикацию
    if ads_count > 20:
        result["trust_score"] -= 30
        result["warnings"].append("Слишком много объявлений за короткое время")
    
    # Проверка имени продавца
    if not seller_name or len(seller_name) < 3:
        result["trust_score"] -= 20
        result["warnings"].append("Подозрительное имя продавца")
    
    # Проверка на черный список
    if not check_seller(seller_name):
        result["is_trusted"] = False
        result["trust_score"] = 0
        result["warnings"].append("В черном списке!")
    
    result["is_trusted"] = result["trust_score"] >= 30
    
    return result


def get_scam_check_report(seller_name: str, text: str, price_per_ton: float, market_price: float) -> str:
    """
    Генерирует полный отчет проверки на мошенничество
    
    Args:
        seller_name: Имя продавца
        text: Текст объявления
        price_per_ton: Цена за TON
        market_price: Рыночная цена
        
    Returns:
        Отформатированный отчет
    """
    # Анализ текста
    is_suspicious, risk_score, flags = analyze_text_for_scam(text)
    
    # Проверка цены
    price_check = check_price_anomaly(price_per_ton, market_price)
    
    # Общая оценка безопасности
    safety_score = 100 - (risk_score * 0.7 + (price_check["deviation_percent"] * 0.3))
    safety_score = max(0, min(100, safety_score))
    
    if safety_score >= 70:
        safety_emoji = "✅"
        safety_level = "БЕЗОПАСНО"
    elif safety_score >= 40:
        safety_emoji = "⚠️"
        safety_level = "ОСТОРОЖНО"
    else:
        safety_emoji = "❌"
        safety_level = "ОПАСНО"
    
    report = f"{safety_emoji} <b>ПРОВЕРКА БЕЗОПАСНОСТИ</b>\n\n"
    report += f"🎯 Общая оценка: <b>{safety_score:.0f}/100</b> ({safety_level})\n"
    report += f"📊 Риск мошенничества: <b>{risk_score:.0f}%</b>\n\n"
    
    if flags:
        report += f"🚩 <b>Красные флаги:</b>\n"
        for flag in flags[:3]:  # Показываем только первые 3
            report += f"   • {flag}\n"
        report += "\n"
    
    if price_check.get("warning"):
        report += f"💰 <b>Цена:</b> {price_check['warning']}\n\n"
    
    if safety_score < 70:
        report += "⚠️ <i>Рекомендуем проявить осторожность!</i>"
    
    return report
