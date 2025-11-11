from datetime import datetime, timedelta
from database import Session, User, Property, Booking, Rating
from sqlalchemy import func, extract

class AnalyticsService:
    @staticmethod
    def get_dashboard_stats():
        """Получает статистику для дашборда"""
        session = Session()
        try:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            # Основная статистика
            total_users = session.query(User).count()
            total_properties = session.query(Property).count()
            active_properties = session.query(Property).filter(Property.status == 'active').count()
            
            # Статистика за неделю
            new_users_week = session.query(User).filter(User.created_at >= week_ago).count()
            new_properties_week = session.query(Property).filter(Property.created_at >= week_ago).count()
            
            # Статистика по ролям
            roles_stats = session.query(
                User.role,
                func.count(User.id)
            ).group_by(User.role).all()
            
            # Популярные районы
            popular_districts = session.query(
                Property.district,
                func.count(Property.id)
            ).filter(Property.status == 'active').group_by(Property.district).order_by(
                func.count(Property.id).desc()
            ).limit(10).all()
            
            # Статистика цен
            avg_price = session.query(func.avg(Property.price_uzs)).filter(
                Property.status == 'active'
            ).scalar() or 0
            
            return {
                'total_users': total_users,
                'total_properties': total_properties,
                'active_properties': active_properties,
                'new_users_week': new_users_week,
                'new_properties_week': new_properties_week,
                'roles_stats': dict(roles_stats),
                'popular_districts': dict(popular_districts),
                'avg_price': avg_price
            }
            
        finally:
            session.close()
    
    @staticmethod
    def get_market_trends(district=None, property_type=None):
        """Анализирует рыночные тренды"""
        session = Session()
        try:
            # Анализ цен по месяцам
            price_trends = session.query(
                extract('year', Property.created_at).label('year'),
                extract('month', Property.created_at).label('month'),
                func.avg(Property.price_uzs).label('avg_price'),
                func.count(Property.id).label('count')
            ).filter(Property.status == 'active')
            
            if district:
                price_trends = price_trends.filter(Property.district == district)
            if property_type:
                price_trends = price_trends.filter(Property.property_type == property_type)
            
            price_trends = price_trends.group_by('year', 'month').order_by('year', 'month').all()
            
            return [
                {
                    'period': f"{int(trend.month)}/{int(trend.year)}",
                    'avg_price': trend.avg_price,
                    'count': trend.count
                }
                for trend in price_trends
            ]
            
        finally:
            session.close()
    
    @staticmethod
    def get_user_activity(user_id, days=30):
        """Анализирует активность пользователя"""
        session = Session()
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Статистика действий пользователя
            activities = session.query(
                UserActivity.activity_type,
                func.count(UserActivity.id)
            ).filter(
                UserActivity.user_id == user_id,
                UserActivity.created_at >= start_date
            ).group_by(UserActivity.activity_type).all()
            
            return dict(activities)
            
        finally:
            session.close()
