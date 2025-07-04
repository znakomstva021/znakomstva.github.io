import os
import json
import logging
import asyncio
import signal
from aiogram import Bot, Dispatcher, types
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

# Конфигурация
TOKEN = os.getenv("8018604636:AAEmP81mU4rYjhLel6_Q7jVYcpIfNUMcBHQ")  # Токен из Secrets GitHub
ADMIN_ID = int(os.getenv("7807571960", 0))  # ID админа из Secrets

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# База данных
DB_FILE = "users.json"

def init_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)

def load_users():
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=2)

init_db()

# Клавиатуры
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Создать анкету")],
        [KeyboardButton(text="🔍 Смотреть анкеты")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

like_skip_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Лайк", callback_data="like"),
            InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")
        ]
    ]
)

# Обработчики
@dp.message(F.text == "/start")
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()
    
    if user_id not in users:
        users[user_id] = {"step": "name"}
        save_users(users)
        await message.answer(
            "👋 Привет! Как тебя зовут?",
            reply_markup=main_kb
        )
    else:
        await message.answer(
            "Ты уже зарегистрирован!",
            reply_markup=main_kb
        )

@dp.message(F.text == "/browse")
async def browse(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)
    
    for uid, data in users.items():
        if uid != user_id and data.get("step") == "done":
            await message.answer(
                f"👤 {data['name']}\n"
                f"🏙 {data['city']}\n"
                f"🎯 {data['interests']}",
                reply_markup=like_skip_kb
            )
            return
    
    await message.answer("Нет анкет для просмотра")

@dp.message(F.text == "➕ Создать анкету")
async def create_profile(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()
    users[user_id] = {"step": "name"}
    save_users(users)
    await message.answer("Как тебя зовут?")

@dp.callback_query(F.data == "like")
async def like(callback: types.CallbackQuery):
    await callback.answer("Лайк поставлен!")
    await browse(callback.message)

@dp.callback_query(F.data == "skip")
async def skip(callback: types.CallbackQuery):
    await callback.answer("Пропущено")
    await browse(callback.message)

@dp.message()
async def form(message: types.Message):
    user_id = str(message.from_user.id)
    users = load_users()
    
    if user_id not in users:
        return
    
    step = users[user_id].get("step")
    
    if step == "name":
        users[user_id]["name"] = message.text
        users[user_id]["step"] = "city"
        await message.answer("Из какого ты города?")
    
    elif step == "city":
        users[user_id]["city"] = message.text
        users[user_id]["step"] = "interests"
        await message.answer("Расскажи о своих интересах")
    
    elif step == "interests":
        users[user_id]["interests"] = message.text
        users[user_id]["step"] = "done"
        await message.answer(
            "Анкета готова!",
            reply_markup=main_kb
        )
    
    save_users(users)

async def shutdown(signal, loop):
    """Аккуратный shutdown бота"""
    logger.info("Получен сигнал завершения...")
    await bot.close()
    loop.stop()

async def main():
    # Настройка обработчиков сигналов
    loop = asyncio.get_running_loop()
    for s in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(
            s,
            lambda s=s: asyncio.create_task(shutdown(s, loop))
        )
    
    try:
        # Автоперезапуск каждые 2 часа
        restart_task = asyncio.create_task(asyncio.sleep(7200))  # 2 часа
        polling_task = asyncio.create_task(dp.start_polling(bot))
        
        await asyncio.wait(
            [restart_task, polling_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        if restart_task.done():
            logger.info("Время работы истекло, перезапуск...")
            await bot.close()
            return  # GitHub Actions перезапустит бота
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    logger.info("Бот запущен!")
    asyncio.run(main())
