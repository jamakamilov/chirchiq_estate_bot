import aiosqlite
import asyncpg
import json
from datetime import datetime, timedelta
from config import DATABASE_CONFIG, USE_SQLITE

class Database:
    def _init_(self):
        self.pool = None
        self.sqlite_conn = None
        
    async def create_tables(self):
        """Создание таблиц в базе данных"""
        if USE_SQLITE:
            await self._create_sqlite_tables()
        else:
            await self._create_postgres_tables()
    
    async def _create_sqlite_tables(self):
        """Создание таблиц в SQLite"""
        self.sqlite_conn = await aiosqlite.connect('bot.db')
        
        # Таблица пользователей
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                role TEXT,
                language TEXT DEFAULT 'ru',
                currency TEXT DEFAULT 'UZS',
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица подписок
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                is_free BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица объявлений
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS properties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                district TEXT,
                address TEXT,
                price DECIMAL,
                currency TEXT DEFAULT 'UZS',
                rooms INTEGER,
                area DECIMAL,
                description TEXT,
                photos TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Таблица избранного
        await self.sqlite_conn.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                property_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (property_id) REFERENCES properties (id),
                UNIQUE(user_id, property_id)
            )
        ''')
        
        await self.sqlite_conn.commit()
    
    async def get_user(self, user_id: int):
        """Получение пользователя по ID"""
        if USE_SQLITE:
            cursor = await self.sqlite_conn.execute(
                'SELECT * FROM users WHERE id = ?', (user_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                return {
                    'id': row[0],
                    'username': row[1],
                    'full_name': row[2],
                    'role': row[3],
                    'language': row[4],
                    'currency': row[5],
                    'phone_number': row[6],
                    'created_at': row[7]
                }
            return None
    
    async def create_user(self, user_id: int, username: str, full_name: str, language: str = 'ru'):
        """Создание нового пользователя"""
        if USE_SQLITE:
            await self.sqlite_conn.execute('''
                INSERT OR IGNORE INTO users (id, username, full_name, language)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, full_name, language))
            await self.sqlite_conn.commit()
    
    async def update_user_role(self, user_id: int, role: str):
        """Обновление роли пользователя"""
        if USE_SQLITE:
            await self.sqlite_conn.execute(
                'UPDATE users SET role = ? WHERE id = ?',
                (role, user_id)
            )
            await self.sqlite_conn.commit()
    
    async def update_user_language(self, user_id: int, language: str):
        """Обновление языка пользователя"""
        if USE_SQLITE:
            await self.sqlite_conn.execute(
                'UPDATE users SET language = ? WHERE id = ?',
                (language, user_id)
            )
            await self.sqlite_conn.commit()
    
    async def update_user_currency(self, user_id: int, currency: str):
        """Обновление валюты пользователя"""
        if USE_SQLITE:
            await self.sqlite_conn.execute(
                'UPDATE users SET currency = ? WHERE id = ?',
                (currency, user_id)
            )
            await self.sqlite_conn.commit()
    
    async def create_subscription(self, user_id: int, days: int, is_free: bool = True):
        """Создание подписки"""
        if USE_SQLITE:
            end_date = datetime.now() + timedelta(days=days)
            await self.sqlite_conn.execute('''
                INSERT INTO subscriptions (user_id, end_date, is_free)
                VALUES (?, ?, ?)
            ''', (user_id, end_date, is_free))
            await self.sqlite_conn.commit()
    
    async def get_user_subscription(self, user_id: int):
        """Получение активной подписки пользователя"""
        if USE_SQLITE:
            cursor = await self.sqlite_conn.execute('''
                SELECT * FROM subscriptions 
                WHERE user_id = ? AND is_active = TRUE AND end_date > ?
                ORDER BY end_date DESC LIMIT 1
            ''', (user_id, datetime.now()))
            
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'start_date': row[2],
                    'end_date': row[3],
                    'is_free': bool(row[4]),
                    'is_active': bool(row[5])
                }
            return None
    
    async def add_to_favorites(self, user_id: int, property_id: int) -> bool:
        """Добавление в избранное"""
        try:
            if USE_SQLITE:
                await self.sqlite_conn.execute('''
                    INSERT OR IGNORE INTO favorites (user_id, property_id)
                    VALUES (?, ?)
                ''', (user_id, property_id))
                await self.sqlite_conn.commit()
                return True
        except Exception:
            return False
    
    async def get_user_favorites(self, user_id: int):
        """Получение избранного пользователя"""
        if USE_SQLITE:
            cursor = await self.sqlite_conn.execute('''
                SELECT f., p. FROM favorites f
                JOIN properties p ON f.property_id = p.id
                WHERE f.user_id = ? AND p.is_active = TRUE
                ORDER BY f.created_at DESC
            ''', (user_id,))
            
            rows = await cursor.fetchall()
            await cursor.close()
            
            favorites = []
            for row in rows:
                favorites.append({
                    'id': row[0],
                    'user_id': row[1],
                    'property_id': row[2],
                    'created_at': row[3]
                })
            return favorites
    
    async def is_property_in_favorites(self, user_id: int, property_id: int) -> bool:
        """Проверка, есть ли объявление в избранном"""
        if USE_SQLITE:
            cursor = await self.sqlite_conn.execute('''
                SELECT 1 FROM favorites 
                WHERE user_id = ? AND property_id = ?
            ''', (user_id, property_id))
            
            row = await cursor.fetchone()
            await cursor.close()
            return row is not None
    
    async def create_contact_request(self, user_id: int, target_user_id: int, property_id: int = None) -> int:
        """Создание запроса на контакт"""
        try:
            if USE_SQLITE:
                cursor = await self.sqlite_conn.execute('''
                    INSERT INTO contact_requests (user_id, target_user_id, property_id, status)
                    VALUES (?, ?, ?, 'pending')
                ''', (user_id, target_user_id, property_id))
                await self.sqlite_conn.commit()
                return cursor.lastrowid
        except Exception:
            return None
    
    async def get_user_rating_stats(self, user_id: int):
        """Получение статистики рейтинга пользователя"""
        # Заглушка - в реальной реализации здесь будет запрос к таблице рейтингов
        return {'average': 4.5, 'count': 10}
    
    async def get_property(self, property_id: int):
        """Получение объявления по ID"""
        if USE_SQLITE:
            cursor = await self.sqlite_conn.execute(
                'SELECT * FROM properties WHERE id = ?', (property_id,)
            )
            row = await cursor.fetchone()
            await cursor.close()
            
            if row:
                return {
                    'id': row[0],
                    'user_id': row[1],
                    'type': row[2],
                    'district': row[3],
                    'address': row[4],
                    'price': float(row[5]),
                    'currency': row[6],
                    'rooms': row[7],
                    'area': float(row[8]),
                    'description': row[9],
                    'photos': json.loads(row[10]) if row[10] else [],
                    'is_active': bool(row[11]),
                    'created_at': row[12]
                }
            return None

# Создаем глобальный экземпляр базы данных
database_instance = Database()
