import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN, ADMIN_IDS
from database import Database
from locales import TEXTS
from states import PropertyStates, SearchStates, AdminStates
from keyboards import (
    get_role_keyboard, get_main_menu_keyboard, get_property_type_keyboard,
    get_district_keyboard, get_currency_keyboard, get_ai_features_keyboard,
    get_admin_keyboard, get_language_keyboard, get_rating_keyboard,
    get_back_to_main_keyboard, get_yes_no_keyboard, get_phone_keyboard
)
from utils import format_price, send_notification, check_subscription

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

# Инициализация базы данных
db = Database()

class UserStates(StatesGroup):
    choosing_role = State()
    main_menu = State()
    adding_listing = State()
    searching = State()

# ========== START HANDLER ==========

@dp.message(F.text == "🚀 Start")
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик начала работы"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user:
        # Пользователь уже существует
        language = user.get('language', 'ru')
        role = user.get('role')
        
        if role:
            # Пользователь уже выбрал роль - показываем главное меню
            await state.set_state(UserStates.main_menu)
            await show_main_menu(message, state, language)
        else:
            # Пользователь не выбрал роль
            await state.set_state(UserStates.choosing_role)
            await show_role_selection(message, language)
    else:
        # Новый пользователь
        language = 'ru'
        await db.create_user(user_id, message.from_user.username, message.from_user.first_name, language)
        await state.set_state(UserStates.choosing_role)
        await show_role_selection(message, language)

@dp.message(F.text == "🌐 Language")
async def change_language(message: types.Message):
    """Смена языка"""
    await show_language_selection(message)

@dp.message(F.text == "⚙ Admin")
async def admin_panel(message: types.Message, state: FSMContext):
    """Админ панель"""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Access denied")
        return
        
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    await state.set_state(AdminStates.admin_menu)
    await message.answer(
        TEXTS[language]["admin_welcome"],
        reply_markup=get_admin_keyboard(language)
    )

# ========== ROLE SELECTION ==========

async def show_role_selection(message: types.Message, language: str):
    """Показ выбора роли"""
    keyboard = get_role_keyboard(language)
    await message.answer(
        TEXTS[language]["welcome"] + "\n\n" + TEXTS[language]["choose_role"],
        reply_markup=keyboard
    )

