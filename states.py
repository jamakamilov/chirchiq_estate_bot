from aiogram.fsm.state import State, StatesGroup

class PropertyStates(StatesGroup):
    """Состояния для добавления объявления"""
    choosing_property_type = State()
    choosing_district = State()
    entering_address = State()
    entering_price = State()
    entering_rooms = State()
    entering_area = State()
    entering_description = State()
    adding_photos = State()
    confirming_listing = State()

class SearchStates(StatesGroup):
    """Состояния для поиска недвижимости"""
    choosing_property_type = State()
    choosing_district = State()
    setting_filters = State()
    viewing_results = State()

class AdminStates(StatesGroup):
    """Состояния для админ панели"""
    admin_menu = State()
    managing_users = State()
    managing_properties = State()
    broadcasting = State()
    changing_user_role = State()
    managing_contact_requests = State()
    viewing_stats = State()

class SubscriptionStates(StatesGroup):
    """Состояния для управления подпиской"""
    choosing_plan = State()
    processing_payment = State()
    extending_subscription = State()

class ChatStates(StatesGroup):
    """Состояния для чата"""
    waiting_for_message = State()
    active_chat = State()

class RatingStates(StatesGroup):
    """Состояния для рейтингов"""
    selecting_rating = State()
    writing_review = State()

class BookingStates(StatesGroup):
    """Состояния для бронирования"""
    selecting_dates = State()
    entering_check_in = State()
    entering_check_out = State()
    entering_guests = State()
    confirming_booking = State()

class ContactStates(StatesGroup):
    """Состояния для запроса контактов"""
    requesting_contact = State()
    approving_contact = State()

class AIPriceStates(StatesGroup):
    """Состояния для AI оценки цены"""
    entering_property_details = State()
    analyzing_market = State()

class AITextStates(StatesGroup):
    """Состояния для генерации текстов"""
    selecting_text_type = State()
    entering_property_info = State()
    generating_text = State()

class UserProfileStates(StatesGroup):
    """Состояния для управления профилем"""
    editing_profile = State()
    changing_phone = State()
    updating_preferences = State()
