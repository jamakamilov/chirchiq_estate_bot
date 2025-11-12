from datetime import datetime, timedelta
from database import Session, Booking, Property, User
from sqlalchemy import and_
from locales import get_text

class BookingService:
    @staticmethod
    def check_availability(property_id, check_in, check_out):
        """Проверяет доступность объекта на даты"""
        session = Session()
        try:
            conflicting_bookings = session.query(Booking).filter(
                Booking.property_id == property_id,
                Booking.status == 'confirmed',
                and_(
                    Booking.check_in < check_out,
                    Booking.check_out > check_in
                )
            ).count()
            
            return conflicting_bookings == 0
        finally:
            session.close()
    
    @staticmethod
    def create_booking(property_id, user_id, check_in, check_out, guests=1):
        """Создает бронирование"""
        session = Session()
        try:
            if not BookingService.check_availability(property_id, check_in, check_out):
                return False, "Объект недоступен на указанные даты"
            
            property_obj = session.query(Property).filter(Property.id == property_id).first()
            if not property_obj:
                return False, "Объект не найден"
            
            # Рассчитываем цену
            nights = (check_out - check_in).days
            if nights <= 0:
                return False, "Неверные даты бронирования"
            
            total_price = property_obj.price_uzs * nights
            
            booking = Booking(
                property_id=property_id,
                user_id=user_id,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                total_price=total_price,
                status='pending',
                created_at=datetime.now()
            )
            
            session.add(booking)
            session.commit()
            return True, booking.id
            
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()
    
    @staticmethod
    def confirm_booking(booking_id, admin_id):
        """Подтверждает бронирование администратором"""
        session = Session()
        try:
            booking = session.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                return False, "Бронирование не найдено"
            
            booking.status = 'confirmed'
            booking.confirmed_at = datetime.now()
            booking.admin_id = admin_id
            
            session.commit()
            return True, "Бронирование подтверждено"
            
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()
    
    @staticmethod
    def get_user_bookings(user_id):
        """Получает бронирования пользователя"""
        session = Session()
        try:
            bookings = session.query(Booking).filter(
                Booking.user_id == user_id
            ).order_by(Booking.created_at.desc()).all()
            
            return bookings
        finally:
            session.close()
    
    @staticmethod
    def get_property_bookings(property_id):
        """Получает бронирования объекта"""
        session = Session()
        try:
            bookings = session.query(Booking).filter(
                Booking.property_id == property_id
            ).order_by(Booking.check_in).all()
            
            return bookings
        finally:
            session.close()