@dp.message(F.text.in_([
    "👤 Seller", "👤 Buyer", "👤 Renter", 
    "🤵 Realtor", "🏢 Agency", "🏗 Developer",
    "👤 Sotuvchi", "👤 Xaridor", "👤 Ijarachi",
    "🤵 Rieltor", "🏢 Agentlik", "🏗 Quruvchi",
    "👤 Продавец", "👤 Покупатель", "👤 Арендатор",
    "🤵 Риэлтор", "🏢 Агентство", "🏗 Застройщик"
]))
async def process_role_selection(message: types.Message, state: FSMContext):
    """Обработка выбора роли"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    # Определяем выбранную роль
    role_text = message.text
    role_map = {
        # English
        "👤 Seller": "seller",
        "👤 Buyer": "buyer", 
        "👤 Renter": "renter",
        "🤵 Realtor": "realtor",
        "🏢 Agency": "agency",
        "🏗 Developer": "developer",
        # Uzbek
        "👤 Sotuvchi": "seller",
        "👤 Xaridor": "buyer",
        "👤 Ijarachi": "renter",
        "🤵 Rieltor": "realtor",
        "🏢 Agentlik": "agency",
        "🏗 Quruvchi": "developer",
        # Russian
        "👤 Продавец": "seller",
        "👤 Покупатель": "buyer",
        "👤 Арендатор": "renter",
        "🤵 Риэлтор": "realtor",
        "🏢 Агентство": "agency",
        "🏗 Застройщик": "developer"
    }
    
    role = role_map.get(role_text)
    if not role:
        await message.answer("❌ Unknown role")
        return
    
    # Проверяем, можно ли пользователю самостоятельно сменить роль
    current_role = user.get('role')
    if current_role and current_role in ['developer', 'agency', 'realtor', 'renter']:
        # Роль заблокирована для самостоятельной смены
        await message.answer(
            TEXTS[language]["role_change_locked"],
            reply_markup=get_back_to_main_keyboard(language)
        )
        return
    
    # Обновляем роль пользователя
    await db.update_user_role(user_id, role)
    
    # Активируем бесплатный период если положено
    await activate_free_subscription(user_id, role, language)
    
    await state.set_state(UserStates.main_menu)
    await show_main_menu(message, state, language)

# ========== MAIN MENU ==========

async def show_main_menu(message: types.Message, state: FSMContext, language: str):
    """Показ главного меню"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    role = user.get('role')
    
    # Создаем клавиатуру главного меню
    keyboard = ReplyKeyboardBuilder()
    
    # Базовые кнопки для всех
    buttons = [
        "🔍 Search", "👤 Profile", "❤ Favorites",
        "💰 Currency", "🤖 AI Features", "🌐 Language"
    ]
    
    # Добавляем кнопку добавления объявления для определенных ролей
    if role in ['seller', 'realtor', 'agency', 'developer']:
        buttons.insert(1, "➕ Add Listing")
    
    # Добавляем админку для администраторов
    if user_id in ADMIN_IDS:
        buttons.append("⚙ Admin")
    
    for button in buttons:
        keyboard.add(KeyboardButton(text=button))
    
    keyboard.adjust(2)
    
    await message.answer(
        TEXTS[language]["main_menu"],
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

@dp.message(F.text.in_([
    "🔍 Search", "➕ Add Listing", "👤 Profile",
    "❤ Favorites", "💰 Currency", "🤖 AI Features",
    "🔍 Qidirish", "➕ E'lon qo'shish", "👤 Profil",
    "❤ Sevimlilar", "💰 Valyuta", "🤖 AI funksiyalari",
    "🔍 Поиск", "➕ Добавить объявление", "👤 Профиль",
    "❤ Избранное", "💰 Валюта", "🤖 AI функции"
]))
async def process_main_menu(message: types.Message, state: FSMContext):
    """Обработка главного меню"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    role = user.get('role')
    
    text = message.text
    
    if text in ["🔍 Search", "🔍 Qidirish", "🔍 Поиск"]:
        # Поиск недвижимости
        await state.set_state(SearchStates.choosing_property_type)
        await message.answer(
            TEXTS[language]["choose_property_type"],
            reply_markup=get_property_type_keyboard(language, include_any=True)
        )
        
    elif text in ["➕ Add Listing", "➕ E'lon qo'shish", "➕ Добавить объявление"]:
        # Добавление объявления
        if not await check_subscription(user_id, db):
            await message.answer(
                TEXTS[language]["subscription_required"],
                reply_markup=get_back_to_main_keyboard(language)
            )
            return
            
        await state.set_state(PropertyStates.choosing_property_type)
        await message.answer(
            TEXTS[language]["choose_property_type"],
            reply_markup=get_property_type_keyboard(language)
        )
        
    elif text in ["👤 Profile", "👤 Profil", "👤 Профиль"]:
        # Мой профиль
        await show_user_profile(message, user_id, language)
        
    elif text in ["❤ Favorites", "❤ Sevimlilar", "❤ Избранное"]:
        # Избранное
        await show_favorites(message, user_id, language)
        
    elif text in ["💰 Currency", "💰 Valyuta", "💰 Валюта"]:
        # Смена валюты
        await show_currency_selection(message, language)
        
    elif text in ["🤖 AI Features", "🤖 AI funksiyalari", "🤖 AI функции"]:
        # AI функции
        await show_ai_features(message, language)

# ========== PROFILE MANAGEMENT ==========

async def show_user_profile(message: types.Message, user_id: int, language: str):
    """Показ профиля пользователя"""
    user = await db.get_user(user_id)
    subscription = await db.get_user_subscription(user_id)
    
    profile_text = f"👤 <b>{TEXTS[language]['my_profile']}</b>\n\n"
    profile_text += f"🆔 ID: {user_id}\n"
    profile_text += f"📝 Name: {user.get('full_name', message.from_user.full_name)}\n"
    profile_text += f"👤 Role: {TEXTS[language].get('role_' + user.get('role', 'buyer'), user.get('role', 'buyer'))}\n"
    profile_text += f"🌐 Language: {language.upper()}\n"
    profile_text += f"💰 Currency: {user.get('currency', 'UZS')}\n\n"
    
    # Информация о подписке
    if subscription:
        days_left = (subscription['end_date'] - datetime.now()).days
        if subscription['is_free']:
            profile_text += f"🎁 <b>Free Subscription</b>\n"
            profile_text += f"⏰ Days left: {days_left}\n"
            profile_text += f"📅 Valid until: {subscription['end_date'].strftime('%d.%m.%Y')}\n"
        else:
            profile_text += f"⭐ <b>Paid Subscription</b>\n"
            profile_text += f"⏰ Days left: {days_left}\n"
            profile_text += f"📅 Valid until: {subscription['end_date'].strftime('%d.%m.%Y')}\n"
    else:
        profile_text += "❌ <b>No active subscription</b>\n"
    
    # Рейтинг
    rating_stats = await db.get_user_rating_stats(user_id)
    if rating_stats['count'] > 0:
        profile_text += f"\n⭐ <b>Rating: {rating_stats['average']:.1f}/5.0</b>\n"
        profile_text += f"📊 Total ratings: {rating_stats['count']}\n"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✏ Edit Profile",
        callback_data="edit_profile"
    ))
    keyboard.add(InlineKeyboardButton(
        text="📋 My Subscription", 
        callback_data="my_subscription"
    ))
    keyboard.adjust(1)
    
    await message.answer(profile_text, reply_markup=keyboard.as_markup())

# ========== SUBSCRIPTION MANAGEMENT ==========

async def activate_free_subscription(user_id: int, role: str, language: str):
    """Активация бесплатного периода для новых ролей"""
    free_periods = {
        'developer': 7,
        'agency': 14, 
        'realtor': 21,
        'renter': 30
    }
    
    if role in free_periods:
        days = free_periods[role]
        await db.create_subscription(user_id, days, is_free=True)
        await send_notification(bot, user_id, 
            TEXTS[language]["free_period_activated"].format(days=days)
        )

# ========== FAVORITES ==========

async def show_favorites(message: types.Message, user_id: int, language: str):
    """Показ избранных объявлений"""
    favorites = await db.get_user_favorites(user_id)
    
    if not favorites:
        await message.answer(
            TEXTS[language]["favorites_empty"],
            reply_markup=get_back_to_main_keyboard(language)
        )
        return
    
    await message.answer(f"❤ <b>{TEXTS[language]['favorites']}</b> ({len(favorites)}):")
    
    for favorite in favorites[:5]:  # Показываем первые 5
        property_data = await db.get_property(favorite['property_id'])
        if property_data:
            await send_property_preview(message, property_data, language, show_favorite_button=False)

# ========== PROPERTY MANAGEMENT ==========

async def send_property_preview(message: types.Message, property_data: dict, language: str, show_favorite_button: bool = True):
    """Отправка превью объявления"""
    text = format_property_text(property_data, language)
    keyboard = InlineKeyboardBuilder()
    
    if show_favorite_button:
        # Проверяем, есть ли уже в избранном
        is_favorite = await db.is_property_in_favorites(message.from_user.id, property_data['id'])
        favorite_text = TEXTS[language]["add_to_favorites"] if not is_favorite else "❤ In favorites"
        favorite_callback = f"add_favorite_{property_data['id']}" if not is_favorite else f"remove_favorite_{property_data['id']}"
        
        keyboard.add(InlineKeyboardButton(
            text=favorite_text,
            callback_data=favorite_callback
        ))
    
    # Кнопка запроса контакта
    keyboard.add(InlineKeyboardButton(
        text=TEXTS[language]["request_contact"],
        callback_data=f"request_contact_{property_data['user_id']}_{property_data['id']}"
    ))
    
    keyboard.adjust(1)
    
    # Если есть фото, отправляем с фото
    if property_data.get('photos'):
        await message.answer_photo(
            property_data['photos'][0],
            caption=text,
            reply_markup=keyboard.as_markup()
        )
    else:
        await message.answer(
            text,
            reply_markup=keyboard.as_markup()
        )

def format_property_text(property_data: dict, language: str) -> str:
    """Форматирование текста объявления"""
    property_type_map = {
        'apartment': '🏠 Apartment',
        'house': '🏡 House',
        'office': '🏢 Office', 
        'commercial': '🏬 Commercial',
        'rent': '📅 Rent',
        'new_building': '🏗 New Building'
    }
    
    property_type = property_type_map.get(property_data['type'], property_data['type'])
    district = property_data['district']
    address = property_data['address']
    price = format_price(property_data['price'], property_data.get('currency', 'UZS'))
    rooms = property_data['rooms']
    area = property_data['area']
    description = property_data['description']
    
    text = f"<b>{property_type}</b>\n\n"
    text += f"📍 <b>District:</b> {district}\n"
    text += f"📌 <b>Address:</b> {address}\n"
    text += f"💰 <b>Price:</b> {price}\n"
    text += f"🚪 <b>Rooms:</b> {rooms}\n"
    text += f"📐 <b>Area:</b> {area} m²\n\n"
    text += f"📝 <b>Description:</b>\n{description}\n\n"
    text += f"👤 <b>Contacts:</b> [available on request]"
    
    return text

# ========== CALLBACK QUERIES ==========

@dp.callback_query(F.data.startswith("add_favorite_"))
async def add_to_favorites(callback: types.CallbackQuery):
    """Добавление в избранное"""
    property_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    success = await db.add_to_favorites(user_id, property_id)
    if success:
        await callback.answer(TEXTS[language]["added_to_favorites"])
        # Обновляем кнопку
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text="❤ In favorites",
            callback_data=f"remove_favorite_{property_id}"
        ))
        keyboard.add(InlineKeyboardButton(
            text=TEXTS[language]["request_contact"],
            callback_data=f"request_contact_{callback.message.reply_to_message.from_user.id}_{property_id}"
        ))
        keyboard.adjust(1)
        
        await callback.message.edit_reply_markup(reply_markup=keyboard.as_markup())
    else:
        await callback.answer(TEXTS[language]["already_in_favorites"])

@dp.callback_query(F.data.startswith("request_contact_"))
async def request_contact(callback: types.CallbackQuery):
    """Запрос контактов"""
    parts = callback.data.split("_")
    if len(parts) < 3:
        await callback.answer("❌ Invalid request")
        return
        
    target_user_id = int(parts[2])
    property_id = int(parts[3]) if len(parts) > 3 else None
    
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    # Создаем запрос на контакт
    request_id = await db.create_contact_request(user_id, target_user_id, property_id)
    
    if request_id:
        # Уведомляем администраторов
        for admin_id in ADMIN_IDS:
            await bot.send_message(
                admin_id,
                f"📞 New contact request!\n"
                f"From: {user.get('full_name')} (ID: {user_id})\n"
                f"To: user ID: {target_user_id}\n"
                f"Property: {property_id if property_id else 'not specified'}\n\n"
                f"Request ID: {request_id}"
            )
        
        await callback.answer(TEXTS[language]["contact_request_sent"])
    else:
        await callback.answer(TEXTS[language]["contact_request_pending"])

# ========== LANGUAGE SELECTION ==========

async def show_language_selection(message: types.Message):
    """Показ выбора языка"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    current_language = user.get('language', 'ru') if user else 'ru'
    
    await message.answer(
        TEXTS[current_language]["choose_language"],
        reply_markup=get_language_keyboard()
    )

@dp.callback_query(F.data.startswith("set_language_"))
async def set_language(callback: types.CallbackQuery):
    """Установка языка"""
    language = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    await db.update_user_language(user_id, language)
    await callback.answer(TEXTS[language]["language_set"].format(language=language.upper()))
    
    # Обновляем сообщение
    await callback.message.edit_text(
        TEXTS[language]["language_set"].format(language=language.upper()),
        reply_markup=get_back_to_main_keyboard(language)
    )

# ========== CURRENCY SELECTION ==========

async def show_currency_selection(message: types.Message, language: str):
    """Показ выбора валюты"""
    await message.answer(
        "💰 Choose currency for price display:",
        reply_markup=get_currency_keyboard(language)
    )

@dp.callback_query(F.data.startswith("set_currency_"))
async def set_currency(callback: types.CallbackQuery):
    """Установка валюты"""
    currency = callback.data.split("_")[2]
    user_id = callback.from_user.id
    
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    await db.update_user_currency(user_id, currency)
    await callback.answer(TEXTS[language]["currency_set"].format(currency=currency))
    
    await callback.message.edit_text(
        TEXTS[language]["currency_set"].format(currency=currency),
        reply_markup=get_back_to_main_keyboard(language)
    )

# ========== AI FEATURES ==========

async def show_ai_features(message: types.Message, language: str):
    """Показ AI функций"""
    await message.answer(
        "🤖 <b>AI Features</b>\n\n"
        "Choose one of the available AI features:",
        reply_markup=get_ai_features_keyboard(language)
    )

# ========== BACK TO MAIN MENU ==========

@dp.message(F.text.in_([
    "🔙 Main Menu", "🔙 Asosiy menyu", "🔙 Главное меню",
    "← Back", "← Orqaga", "← Назад"
]))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    await state.set_state(UserStates.main_menu)
    await show_main_menu(message, state, language)

@dp.callback_query(F.data == "back_to_main")
async def back_to_main_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик возврата в главное меню из inline клавиатуры"""
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    await state.set_state(UserStates.main_menu)
    await callback.message.edit_text(
        TEXTS[language]["main_menu"]
    )
    await show_main_menu(callback.message, state, language)

# ========== WELCOME MESSAGE ==========

@dp.message()
async def welcome_message(message: types.Message, state: FSMContext):
    """Приветственное сообщение для новых пользователей"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        # Создаем пользователя и показываем стартовое меню
        language = 'ru'
        await db.create_user(user_id, message.from_user.username, message.from_user.first_name, language)
        
        welcome_keyboard = ReplyKeyboardBuilder()
        welcome_keyboard.add(KeyboardButton(text="🚀 Start"))
        welcome_keyboard.adjust(1)
        
        await message.answer(
            "🏡 Welcome to Chirchiq Estate Bot!\n\n"
            "I will help you find or list real estate in Chirchiq.\n\n"
            "Press 🚀 Start to begin!",
            reply_markup=welcome_keyboard.as_markup(resize_keyboard=True)
        )
    else:
        # Пользователь существует, но отправил неизвестную команду
        language = user.get('language', 'ru')
        await message.answer(
            "❌ Unknown command. Please use the menu buttons.",
            reply_markup=get_back_to_main_keyboard(language)
        )

# ========== ERROR HANDLER ==========

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Обработчик ошибок"""
    logger.error(f"Error processing update {update}: {exception}")
    
    if update.message:
        await update.message.answer("❌ An error occurred. Please try again later.")

# ========== START BOT ==========

async def main():
    """Основная функция запуска бота"""
    logger.info("Starting bot...")
    
    # Создаем таблицы в базе данных
    await db.create_tables()
    
    # Запускаем бота
    await dp.start_polling(bot)

if _name_ == "_main_":
    asyncio.run(main())
