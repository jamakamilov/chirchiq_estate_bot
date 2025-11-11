from database import Session, User, Rating
from config import RATED_ROLES
from locales import get_text

class RatingService:
    @staticmethod
    def add_rating(target_user_id: int, author_user_id: int, rating_value: int, comment: str = "", lang: str = 'ru'):
        """Добавить оценку пользователю"""
        session = Session()
        
        try:
            # Проверяем существование пользователей
            target_user = session.query(User).filter(User.telegram_id == target_user_id).first()
            author_user = session.query(User).filter(User.telegram_id == author_user_id).first()
            
            if not target_user or not author_user:
                return False, get_text("user_not_found", lang)
            
            # Проверяем, можно ли оценивать этого пользователя
            if target_user.role not in RATED_ROLES:
                return False, get_text("cannot_rate_user", lang)
            
            # Проверяем, не пытается ли пользователь оценить себя
            if target_user_id == author_user_id:
                return False, get_text("cannot_rate_yourself", lang)
            
            # Проверяем, не оставлял ли уже оценку
            existing_rating = session.query(Rating).filter(
                Rating.target_user_id == target_user_id,
                Rating.author_user_id == author_user_id
            ).first()
            
            if existing_rating:
                return False, get_text("rating_already_exists", lang)
            
            # Проверяем валидность оценки
            if rating_value < 1 or rating_value > 5:
                return False, get_text("invalid_rating", lang)
            
            # Создаем оценку
            rating = Rating(
                target_user_id=target_user_id,
                author_user_id=author_user_id,
                rating=rating_value,
                comment=comment
            )
            
            session.add(rating)
            
            # Обновляем рейтинг пользователя
            total_ratings = session.query(Rating).filter(Rating.target_user_id == target_user_id).count()
            total_score = session.query(Rating).filter(Rating.target_user_id == target_user_id).with_entities(
                func.sum(Rating.rating)
            ).scalar() or 0
            
            # Добавляем новую оценку
            new_total_score = total_score + rating_value
            new_total_ratings = total_ratings + 1
            new_rating = new_total_score / new_total_ratings
            
            target_user.rating = round(new_rating, 1)
            target_user.rating_count = new_total_ratings
            
            session.commit()
            
            return True, get_text("rating_added", lang)
            
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def get_user_ratings(user_id: int, lang: str = 'ru'):
        """Получить все оценки пользователя"""
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return None, get_text("user_not_found", lang)
            
            ratings = session.query(Rating).filter(Rating.target_user_id == user_id).order_by(
                Rating.created_at.desc()
            ).all()
            
            return ratings, None
            
        except Exception as e:
            return None, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def get_rating_stats(user_id: int, lang: str = 'ru'):
        """Получить статистику рейтинга пользователя"""
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return None, get_text("user_not_found", lang)
            
            if user.rating_count == 0:
                return {
                    'rating': 0,
                    'count': 0,
                    'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                }, None
            
            # Получаем распределение оценок
            distribution = {}
            for i in range(1, 6):
                count = session.query(Rating).filter(
                    Rating.target_user_id == user_id,
                    Rating.rating == i
                ).count()
                distribution[i] = count
            
            return {
                'rating': user.rating,
                'count': user.rating_count,
                'distribution': distribution
            }, None
            
        except Exception as e:
            return None, f"Error: {str(e)}"
        finally:
            session.close()
