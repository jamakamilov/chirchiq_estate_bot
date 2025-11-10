from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from locales import TEXTS

# ========== REPLY KEYBOARDS ==========

def get_role_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Клавиатура выбора роли"""
    builder = ReplyKeyboardBuilder()
    
    roles = [
        TEXTS[language]["role_seller"],
        TEXTS[language]["role_buyer"], 
        TEXTS[language]["role_renter"],
        TEXTS[language]["role_realtor"],
        TEXTS[language]["role_agency"],
        TEXTS[language]["role_developer"]
    ]
    
    for role in roles:
        builder.add(KeyboardButton(text=role))
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_main_menu_keyboard(language: str, role: str) -> ReplyKeyboardMarkup:
    """Главное меню в зависимости от роли"""
    builder = ReplyKeyboardBuilder()
    
    # Базовые кнопки для всех ролей
    base_buttons = [
        TEXTS[language]["search_properties"],
        TEXTS[language]["my_profile"],
        TEXTS[language]["favorites"],
        TEXTS[language]["change_currency"],
        TEXTS[language]["ai_features"]
    ]
    
    # Добавляем кнопку добавления объявления для продавцов, риэлторов и т.д.
    if role in ['seller', 'realtor', 'agency', 'developer']:
        base_buttons.insert(1, TEXTS[language]["add_listing"])
    
    for button in base_buttons:
        builder.add(KeyboardButton(text=button))
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_main_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой возврата в главное меню"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=TEXTS[language]["back_to_main"]))
    return builder.as_markup(resize_keyboard=True)

def get_phone_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Клавиатура для запроса номера телефона"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(
        text=TEXTS[language]["send_contact"],
        request_contact=True
    ))
    builder.add(KeyboardButton(text=TEXTS[language]["back_to_main"]))
    return builder.as_markup(resize_keyboard=True)

def get_yes_no_keyboard(language: str) -> ReplyKeyboardMarkup:
    """Клавиатура Да/Нет"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Да"))
    builder.add(KeyboardButton(text="❌ Нет"))
    builder.add(KeyboardButton(text=TEXTS[language]["back_to_main"]))
    return builder.as_markup(resize_keyboard=True)

# ========== INLINE KEYBOARDS ==========

def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_language_ru"),
        InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="set_language_uz"),
        InlineKeyboardButton(text="🇺🇸 English", callback_data="set_language_en")
    )
    builder.adjust(2)
    return builder.as_markup()

