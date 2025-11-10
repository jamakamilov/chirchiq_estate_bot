import os
from typing import List

# Токен бота из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'YOUR_BOT_TOKEN_HERE')

# ID администраторов
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') 
    if x.strip().isdigit()
]

# Настройки базы данных
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'chirchiq_estate'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# Настройки Redis для кэширования и rate limiting
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0)),
    'password': os.getenv('REDIS_PASSWORD', None)
}

# Настройки API
API_CONFIG = {
    'exchange_rate_url': 'https://api.exchangerate-api.com/v4/latest/UZS',
    'ai_service_url': os.getenv('AI_SERVICE_URL', 'http://localhost:8000'),
    'ai_service_timeout': 30
}

# Настройки подписок
SUBSCRIPTION_CONFIG = {
    'free_periods': {
        'developer': 7,
        'agency': 14,
        'realtor': 21, 
        'renter': 30
    },
    'paid_plans': {
        '1': {'price': 50000, 'days': 30},
        '3': {'price': 120000, 'days': 90},
        '6': {'price': 200000, 'days': 180},
        '12': {'price': 350000, 'days': 365}
    }
}

# Настройки модерации
MODERATION_CONFIG = {
    'auto_moderation': True,
    'max_properties_per_user': 10,
    'max_photos_per_property': 10,
    'min_description_length': 10,
    'max_description_length': 2000
}

# Настройки уведомлений
NOTIFICATION_CONFIG = {
    'new_property_notify_admins': True,
    'contact_request_notify_admins': True,
    'subscription_expiry_reminder_days': [7, 3, 1],
    'price_drop_notification': True
}

# Логирование
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'bot.log'
}

# Настройки локализации
I18N_CONFIG = {
    'default_language': 'ru',
    'available_languages': ['ru', 'uz', 'en'],
    'language_session_key': 'language'
}

# Проверка обязательных переменных
def validate_config():
    """Валидация конфигурации"""
    required_vars = ['TELEGRAM_TOKEN']
    
    for var in required_vars:
        if not globals().get(var):
            raise ValueError(f"Не задана обязательная переменная: {var}")
    
    if not ADMIN_IDS:
        print("⚠  Предупреждение: ADMIN_IDS не заданы")

# Выполняем валидацию при импорте
validate_config()
