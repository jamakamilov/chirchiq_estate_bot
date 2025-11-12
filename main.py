import logging
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import TELEGRAM_TOKEN, ADMIN_IDS
from database import Database
from locales import TEXTS
from states import PropertyStates, SearchStates, AdminStates, UserStates
from keyboards import (
    get_role_keyboard, get_main_menu_keyboard, get_property_type_keyboard,
    get_district_keyboard, get_currency_keyboard, get_ai_features_keyboard,
    get_admin_keyboard, get_language_keyboard, get_rating_keyboard,
    get_back_to_main_keyboard, get_yes_no_keyboard, get_phone_keyboard
)
from utils import format_price, send_notification, check_subscription

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN is not set. Set TELEGRAM_TOKEN environment variable.")
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Инициализация базы данных
db = Database()

# ========== START HANDLER ==========
@dp.message(F.text == "/start")
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


# ========== ROLE SELECTION ==========
async def show_role_selection(message: types.Message, language: str):
    """Показ выбора роли"""
    keyboard = get_role_keyboard(language)
    await message.answer(
        TEXTS[language]["welcome"] + "\n\n" + TEXTS[language]["choose_role"],
        reply_markup=keyboard
    )

async def show_main_menu(message: types.Message, state: FSMContext, language: str):
    """Показ главного меню"""
    user = await db.get_user(message.from_user.id)
    if user and user.get('role'):
        role = user.get('role')
        keyboard = get_main_menu_keyboard(language, role)
        await message.answer(
            TEXTS[language]["main_menu"],
            reply_markup=keyboard
        )
    else:
        await show_role_selection(message, language)

async def show_language_selection(message: types.Message):
    """Показ меню выбора языка"""
    keyboard = get_language_keyboard()
    await message.answer(
        "🌐 Выберите язык / Tilni tanlang / Choose language:",
        reply_markup=keyboard
    )

# ========== ERROR HANDLER ==========
@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    """Обработчик ошибок"""
    logger.exception(f"Error processing update {update}: {exception}")
    # Пытаемся определить язык пользователя и отправить локализованное сообщение
    language = "ru"
    try:
        if update and getattr(update, "message", None) and update.message.from_user:
            user = await db.get_user(update.message.from_user.id)
            if user:
                language = user.get("language", "ru")
    except Exception:
        language = "ru"
    if getattr(update, "message", None):
        await update.message.answer(TEXTS.get(language, TEXTS["ru"])["error_general"])

# ========== START BOT ==========
async def main():
    """Основная функция запуска бота"""
    logger.info("Starting bot...")
    
    # Создаем таблицы в базе данных
    await db.create_tables()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
