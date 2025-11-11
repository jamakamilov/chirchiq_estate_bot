from datetime import datetime
from database import Session, Badge, User, Property, Rating
from locales import get_text

class GamificationService:
    BADGES = {
        'first_property': {
            'name': '🏠 Первое объявление',
            'description': 'Разместил первое объявление'
        },
        'power_user': {
            'name': '⚡ Активный пользователь',
            'description': '10+ размещенных объявлений'
        },
        'top_rated': {
            'name': '⭐ Высокий рейтинг',
            'description': 'Рейтинг 4.5+ с 10+ оценками'
        },
        'quick_responder': {
            'name': '🚀 Быстрый ответ',
            'description': 'Быстро отвечает на сообщения'
        },
        'trusted_seller': {
            'name': '🛡 Надежный продавец',
            'description': 'Много успешных сделок'
        }
    }
    
    @staticmethod
    def check_and_award_badges(user_id):
        """Проверяет и награждает пользователя бейджами"""
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return []
            
            awarded_badges = []
            
            # Проверяем бейдж первого объявления
            properties_count = session.query(Property).filter(Property.user_id == user_id).count()
            if properties_count >= 1 and not GamificationService.has_badge(user_id, 'first_property'):
                GamificationService.award_badge(user_id, 'first_property')
                awarded_badges.append('first_property')
            
            # Проверяем бейдж активного пользователя
            if properties_count >= 10 and not GamificationService.has_badge(user_id, 'power_user'):
                GamificationService.award_badge(user_id, 'power_user')
                awarded_badges.append('power_user')
            
            # Проверяем бейдж высокого рейтинга
            if user.rating >= 4.5 and user.rating_count >= 10 and not GamificationService.has_badge(user_id, 'top_rated'):
                GamificationService.award_badge(user_id, 'top_rated')
                awarded_badges.append('top_rated')
            
            return awarded_badges
            
        finally:
            session.close()
    
    @staticmethod
    def award_badge(user_id, badge_type):
        """Награждает пользователя бейджем"""
        session = Session()
        try:
            badge_info = GamificationService.BADGES.get(badge_type)
            if not badge_info:
                return False
            
            badge = Badge(
                user_id=user_id,
                badge_type=badge_type,
                badge_name=badge_info['name'],
                description=badge_info['description'],
                awarded_at=datetime.now()
            )
            
            session.add(badge)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    def has_badge(user_id, badge_type):
        """Проверяет, есть ли у пользователя бейдж"""
        session = Session()
        try:
            badge = session.query(Badge).filter(
                Badge.user_id == user_id,
                Badge.badge_type == badge_type,
                Badge.is_active == True
            ).first()
            
            return badge is not None
        finally:
            session.close()
    
    @staticmethod
    def get_user_badges(user_id):
        """Получает все бейджи пользователя"""
        session = Session()
        try:
            badges = session.query(Badge).filter(
                Badge.user_id == user_id,
                Badge.is_active == True
            ).order_by(Badge.awarded_at.desc()).all()
            
            return badges
        finally:
            session.close()
