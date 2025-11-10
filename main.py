import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
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
    get_back_to_main_keyboard, get_yes_no_keyboard
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

# ========== BASIC HANDLERS ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start"""
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

@dp.message(Command("language"))
async def cmd_language(message: types.Message):
    """Смена языка"""
    await show_language_selection(message)

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    """Админ панель"""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Доступ запрещен")
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
    TEXTS["ru"]["role_seller"], TEXTS["uz"]["role_seller"], TEXTS["en"]["role_seller"],
    TEXTS["ru"]["role_buyer"], TEXTS["uz"]["role_buyer"], TEXTS["en"]["role_buyer"],
    TEXTS["ru"]["role_renter"], TEXTS["uz"]["role_renter"], TEXTS["en"]["role_renter"],
    TEXTS["ru"]["role_realtor"], TEXTS["uz"]["role_realtor"], TEXTS["en"]["role_realtor"],
    TEXTS["ru"]["role_agency"], TEXTS["uz"]["role_agency"], TEXTS["en"]["role_agency"],
    TEXTS["ru"]["role_developer"], TEXTS["uz"]["role_developer"], TEXTS["en"]["role_developer"]
]))
async def process_role_selection(message: types.Message, state: FSMContext):
    """Обработка выбора роли"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    # Определяем выбранную роль
    role_text = message.text
    role_map = {
        # Русский
        TEXTS["ru"]["role_seller"]: "seller",
        TEXTS["ru"]["role_buyer"]: "buyer", 
        TEXTS["ru"]["role_renter"]: "renter",
        TEXTS["ru"]["role_realtor"]: "realtor",
        TEXTS["ru"]["role_agency"]: "agency",
        TEXTS["ru"]["role_developer"]: "developer",
        # Узбекский
        TEXTS["uz"]["role_seller"]: "seller",
        TEXTS["uz"]["role_buyer"]: "buyer",
        TEXTS["uz"]["role_renter"]: "renter",
        TEXTS["uz"]["role_realtor"]: "realtor",
        TEXTS["uz"]["role_agency"]: "agency",
        TEXTS["uz"]["role_developer"]: "developer",
        # Английский
        TEXTS["en"]["role_seller"]: "seller",
        TEXTS["en"]["role_buyer"]: "buyer",
        TEXTS["en"]["role_renter"]: "renter",
        TEXTS["en"]["role_realtor"]: "realtor",
        TEXTS["en"]["role_agency"]: "agency",
        TEXTS["en"]["role_developer"]: "developer"
    }
    
    role = role_map.get(role_text)
    if not role:
        await message.answer("❌ Неизвестная роль")
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
    
    keyboard = get_main_menu_keyboard(language, role)
    await message.answer(
        TEXTS[language]["main_menu"],
        reply_markup=keyboard
    )

@dp.message(F.text.in_([
    TEXTS["ru"]["search_properties"], TEXTS["uz"]["search_properties"], TEXTS["en"]["search_properties"],
    TEXTS["ru"]["add_listing"], TEXTS["uz"]["add_listing"], TEXTS["en"]["add_listing"],
    TEXTS["ru"]["my_profile"], TEXTS["uz"]["my_profile"], TEXTS["en"]["my_profile"],
    TEXTS["ru"]["favorites"], TEXTS["uz"]["favorites"], TEXTS["en"]["favorites"],
    TEXTS["ru"]["change_currency"], TEXTS["uz"]["change_currency"], TEXTS["en"]["change_currency"],
    TEXTS["ru"]["ai_features"], TEXTS["uz"]["ai_features"], TEXTS["en"]["ai_features"]
]))
async def process_main_menu(message: types.Message, state: FSMContext):
    """Обработка главного меню"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    role = user.get('role')
    
    text = message.text
    
    if text in [TEXTS["ru"]["search_properties"], TEXTS["uz"]["search_properties"], TEXTS["en"]["search_properties"]]:
        # Поиск недвижимости
        await state.set_state(SearchStates.choosing_property_type)
        await message.answer(
            TEXTS[language]["choose_property_type"],
            reply_markup=get_property_type_keyboard(language, include_any=True)
        )
        
    elif text in [TEXTS["ru"]["add_listing"], TEXTS["uz"]["add_listing"], TEXTS["en"]["add_listing"]]:
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
        
    elif text in [TEXTS["ru"]["my_profile"], TEXTS["uz"]["my_profile"], TEXTS["en"]["my_profile"]]:
        # Мой профиль
        await show_user_profile(message, user_id, language)
        
    elif text in [TEXTS["ru"]["favorites"], TEXTS["uz"]["favorites"], TEXTS["en"]["favorites"]]:
        # Избранное
        await show_favorites(message, user_id, language)
        
    elif text in [TEXTS["ru"]["change_currency"], TEXTS["uz"]["change_currency"], TEXTS["en"]["change_currency"]]:
        # Смена валюты
        await show_currency_selection(message, language)
        
    elif text in [TEXTS["ru"]["ai_features"], TEXTS["uz"]["ai_features"], TEXTS["en"]["ai_features"]]:
        # AI функции
        await show_ai_features(message, language)

