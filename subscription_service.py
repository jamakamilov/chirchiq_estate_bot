from datetime import datetime, timedelta
from database import Session, User, Subscription
from config import FREE_PERIOD_DAYS, PREMIUM_ROLES, LOCKED_ROLES
from locales import get_text

class SubscriptionService:
    @staticmethod
    def activate_free_period(user_id: int, role: str, lang: str = 'ru'):
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False, get_text("user_not_found", lang)
            
            active_sub = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).first()
            
            if active_sub:
                return False, get_text("subscription_already_active", lang)
            
            days = FREE_PERIOD_DAYS.get(role, 0)
            if days == 0:
                return False, get_text("no_free_period", lang)
            
            start_date = datetime.now()
            end_date = start_date + timedelta(days=days)
            
            subscription = Subscription(
                user_id=user_id,
                role=role,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                is_free_period=True
            )
            
            user.free_period_start = start_date
            user.free_period_end = end_date
            user.free_period_used = True
            
            if role in LOCKED_ROLES:
                user.role_locked = True
            
            session.add(subscription)
            session.commit()
            
            return True, get_text("free_period_activated", lang).format(days=days)
            
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def activate_paid_subscription(user_id: int, role: str, months: int, admin_id: int, lang: str = 'ru'):
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False, get_text("user_not_found", lang)
            
            # Деактивируем старые подписки
            session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).update({'is_active': False})
            
            start_date = datetime.now()
            end_date = start_date + timedelta(days=months*30)
            
            subscription = Subscription(
                user_id=user_id,
                role=role,
                start_date=start_date,
                end_date=end_date,
                is_active=True,
                is_free_period=False,
                payment_confirmed=True,
                admin_id=admin_id
            )
            
            user.role = role
            user.free_period_start = start_date
            user.free_period_end = end_date
            
            session.add(subscription)
            session.commit()
            
            return True, get_text("paid_subscription_activated", lang).format(months=months)
            
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def check_subscription(user_id: int, lang: str = 'ru'):
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False, get_text("user_not_found", lang)
            
            if user.role not in PREMIUM_ROLES:
                return True, get_text("subscription_not_required", lang)
            
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).first()
            
            if not subscription:
                return False, get_text("no_active_subscription", lang)
            
            if datetime.now() > subscription.end_date:
                subscription.is_active = False
                session.commit()
                return False, get_text("subscription_expired", lang)
            
            remaining_days = (subscription.end_date - datetime.now()).days
            return True, get_text("subscription_active", lang).format(days=remaining_days)
            
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def get_subscription_info(user_id: int, lang: str = 'ru'):
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return get_text("user_not_found", lang)
            
            if user.role not in PREMIUM_ROLES:
                return get_text("no_subscription_needed", lang)
            
            subscription = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.is_active == True
            ).first()
            
            if not subscription:
                return get_text("no_active_subscription", lang)
            
            remaining_days = max(0, (subscription.end_date - datetime.now()).days)
            
            if subscription.is_free_period:
                return get_text("free_subscription_info", lang).format(
                    days=remaining_days,
                    end_date=subscription.end_date.strftime("%d.%m.%Y")
                )
            else:
                return get_text("paid_subscription_info", lang).format(
                    days=remaining_days,
                    end_date=subscription.end_date.strftime("%d.%m.%Y")
                )
                
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def can_add_property(user_id: int, lang: str = 'ru'):
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False, get_text("user_not_found", lang)
            
            if user.role in ["seller", "buyer"]:
                return True, ""
            
            if user.role in PREMIUM_ROLES:
                is_active, message = SubscriptionService.check_subscription(user_id, lang)
                return is_active, message
            
            return True, ""
            
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def can_change_role(user_id: int, lang: str = 'ru'):
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                return False, get_text("user_not_found", lang)
            
            if user.role_locked and user.role in LOCKED_ROLES:
                return False, get_text("role_change_locked", lang)
            
            return True, ""
            
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            session.close()
