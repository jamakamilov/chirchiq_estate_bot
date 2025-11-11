import re
from database import Session, Property, User
from datetime import datetime, timedelta

class ModerationService:
    @staticmethod
    def auto_moderate_property(property_data):
        """Автоматическая модерация объявления"""
        score = 100  # Начальный score
        
        # Проверка описания
        if property_data.get('description'):
            description = property_data['description'].lower()
            
            # Проверка на спам
            spam_keywords = ['купить', 'продать', 'срочно', 'недорого']
            spam_count = sum(1 for keyword in spam_keywords if keyword in description)
            if spam_count > 3:
                score -= 20
            
            # Проверка на контактные данные в описании
            phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(\)]{8,}[0-9]'
            if re.search(phone_pattern, property_data['description']):
                score -= 15
        
        # Проверка цены
        if property_data.get('price_uzs'):
            avg_prices = {
                'apartment': 200000000,  # Средняя цена квартиры
                'house': 500000000,      # Средняя цена дома
                'commercial': 300000000  # Средняя цена коммерции
            }
            
            property_type = property_data.get('property_type')
            if property_type in avg_prices:
                avg_price = avg_prices[property_type]
                user_price = property_data['price_uzs']
                
                # Если цена отличается более чем на 70% от средней
                if user_price < avg_price * 0.3 or user_price > avg_price * 1.7:
                    score -= 25
        
        return score >= 70  # Проходит модерацию если score >= 70
    
    @staticmethod
    def check_user_behavior(user_id):
        """Проверяет поведение пользователя на подозрительность"""
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False
            
            # Проверяем количество объявлений за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            recent_properties = session.query(Property).filter(
                Property.user_id == user_id,
                Property.created_at >= yesterday
            ).count()
            
            # Если больше 5 объявлений за день - подозрительно
            if recent_properties > 5:
                return True
            
            return False
            
        finally:
            session.close()
    
    @staticmethod
    def flag_suspicious_property(property_id, reason):
        """Помечает объявление как подозрительное"""
        session = Session()
        try:
            property_obj = session.query(Property).filter(Property.id == property_id).first()
            if property_obj:
                property_obj.status = 'suspicious'
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