# ========== PROFILE MANAGEMENT ==========

async def show_user_profile(message: types.Message, user_id: int, language: str):
    """Показ профиля пользователя"""
    user = await db.get_user(user_id)
    subscription = await db.get_user_subscription(user_id)
    
    profile_text = f"👤 <b>Ваш профиль</b>\n\n"
    profile_text += f"🆔 ID: {user_id}\n"
    profile_text += f"📝 Имя: {user.get('full_name', 'Не указано')}\n"
    profile_text += f"👤 Роль: {TEXTS[language].get('role_' + user.get('role', 'buyer'), user.get('role', 'buyer'))}\n"
    profile_text += f"🌐 Язык: {language.upper()}\n"
    profile_text += f"💰 Валюта: {user.get('currency', 'UZS')}\n\n"
    
    # Информация о подписке
    if subscription:
        days_left = (subscription['end_date'] - datetime.now()).days
        if subscription['is_free']:
            profile_text += f"🎁 <b>Бесплатная подписка</b>\n"
            profile_text += f"⏰ Осталось дней: {days_left}\n"
            profile_text += f"📅 Действует до: {subscription['end_date'].strftime('%d.%m.%Y')}\n"
        else:
            profile_text += f"⭐ <b>Платная подписка</b>\n"
            profile_text += f"⏰ Осталось дней: {days_left}\n"
            profile_text += f"📅 Действует до: {subscription['end_date'].strftime('%d.%m.%Y')}\n"
    else:
        profile_text += "❌ <b>Нет активной подписки</b>\n"
    
    # Рейтинг
    rating_stats = await db.get_user_rating_stats(user_id)
    if rating_stats['count'] > 0:
        profile_text += f"\n⭐ <b>Рейтинг: {rating_stats['average']:.1f}/5.0</b>\n"
        profile_text += f"📊 Всего оценок: {rating_stats['count']}\n"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="✏ Изменить профиль",
        callback_data="edit_profile"
    ))
    keyboard.add(InlineKeyboardButton(
        text="📋 Моя подписка", 
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
    
    await message.answer(f"❤ <b>Ваши избранные объявления</b> ({len(favorites)}):")
    
    for favorite in favorites[:10]:  # Показываем первые 10
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
        favorite_text = TEXTS[language]["add_to_favorites"] if not is_favorite else "❤ В избранном"
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
        # В реальной реализации здесь будет отправка медиа-группы
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
    property_type = property_data['type']
    district = property_data['district']
    address = property_data['address']
    price = format_price(property_data['price'], property_data.get('currency', 'UZS'))
    rooms = property_data['rooms']
    area = property_data['area']
    description = property_data['description']
    
    text = f"🏠 <b>{property_type.upper()}</b>\n\n"
    text += f"📍 <b>Район:</b> {district}\n"
    text += f"📌 <b>Адрес:</b> {address}\n"
    text += f"💰 <b>Цена:</b> {price}\n"
    text += f"🚪 <b>Комнат:</b> {rooms}\n"
    text += f"📐 <b>Площадь:</b> {area} м²\n\n"
    text += f"📝 <b>Описание:</b>\n{description}\n\n"
    text += f"👤 <b>Контакты:</b> [доступны по запросу]"
    
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
            text="❤ В избранном",
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
                f"📞 Новый запрос на контакт!\n"
                f"От: {user.get('full_name')} (ID: {user_id})\n"
                f"К: пользователь ID: {target_user_id}\n"
                f"Объявление: {property_id if property_id else 'не указано'}\n\n"
                f"ID запроса: {request_id}"
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
        "💰 Выберите валюту для отображения цен:",
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
        "🤖 <b>AI функции</b>\n\n"
        "Выберите одну из доступных AI функций:",
        reply_markup=get_ai_features_keyboard(language)
    )

# ========== BACK TO MAIN MENU ==========

@dp.message(F.text.in_([
    TEXTS["ru"]["back_to_main"], TEXTS["uz"]["back_to_main"], TEXTS["en"]["back_to_main"]
]))
async def back_to_main_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    language = user.get('language', 'ru')
    
    await state.set_state(UserStates.main_menu)
    await show_main_menu(message, state, language)

# ========== ERROR HANDLER ==========

@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке update {update}: {exception}")
    
    # Можно отправить сообщение об ошибке пользователю
    if update.message:
        await update.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

# ========== START BOT ==========

async def main():
    """Основная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Создаем таблицы в базе данных
    await db.create_tables()
    
    # Запускаем бота
    await dp.start_polling(bot)

if _name_ == "_main_":
    asyncio.run(main())
