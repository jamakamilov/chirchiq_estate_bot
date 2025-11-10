import os
from typing import List

# Токен бота из переменных окружения
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '7662653538:AAEUlSnB7cOdJ5GybKEWoHL88h3feko_xJQ')

# ID администраторов
ADMIN_IDS = [
    int(x.strip()) for x in os.getenv('ADMIN_IDS', '2132610146').split(',') 
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

# Для простоты используем SQLite если нет PostgreSQL
USE_SQLITE = os.getenv('USE_SQLITE', 'True').lower() == 'true'

# Проверка обязательных переменных
def validate_config():
    """Валидация конфигурации"""
    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == '7662653538:AAEUlSnB7cOdJ5GybKEWoHL88h3feko_xJQ':
        raise ValueError("Please set TELEGRAM_TOKEN environment variable")

# Выполняем валидацию при импорте
validate_config()
