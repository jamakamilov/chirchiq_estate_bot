from database import Session, User, Property, ContactRequest
from config import RESTRICTED_CONTACT_ROLES, ADMINS, ADMIN_CONTACT
from locales import get_text

class ContactService:
    @staticmethod
    def can_show_contact(property_owner_id: int, requester_id: int, lang: str = 'ru'):
        """Можно ли показывать контактные данные"""
        session = Session()
        
        try:
            property_owner = session.query(User).filter(User.telegram_id == property_owner_id).first()
            
            if not property_owner:
                return False, get_text("user_not_found", lang)
            
            # Если владелец не входит в ограниченные роли, показываем контакт
            if property_owner.role not in RESTRICTED_CONTACT_ROLES:
                return True, ""
            
            # Если запрашивающий - администратор, показываем контакт
            if requester_id in ADMINS:
                return True, ""
            
            # Для ограниченных ролей не показываем контакт напрямую
            return False, get_text("contact_restricted", lang).format(admin=ADMIN_CONTACT)
            
        except Exception as e:
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def request_contact(requester_id: int, target_user_id: int, property_id: int, lang: str = 'ru'):
        """Запросить контакт через администратора"""
        session = Session()
        
        try:
            # Проверяем существование пользователей и объекта
            requester = session.query(User).filter(User.telegram_id == requester_id).first()
            target_user = session.query(User).filter(User.telegram_id == target_user_id).first()
            property_obj = session.query(Property).filter(Property.id == property_id).first()
            
            if not requester or not target_user or not property_obj:
                return False, get_text("request_data_invalid", lang)
            
            # Проверяем, не отправлен ли уже запрос
            existing_request = session.query(ContactRequest).filter(
                ContactRequest.requester_id == requester_id,
                ContactRequest.target_user_id == target_user_id,
                ContactRequest.property_id == property_id,
                ContactRequest.status == 'pending'
            ).first()
            
            if existing_request:
                return False, get_text("contact_request_pending", lang)
            
            # Создаем запрос
            contact_request = ContactRequest(
                requester_id=requester_id,
                target_user_id=target_user_id,
                property_id=property_id
            )
            
            session.add(contact_request)
            session.commit()
            
            return True, get_text("contact_request_sent", lang)
            
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def get_pending_requests():
        """Получить все pending запросы на контакт"""
        session = Session()
        
        try:
            requests = session.query(ContactRequest).filter(
                ContactRequest.status == 'pending'
            ).order_by(ContactRequest.created_at.desc()).all()
            
            return requests, None
            
        except Exception as e:
            return None, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def approve_contact_request(request_id: int, admin_id: int, lang: str = 'ru'):
        """Одобрить запрос на контакт"""
        session = Session()
        
        try:
            contact_request = session.query(ContactRequest).filter(ContactRequest.id == request_id).first()
            
            if not contact_request:
                return False, get_text("request_not_found", lang)
            
            contact_request.status = 'approved'
            contact_request.admin_id = admin_id
            contact_request.processed_at = datetime.now()
            
            session.commit()
            
            return True, get_text("contact_request_approved", lang)
            
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
    
    @staticmethod
    def reject_contact_request(request_id: int, admin_id: int, lang: str = 'ru'):
        """Отклонить запрос на контакт"""
        session = Session()
        
        try:
            contact_request = session.query(ContactRequest).filter(ContactRequest.id == request_id).first()
            
            if not contact_request:
                return False, get_text("request_not_found", lang)
            
            contact_request.status = 'rejected'
            contact_request.admin_id = admin_id
            contact_request.processed_at = datetime.now()
            
            session.commit()
            
            return True, get_text("contact_request_rejected", lang)
            
        except Exception as e:
            session.rollback()
            return False, f"Error: {str(e)}"
        finally:
            session.close()
