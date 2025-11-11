import asyncio
from datetime import datetime, timedelta
from database import Session, User, Property, SavedSearch, Favorite
from aiogram import Bot
from utils import format_property_message
from locales import get_text

class NotificationService:
    def _init_(self, bot: Bot):
        self.bot = bot
    
    async def check_saved_searches(self):
        """Проверяет новые объявления для сохраненных поисков"""
        session = Session()
        try:
            saved_searches = session.query(SavedSearch).filter(
                SavedSearch.is_active == True
            ).all()
            
            for search in saved_searches:
                await self.check_search_matches(search)
                
        except Exception as e:
            print(f"Error in saved searches: {e}")
        finally:
            session.close()
    
    async def check_search_matches(self, search):
        """Проверяет совпадения для конкретного поиска"""
        session = Session()
        try:
            filters = search.filters or {}
            last_notified = search.last_notified or datetime.now() - timedelta(days=30)
            
            query = session.query(Property).filter(
                Property.status == 'active',
                Property.created_at > last_notified
            )
            
            # Применяем фильтры
            if filters.get('property_type'):
                query = query.filter(Property.property_type == filters['property_type'])
            if filters.get('district') and filters['district'] != 'any':
                query = query.filter(Property.district == filters['district'])
            if filters.get('min_price'):
                query = query.filter(Property.price_uzs >= filters['min_price'])
            if filters.get('max_price'):
                query = query.filter(Property.price_uzs <= filters['max_price'])
            if filters.get('rooms'):
                query = query.filter(Property.rooms == filters['rooms'])
            
            new_properties = query.order_by(Property.created_at.desc()).limit(10).all()
            
            for prop in new_properties:
                await self.send_search_notification(search.user_id, prop, search.search_name)
            
            if new_properties:
                search.last_notified = datetime.now()
                session.commit()
                
        except Exception as e:
            print(f"Error checking search matches: {e}")
        finally:
            session.close()
    
    async def send_search_notification(self, user_id, property_obj, search_name):
        """Отправляет уведомление о новом объекте"""
        try:
            message = (
                f"🔔 <b>Новое объявление по вашему запросу \"{search_name}\"</b>\n\n"
                f"{format_property_message(property_obj)}"
            )
            
            await self.bot.send_message(user_id, message, parse_mode="HTML")
            
        except Exception as e:
            print(f"Failed to send notification to {user_id}: {e}")
    
    async def send_price_drop_notification(self, property_obj, old_price, new_price):
        """Уведомление о снижении цены"""
        session = Session()
        try:
            favorites = session.query(Favorite).filter(
                Favorite.property_id == property_obj.id
            ).all()
            
            for fav in favorites:
                try:
                    message = (
                        f"📉 <b>Цена снижена!</b>\n\n"
                        f"🏠 {property_obj.property_type} в {property_obj.district}\n"
                        f"💰 Было: {old_price:,.0f} сум\n"
                        f"💰 Стало: {new_price:,.0f} сум\n"
                        f"📉 Скидка: {((old_price - new_price) / old_price * 100):.1f}%"
                    )
                    
                    await self.bot.send_message(fav.user_id, message, parse_mode="HTML")
                except Exception as e:
                    print(f"Failed to send price drop notification: {e}")
                    
        finally:
            session.close()
    
    async def send_subscription_expiry_notification(self, user_id, days_left):
        """Уведомление о скором окончании подписки"""
        try:
            if days_left in [7, 3, 1]:
                message = (
                    f"⏰ <b>Ваша подписка заканчивается через {days_left} дней</b>\n\n"
                    f"Для продления свяжитесь с администратором: @Jamastik"
                )
                
                await self.bot.send_message(user_id, message, parse_mode="HTML")
                
        except Exception as e:
            print(f"Failed to send subscription notification: {e}")