def get_currency_keyboard(language: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты"""
    builder = InlineKeyboardBuilder()
    currencies = [
        ("🇺🇿 UZS", "UZS"),
        ("🇺🇸 USD", "USD"),
        ("🇪🇺 EUR", "EUR"),
        ("🇷🇺 RUB", "RUB")
    ]
    
    for text, currency in currencies:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"set_currency_{currency}"
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_property_type_keyboard(language: str, include_any: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора типа недвижимости"""
    builder = InlineKeyboardBuilder()
    
    property_types = [
        ("🏠 Квартира", "apartment"),
        ("🏡 Дом", "house"),
        ("🏢 Офис", "office"),
        ("🏬 Коммерческая", "commercial"),
        ("📅 Аренда", "rent"),
        ("🏗 Новостройка", "new_building")
    ]
    
    for text, prop_type in property_types:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"property_type_{prop_type}"
        ))
    
    if include_any:
        builder.add(InlineKeyboardButton(
            text="📍 Любой тип",
            callback_data="property_type_any"
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_district_keyboard(language: str, include_any: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура выбора района Чирчика"""
    builder = InlineKeyboardBuilder()
    
    districts = [
        "Центр",
        "Старгород",
        "Гидропарк",
        "Северный",
        "Южный", 
        "Восточный",
        "Западный",
        "Промзона",
        "Кирзавод",
        "Текстильщик"
    ]
    
    for district in districts:
        builder.add(InlineKeyboardButton(
            text=district,
            callback_data=f"district_{district}"
        ))
    
    if include_any:
        builder.add(InlineKeyboardButton(
            text=TEXTS[language]["any_district"],
            callback_data="district_any"
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_ai_features_keyboard(language: str) -> InlineKeyboardMarkup:
    """Клавиатура AI функций"""
    builder = InlineKeyboardBuilder()
    
    ai_features = [
        (TEXTS[language]["ai_search"], "ai_search"),
        (TEXTS[language]["ai_price"], "ai_price"),
        (TEXTS[language]["ai_text"], "ai_text"),
        (TEXTS[language]["ai_analytics"], "ai_analytics")
    ]
    
    for text, feature in ai_features:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"ai_{feature}"
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_admin_keyboard(language: str) -> InlineKeyboardMarkup:
    """Клавиатура админ панели"""
    builder = InlineKeyboardBuilder()
    
    admin_features = [
        (TEXTS[language]["stats"], "admin_stats"),
        (TEXTS[language]["users"], "admin_users"),
        (TEXTS[language]["properties"], "admin_properties"),
        (TEXTS[language]["broadcast"], "admin_broadcast"),
        (TEXTS[language]["change_user_role"], "admin_change_role"),
        (TEXTS[language]["contact_requests"], "admin_contact_requests"),
        (TEXTS[language]["advanced_stats"], "admin_advanced_stats"),
        (TEXTS[language]["booking_requests"], "admin_booking_requests"),
        (TEXTS[language]["subscription_requests"], "admin_subscription_requests")
    ]
    
    for text, feature in admin_features:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=feature
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_rating_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для оценки пользователя"""
    builder = InlineKeyboardBuilder()
    
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(
            text="⭐" * i,
            callback_data=f"rate_{i}"
        ))
    
    builder.adjust(5)
    return builder.as_markup()

def get_subscription_keyboard(language: str, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления подпиской"""
    builder = InlineKeyboardBuilder()
    
    subscription_plans = [
        ("1 месяц - 50,000 UZS", "subscription_1"),
        ("3 месяца - 120,000 UZS", "subscription_3"),
        ("6 месяцев - 200,000 UZS", "subscription_6"),
        ("12 месяцев - 350,000 UZS", "subscription_12")
    ]
    
    for text, plan in subscription_plans:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"{plan}_{user_id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_contact_request_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для обработки запроса на контакт"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve_contact_{request_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить", 
            callback_data=f"reject_contact_{request_id}"
        )
    )
    
    builder.adjust(2)
    return builder.as_markup()

def get_quick_filters_keyboard(language: str) -> InlineKeyboardMarkup:
    """Клавиатура быстрых фильтров"""
    builder = InlineKeyboardBuilder()
    
    filters = [
        (TEXTS[language]["filter_by_price"], "filter_price"),
        (TEXTS[language]["filter_by_rooms"], "filter_rooms"),
        (TEXTS[language]["filter_by_area"], "filter_area"),
        (TEXTS[language]["filter_recent"], "filter_recent"),
        (TEXTS[language]["save_search"], "save_search")
    ]
    
    for text, filter_type in filters:
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=filter_type
        ))
    
    builder.add(InlineKeyboardButton(
        text=TEXTS[language]["back_to_main"],
        callback_data="back_to_main"
    ))
    
    builder.adjust(2)
    return builder.as_markup()

def get_booking_keyboard(language: str, property_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для бронирования"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text=TEXTS[language]["book_property"],
            callback_data=f"book_{property_id}"
        ),
        InlineKeyboardButton(
            text=TEXTS[language]["check_availability"],
            callback_data=f"check_availability_{property_id}"
        )
    )
    
    builder.adjust(1)
    return builder.as_markup()

def get_chat_keyboard(language: str, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для чата"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text=TEXTS[language]["start_chat"],
            callback_data=f"start_chat_{user_id}"
        )
    )
    
    return builder.as_markup()

def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    """Клавиатура пагинации"""
    builder = InlineKeyboardBuilder()
    
    if page > 1:
        builder.add(InlineKeyboardButton(
            text="⬅ Назад",
            callback_data=f"{prefix}page{page-1}"
        ))
    
    builder.add(InlineKeyboardButton(
        text=f"{page}/{total_pages}",
        callback_data="current_page"
    ))
    
    if page < total_pages:
        builder.add(InlineKeyboardButton(
            text="Вперед ➡",
            callback_data=f"{prefix}page{page+1}"
        ))
    
    builder.adjust(3)
    return builder.as_markup()

def get_confirmation_keyboard(language: str, action: str) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения действия"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data=f"confirm_{action}"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="cancel_action"
        )
    )
    
    builder.adjust(2)
    return builder.as_markup()

def get_user_management_keyboard(language: str, user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления пользователем (для админа)"""
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="👤 Сменить роль",
            callback_data=f"admin_change_role_{user_id}"
        ),
        InlineKeyboardButton(
            text="📊 Статистика",
            callback_data=f"admin_user_stats_{user_id}"
        ),
        InlineKeyboardButton(
            text="📨 Написать",
            callback_data=f"admin_message_{user_id}"
        ),
        InlineKeyboardButton(
            text="🔧 Управление подпиской",
            callback_data=f"admin_subscription_{user_id}"
        )
    )
    
    builder.adjust(2)
    return builder.as_markup()
