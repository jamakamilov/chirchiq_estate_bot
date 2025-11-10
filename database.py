import asyncpg
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(_name_)

class Database:
    def _init_(self):
        self.pool = None

    async def create_pool(self, database_url: str = None):
        """Создание пула соединений с базой данных"""
        if database_url:
            self.pool = await asyncpg.create_pool(database_url)
        else:
            # Для тестирования - SQLite через aiosqlite
            pass

    async def create_tables(self):
        """Создание таблиц в базе данных"""
        try:
            async with self.pool.acquire() as conn:
                # Таблица пользователей
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id BIGINT PRIMARY KEY,
                        username VARCHAR(100),
                        full_name VARCHAR(200),
                        phone VARCHAR(20),
                        role VARCHAR(50),
                        language VARCHAR(10) DEFAULT 'ru',
                        currency VARCHAR(10) DEFAULT 'UZS',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        role_locked BOOLEAN DEFAULT FALSE
                    )
                ''')

                # Таблица подписок
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(id),
                        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_date TIMESTAMP,
                        is_free BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица недвижимости
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS properties (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(id),
                        type VARCHAR(100),
                        district VARCHAR(100),
                        address TEXT,
                        price DECIMAL(15,2),
                        rooms INTEGER,
                        area DECIMAL(10,2),
                        description TEXT,
                        photos TEXT[],
                        currency VARCHAR(10) DEFAULT 'UZS',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица избранного
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS favorites (
                        id SERIAL PRIMARY KEY,
                        user_id BIGINT REFERENCES users(id),
                        property_id INTEGER REFERENCES properties(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, property_id)
                    )
                ''')

                # Таблица рейтингов
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS ratings (
                        id SERIAL PRIMARY KEY,
                        from_user_id BIGINT REFERENCES users(id),
                        to_user_id BIGINT REFERENCES users(id),
                        rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(from_user_id, to_user_id)
                    )
                ''')

                # Таблица запросов на контакт
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS contact_requests (
                        id SERIAL PRIMARY KEY,
                        from_user_id BIGINT REFERENCES users(id),
                        to_user_id BIGINT REFERENCES users(id),
                        property_id INTEGER REFERENCES properties(id),
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица чатов
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS chats (
                        id SERIAL PRIMARY KEY,
                        user1_id BIGINT REFERENCES users(id),
                        user2_id BIGINT REFERENCES users(id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Таблица сообщений
                await conn.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        chat_id INTEGER REFERENCES chats(id),
                        from_user_id BIGINT REFERENCES users(id),
                        message_text TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")

    # ========== USER METHODS ==========

    async def create_user(self, user_id: int, username: str, full_name: str, language: str = 'ru'):
        """Создание нового пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO users (id, username, full_name, language) 
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                    username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name,
                    language = EXCLUDED.language
                ''', user_id, username, full_name, language)
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM users WHERE id = $1', user_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения пользователя: {e}")
            return None

    async def update_user_role(self, user_id: int, role: str):
        """Обновление роли пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE users SET role = $1 WHERE id = $2',
                    role, user_id
                )
        except Exception as e:
            logger.error(f"Ошибка обновления роли: {e}")

    async def update_user_language(self, user_id: int, language: str):
        """Обновление языка пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE users SET language = $1 WHERE id = $2',
                    language, user_id
                )
        except Exception as e:
            logger.error(f"Ошибка обновления языка: {e}")

    async def update_user_currency(self, user_id: int, currency: str):
        """Обновление валюты пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE users SET currency = $1 WHERE id = $2',
                    currency, user_id
                )
        except Exception as e:
            logger.error(f"Ошибка обновления валюты: {e}")

    async def update_user_phone(self, user_id: int, phone: str):
        """Обновление телефона пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'UPDATE users SET phone = $1 WHERE id = $2',
                    phone, user_id
                )
        except Exception as e:
            logger.error(f"Ошибка обновления телефона: {e}")

    # ========== SUBSCRIPTION METHODS ==========

    async def create_subscription(self, user_id: int, days: int, is_free: bool = True):
        """Создание подписки для пользователя"""
        try:
            async with self.pool.acquire() as conn:
                end_date = datetime.now() + timedelta(days=days)
                await conn.execute('''
                    INSERT INTO subscriptions (user_id, end_date, is_free)
                    VALUES ($1, $2, $3)
                ''', user_id, end_date, is_free)
        except Exception as e:
            logger.error(f"Ошибка создания подписки: {e}")

    async def get_user_subscription(self, user_id: int) -> Optional[Dict]:
        """Получение активной подписки пользователя"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT * FROM subscriptions 
                    WHERE user_id = $1 AND end_date > CURRENT_TIMESTAMP
                    ORDER BY created_at DESC LIMIT 1
                ''', user_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения подписки: {e}")
            return None

    async def deactivate_subscription(self, user_id: int):
        """Деактивация подписки пользователя"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE subscriptions SET end_date = CURRENT_TIMESTAMP 
                    WHERE user_id = $1 AND end_date > CURRENT_TIMESTAMP
                ''', user_id)
        except Exception as e:
            logger.error(f"Ошибка деактивации подписки: {e}")

    # ========== PROPERTY METHODS ==========

    async def add_property(self, user_id: int, property_data: Dict) -> int:
        """Добавление нового объявления"""
        try:
            async with self.pool.acquire() as conn:
                property_id = await conn.fetchval('''
                    INSERT INTO properties 
                    (user_id, type, district, address, price, rooms, area, description, photos, currency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING id
                ''', user_id, property_data['type'], property_data['district'],
                    property_data['address'], property_data['price'], property_data['rooms'],
                    property_data['area'], property_data['description'], 
                    property_data.get('photos', []), property_data.get('currency', 'UZS'))
                return property_id
        except Exception as e:
            logger.error(f"Ошибка добавления объявления: {e}")
            return 0

    async def get_property(self, property_id: int) -> Optional[Dict]:
        """Получение объявления по ID"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('SELECT * FROM properties WHERE id = $1', property_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения объявления: {e}")
            return None

    async def search_properties(self, filters: Dict) -> List[Dict]:
        """Поиск объявлений по фильтрам"""
        try:
            async with self.pool.acquire() as conn:
                query = 'SELECT * FROM properties WHERE is_active = TRUE'
                params = []
                param_count = 0

                if filters.get('type') and filters['type'] != 'any':
                    param_count += 1
                    query += f' AND type = ${param_count}'
                    params.append(filters['type'])

                if filters.get('district') and filters['district'] != 'any':
                    param_count += 1
                    query += f' AND district = ${param_count}'
                    params.append(filters['district'])

                if filters.get('min_price'):
                    param_count += 1
                    query += f' AND price >= ${param_count}'
                    params.append(filters['min_price'])

                if filters.get('max_price'):
                    param_count += 1
                    query += f' AND price <= ${param_count}'
                    params.append(filters['max_price'])

                if filters.get('min_rooms'):
                    param_count += 1
                    query += f' AND rooms >= ${param_count}'
                    params.append(filters['min_rooms'])

                if filters.get('max_rooms'):
                    param_count += 1
                    query += f' AND rooms <= ${param_count}'
                    params.append(filters['max_rooms'])

                if filters.get('min_area'):
                    param_count += 1
                    query += f' AND area >= ${param_count}'
                    params.append(filters['min_area'])

                if filters.get('max_area'):
                    param_count += 1
                    query += f' AND area <= ${param_count}'
                    params.append(filters['max_area'])

                query += ' ORDER BY created_at DESC'

                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска объявлений: {e}")
            return []

    async def get_user_properties(self, user_id: int) -> List[Dict]:
        """Получение объявлений пользователя"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    'SELECT * FROM properties WHERE user_id = $1 ORDER BY created_at DESC',
                    user_id
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения объявлений пользователя: {e}")
            return []

    async def update_property(self, property_id: int, updates: Dict):
        """Обновление объявления"""
        try:
            async with self.pool.acquire() as conn:
                set_parts = []
                params = []
                param_count = 0

                for key, value in updates.items():
                    param_count += 1
                    set_parts.append(f"{key} = ${param_count}")
                    params.append(value)

                param_count += 1
                set_parts.append(f"updated_at = CURRENT_TIMESTAMP")
                
                params.append(property_id)
                query = f'UPDATE properties SET {", ".join(set_parts)} WHERE id = ${param_count}'
                
                await conn.execute(query, *params)
        except Exception as e:
            logger.error(f"Ошибка обновления объявления: {e}")

    # ========== FAVORITES METHODS ==========

    async def add_to_favorites(self, user_id: int, property_id: int) -> bool:
        """Добавление в избранное"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO favorites (user_id, property_id) 
                    VALUES ($1, $2)
                    ON CONFLICT (user_id, property_id) DO NOTHING
                ''', user_id, property_id)
                return True
        except Exception as e:
            logger.error(f"Ошибка добавления в избранное: {e}")
            return False

    async def remove_from_favorites(self, user_id: int, property_id: int):
        """Удаление из избранного"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    'DELETE FROM favorites WHERE user_id = $1 AND property_id = $2',
                    user_id, property_id
                )
        except Exception as e:
            logger.error(f"Ошибка удаления из избранного: {e}")

    async def get_user_favorites(self, user_id: int) -> List[Dict]:
        """Получение избранных объявлений пользователя"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT p.* FROM properties p
                    JOIN favorites f ON p.id = f.property_id
                    WHERE f.user_id = $1 AND p.is_active = TRUE
                    ORDER BY f.created_at DESC
                ''', user_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения избранного: {e}")
            return []

    async def is_property_in_favorites(self, user_id: int, property_id: int) -> bool:
        """Проверка, есть ли объявление в избранном"""
        try:
            async with self.pool.acquire() as conn:
                count = await conn.fetchval(
                    'SELECT COUNT(*) FROM favorites WHERE user_id = $1 AND property_id = $2',
                    user_id, property_id
                )
                return count > 0
        except Exception as e:
            logger.error(f"Ошибка проверки избранного: {e}")
            return False

    # ========== RATING METHODS ==========

    async def add_rating(self, from_user_id: int, to_user_id: int, rating: int, comment: str = None):
        """Добавление оценки пользователю"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO ratings (from_user_id, to_user_id, rating, comment)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (from_user_id, to_user_id) DO UPDATE SET
                    rating = EXCLUDED.rating,
                    comment = EXCLUDED.comment,
                    created_at = CURRENT_TIMESTAMP
                ''', from_user_id, to_user_id, rating, comment)
        except Exception as e:
            logger.error(f"Ошибка добавления оценки: {e}")

    async def get_user_rating_stats(self, user_id: int) -> Dict:
        """Получение статистики оценок пользователя"""
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow('''
                    SELECT 
                        COUNT(*) as count,
                        AVG(rating) as average,
                        MIN(rating) as min,
                        MAX(rating) as max
                    FROM ratings 
                    WHERE to_user_id = $1
                ''', user_id)
                return dict(row) if row else {'count': 0, 'average': 0, 'min': 0, 'max': 0}
        except Exception as e:
            logger.error(f"Ошибка получения статистики оценок: {e}")
            return {'count': 0, 'average': 0, 'min': 0, 'max': 0}

    async def get_user_ratings(self, user_id: int) -> List[Dict]:
        """Получение всех оценок пользователя"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT r.*, u.full_name, u.username
                    FROM ratings r
                    JOIN users u ON r.from_user_id = u.id
                    WHERE r.to_user_id = $1
                    ORDER BY r.created_at DESC
                ''', user_id)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения оценок: {e}")
            return []

    # ========== CONTACT REQUEST METHODS ==========

    async def create_contact_request(self, from_user_id: int, to_user_id: int, property_id: int = None) -> int:
        """Создание запроса на контакт"""
        try:
            async with self.pool.acquire() as conn:
                request_id = await conn.fetchval('''
                    INSERT INTO contact_requests (from_user_id, to_user_id, property_id)
                    VALUES ($1, $2, $3)
                    RETURNING id
                ''', from_user_id, to_user_id, property_id)
                return request_id
        except Exception as e:
            logger.error(f"Ошибка создания запроса на контакт: {e}")
            return 0

    async def update_contact_request_status(self, request_id: int, status: str):
        """Обновление статуса запроса на контакт"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    UPDATE contact_requests 
                    SET status = $1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $2
                ''', status, request_id)
        except Exception as e:
            logger.error(f"Ошибка обновления статуса запроса: {e}")

    async def get_pending_contact_requests(self) -> List[Dict]:
        """Получение pending запросов на контакт"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT cr.*, 
                           u1.full_name as from_user_name,
                           u2.full_name as to_user_name
                    FROM contact_requests cr
                    JOIN users u1 ON cr.from_user_id = u1.id
                    JOIN users u2 ON cr.to_user_id = u2.id
                    WHERE cr.status = 'pending'
                    ORDER BY cr.created_at DESC
                ''')
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения pending запросов: {e}")
            return []

    # ========== STATISTICS METHODS ==========

    async def get_total_users_count(self) -> int:
        """Получение общего количества пользователей"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM users')
        except Exception as e:
            logger.error(f"Ошибка получения количества пользователей: {e}")
            return 0

    async def get_active_users_count(self) -> int:
        """Получение количества активных пользователей"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
        except Exception as e:
            logger.error(f"Ошибка получения активных пользователей: {e}")
            return 0

    async def get_total_properties_count(self) -> int:
        """Получение общего количества объявлений"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM properties')
        except Exception as e:
            logger.error(f"Ошибка получения количества объявлений: {e}")
            return 0

    async def get_active_properties_count(self) -> int:
        """Получение количества активных объявлений"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval('SELECT COUNT(*) FROM properties WHERE is_active = TRUE')
        except Exception as e:
            logger.error(f"Ошибка получения активных объявлений: {e}")
            return 0

    async def get_user_properties_count(self, user_id: int) -> int:
        """Получение количества объявлений пользователя"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    'SELECT COUNT(*) FROM properties WHERE user_id = $1',
                    user_id
                )
        except Exception as e:
            logger.error(f"Ошибка получения количества объявлений пользователя: {e}")
            return 0

    async def get_user_favorites_count(self, user_id: int) -> int:
        """Получение количества избранных объявлений пользователя"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetchval(
                    'SELECT COUNT(*) FROM favorites WHERE user_id = $1',
                    user_id
                )
        except Exception as e:
            logger.error(f"Ошибка получения количества избранного: {e}")
            return 0

    async def close(self):
        """Закрытие пула соединений"""
        if self.pool:
            await self.pool.close()
