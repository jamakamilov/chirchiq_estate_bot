from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

Base = declarative_base()

class User(Base):
    _tablename_ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String(100))
    full_name = Column(String(200))
    phone = Column(String(20))
    role = Column(String(50))
    currency = Column(String(3), default='UZS')
    language = Column(String(2), default='ru')
    
    # Поля для бесплатного периода
    free_period_start = Column(DateTime)
    free_period_end = Column(DateTime)
    free_period_used = Column(Boolean, default=False)
    
    # Поле для блокировки смены роли
    role_locked = Column(Boolean, default=False)
    
    # Рейтинги
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # Статистика
    properties_count = Column(Integer, default=0)
    last_active = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)

class Property(Base):
    _tablename_ = 'properties'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    user_phone = Column(String(20))
    property_type = Column(String(50))
    district = Column(String(100))
    address = Column(String(300))
    price_uzs = Column(Float)
    price_usd = Column(Float)
    currency = Column(String(3), default='UZS')
    rooms = Column(Integer)
    area = Column(Float)
    description = Column(Text)
    photos = Column(Text)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.now)
    published_in_channel = Column(Boolean, default=False)
    
    # Дополнительные поля
    floor = Column(Integer)
    total_floors = Column(Integer)
    year_built = Column(Integer)
    has_photos = Column(Boolean, default=False)
    
    # Для аренды
    is_daily_rent = Column(Boolean, default=False)
    available_from = Column(DateTime)
    available_to = Column(DateTime)

class Favorite(Base):
    _tablename_ = 'favorites'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    property_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)

class Subscription(Base):
    _tablename_ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    role = Column(String(50))
    start_date = Column(DateTime, default=datetime.now)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_free_period = Column(Boolean, default=True)
    payment_confirmed = Column(Boolean, default=False)
    admin_id = Column(Integer)  # Админ, подтвердивший оплату

class Rating(Base):
    _tablename_ = 'ratings'
    
    id = Column(Integer, primary_key=True)
    target_user_id = Column(Integer)
    author_user_id = Column(Integer)
    rating = Column(Integer)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class ContactRequest(Base):
    _tablename_ = 'contact_requests'
    
    id = Column(Integer, primary_key=True)
    requester_id = Column(Integer)
    target_user_id = Column(Integer)
    property_id = Column(Integer)
    status = Column(String(20), default='pending')
    admin_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime)

class SavedSearch(Base):
    _tablename_ = 'saved_searches'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    search_name = Column(String(100))
    filters = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_notified = Column(DateTime)

class Chat(Base):
    _tablename_ = 'chats'
    
    id = Column(Integer, primary_key=True)
    user1_id = Column(Integer)
    user2_id = Column(Integer)
    property_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, default=datetime.now)

class ChatMessage(Base):
    _tablename_ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    sender_id = Column(Integer)
    message = Column(Text)
    sent_at = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)

class Booking(Base):
    _tablename_ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer)
    user_id = Column(Integer)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    guests = Column(Integer, default=1)
    total_price = Column(Float)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.now)
    confirmed_at = Column(DateTime)
    admin_id = Column(Integer)

class Badge(Base):
    _tablename_ = 'badges'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    badge_type = Column(String(50))
    badge_name = Column(String(100))
    description = Column(Text)
    awarded_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

class UserActivity(Base):
    _tablename_ = 'user_activities'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    activity_type = Column(String(50))  # search, view, contact, etc.
    property_id = Column(Integer)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)

class AdminLog(Base):
    _tablename_ = 'admin_logs'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer)
    action = Column(String(100))
    target_user_id = Column(Integer)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)

# Инициализация БД
engine = create_engine('sqlite:///chirchik_estate.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()
