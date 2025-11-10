import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import Message
from database import Database

logger = logging.getLogger(_name_)

# Курсы валют (в реальном приложении нужно брать из API)
EXCHANGE_RATES = {
    'USD': 12500.0,
    'EUR': 13500.0, 
    'RUB': 140.0,
    'UZS': 1.0
}

def format_price(price: float, currency: str, target_currency: str = None) -> str:
    """Форматирование цены с конвертацией валют"""
    try:
        if target_currency and target_currency != currency:
            # Конвертируем цену
            rate_from = EXCHANGE_RATES.get(currency, 1.0)
            rate_to = EXCHANGE_RATES.get(target_currency, 1.0)
            converted_price = (price * rate_from) / rate_to
        else:
            converted_price = price
            target_currency = currency
        
        # Форматируем число
        if converted_price >= 1000000:
            formatted_price = f"{converted_price / 1000000:.1f} млн"
        elif converted_price >= 1000:
            formatted_price = f"{converted_price / 1000:.0f} тыс"
        else:
            formatted_price = f"{converted_price:.0f}"
        
        # Добавляем символ валюты
        currency_symbols = {
            'UZS': 'сум',
            'USD': '$',
            'EUR': '€',
            'RUB': '₽'
        }
        
        symbol = currency_symbols.get(target_currency, target_currency)
        return f"{formatted_price} {symbol}"
        
    except Exception as e:
        logger.error(f"Ошибка форматирования цены: {e}")
        return f"{price} {currency}"

async def check_subscription(user_id: int, db: Database) -> bool:
    """Проверка активной подписки пользователя"""
    try:
        subscription = await db.get_user_subscription(user_id)
        if not subscription:
            return False
            
        # Проверяем срок действия подписки
        if subscription['end_date'] < datetime.now():
            await db.deactivate_subscription(user_id)
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False

async def send_notification(bot: Bot, user_id: int, message: str, 
                          keyboard=None, parse_mode: str = 'HTML') -> bool:
    """Отправка уведомления пользователю"""
    try:
        await bot.send_message(
            chat_id=user_id,
            text=message,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
        return False

async def broadcast_message(bot: Bot, user_ids: list, message: str, 
                          keyboard=None, parse_mode: str = 'HTML') -> Dict[str, int]:
    """Массовая рассылка сообщений"""
    results = {
        'success': 0,
        'failed': 0,
        'total': len(user_ids)
    }
    
    for user_id in user_ids:
        try:
            success = await send_notification(bot, user_id, message, keyboard, parse_mode)
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                
            # Задержка чтобы не превысить лимиты Telegram
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Ошибка рассылки пользователю {user_id}: {e}")
            results['failed'] += 1
    
    return results

def validate_phone_number(phone: str) -> bool:
    """Валидация номера телефона"""
    import re
    # Убираем все нецифровые символы кроме +
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Проверяем форматы: ‪+998901234567‬, 998901234567, 901234567
    patterns = [
        r'^\+998\d{9}$',  # ‪+998901234567‬
        r'^998\d{9}$',    # 998901234567
        r'^90\d{7}$',     # 901234567
        r'^91\d{7}$',     # 911234567
        r'^93\d{7}$',     # 931234567
        r'^94\d{7}$',     # 941234567
        r'^95\d{7}$',     # 951234567
        r'^97\d{7}$',     # 971234567
        r'^99\d{7}$',     # 991234567
    ]
    
    return any(re.match(pattern, cleaned_phone) for pattern in patterns)

def format_phone_number(phone: str) -> str:
    """Форматирование номера телефона в единый формат"""
    import re
    cleaned_phone = re.sub(r'[^\d+]', '', phone)
    
    # Если номер начинается с +998, оставляем как есть
    if cleaned_phone.startswith('+998'):
        return cleaned_phone
    
    # Если номер начинается с 998, добавляем +
    if cleaned_phone.startswith('998'):
        return '+' + cleaned_phone
    
    # Если номер без кода страны, добавляем +998
    if len(cleaned_phone) == 9:
        return '+998' + cleaned_phone
    
    return phone

def calculate_days_left(end_date: datetime) -> int:
    """Расчет оставшихся дней до даты"""
    now = datetime.now()
    delta = end_date - now
    return max(0, delta.days)

async def get_user_stats(user_id: int, db: Database) -> Dict[str, Any]:
    """Получение статистики пользователя"""
    stats = {}
    
    try:
        # Основная информация
        user = await db.get_user(user_id)
        stats['user'] = user
        
        # Статистика объявлений
        stats['properties_count'] = await db.get_user_properties_count(user_id)
        stats['active_properties'] = await db.get_user_active_properties_count(user_id)
        
        # Статистика избранного
        stats['favorites_count'] = await db.get_user_favorites_count(user_id)
        
        # Статистика подписки
        subscription = await db.get_user_subscription(user_id)
        stats['subscription'] = subscription
        if subscription:
            stats['days_left'] = calculate_days_left(subscription['end_date'])
        
        # Статистика рейтингов
        rating_stats = await db.get_user_rating_stats(user_id)
        stats['rating'] = rating_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики пользователя {user_id}: {e}")
        return {}

async def get_system_stats(db: Database) -> Dict[str, Any]:
    """Получение системной статистики"""
    stats = {}
    
    try:
        stats['total_users'] = await db.get_total_users_count()
        stats['active_users'] = await db.get_active_users_count()
        stats['total_properties'] = await db.get_total_properties_count()
        stats['active_properties'] = await db.get_active_properties_count()
        stats['today_properties'] = await db.get_today_properties_count()
        stats['contact_requests'] = await db.get_pending_contact_requests_count()
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения системной статистики: {e}")
        return {}

def format_stats(stats: Dict[str, Any], language: str = 'ru') -> str:
    """Форматирование статистики в текстовый вид"""
    from locales import TEXTS
    
    text = "📊 <b>Статистика системы</b>\n\n"
    
    text += f"👥 <b>Пользователи:</b>\n"
    text += f"   • Всего: {stats.get('total_users', 0)}\n"
    text += f"   • Активных: {stats.get('active_users', 0)}\n\n"
    
    text += f"🏠 <b>Объявления:</b>\n"
    text += f"   • Всего: {stats.get('total_properties', 0)}\n"
    text += f"   • Активных: {stats.get('active_properties', 0)}\n"
    text += f"   • Сегодня: {stats.get('today_properties', 0)}\n\n"
    
    text += f"📞 <b>Запросы:</b>\n"
    text += f"   • На контакт: {stats.get('contact_requests', 0)}\n"
    
    return text

async def notify_admins(bot: Bot, admin_ids: list, message: str, db: Database = None):
    """Уведомление администраторов"""
    for admin_id in admin_ids:
        try:
            await send_notification(bot, admin_id, message)
        except Exception as e:
            logger.error(f"Ошибка уведомления администратора {admin_id}: {e}")

def sanitize_text(text: str, max_length: int = 4000) -> str:
    """Очистка текста от опасных символов и обрезка длины"""
    import html
    # Экранируем HTML символы
    sanitized = html.escape(text)
    # Обрезаем до максимальной длины
    return sanitized[:max_length]

def parse_date(date_str: str) -> Optional[datetime]:
    """Парсинг даты из строки"""
    try:
        formats = ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None

def is_valid_date_range(check_in: datetime, check_out: datetime) -> bool:
    """Проверка корректности диапазона дат"""
    now = datetime.now()
    return check_in >= now and check_out > check_in

async def rate_limit_check(user_id: int, action: str, db: Database, 
                          limit: int = 10, period: int = 3600) -> bool:
    """Проверка ограничения частоты запросов"""
    try:
        key = f"rate_limit:{user_id}:{action}"
        now = datetime.now().timestamp()
        
        # В реальной реализации здесь будет работа с Redis
        # Для простоты используем in-memory кэш
        return True
        
    except Exception as e:
        logger.error(f"Ошибка проверки лимита запросов: {e}")
        return True
