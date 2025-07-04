import json
import os
from aiogram import Bot, Dispatcher, executor, types

# === Конфигурация ===
TOKEN = os.getenv("8018604636:AAEmP81mU4rYjhLel6_Q7jVYcpIfNUMcBHQ")
OWNER_ID = 7807571960  # Ты – владелец
DB_FILE = "users.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# === Инициализация базы ===
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

# === Главное меню ===
@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    user_id = str(msg.from_user.id)
    users = load_users()

    # Меню
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("📋 Смотреть анкеты")

    if user_id not in users:
        users[user_id] = {"step": "name"}
        save_users(users)
        await msg.answer("👋 Привет! Давай создадим твою анкету.\nКак тебя зовут?", reply_markup=keyboard)
    else:
        await msg.answer("Ты уже зарегистрирован! Отправь /browse или нажми на кнопку ниже.", reply_markup=keyboard)

# === Просмотр анкет ===
@dp.message_handler(commands=["browse"])
@dp.message_handler(lambda msg: msg.text == "📋 Смотреть анкеты")
async def browse_profiles(msg: types.Message):
    user_id = str(msg.from_user.id)
    users = load_users()

    for uid, data in users.items():
        if uid != user_id and data.get("step") == "done":
            keyboard = types.InlineKeyboardMarkup(row_width=2)
            keyboard.add(
                types.InlineKeyboardButton("❤️ Лайк", callback_data=f"like:{uid}"),
                types.InlineKeyboardButton("⏭ Пропустить", callback_data=f"skip:{uid}")
            )
            await msg.answer(
                f"🧑 Имя: {data['name']}\n📍 Город: {data['city']}\n🎯 Интересы: {data['interests']}",
                reply_markup=keyboard
            )
            return
    await msg.answer("Пока нет других анкет 😢")

# === Обработка кнопок ===
@dp.callback_query_handler(lambda c: c.data.startswith("like") or c.data.startswith("skip"))
async def handle_buttons(callback: types.CallbackQuery):
    action, target_id = callback.data.split(":")
    if action == "like":
        await callback.message.answer("❤️ Лайк отправлен!")
    else:
        await callback.message.answer("⏭ Пропущено.")
    await callback.answer()

# === Обработка анкеты ===
@dp.message_handler()
async def form_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    users = load_users()

    # Отправка владельцу всех сообщений
    if int(user_id) != OWNER_ID:
        await bot.send_message(OWNER_ID, f"📥 Сообщение от @{msg.from_user.username or 'без ника'} ({user_id}):\n{msg.text}")

    if user_id in users:
        step = users[user_id].get("step")

        if step == "name":
            users[user_id]["name"] = msg.text
            users[user_id]["step"] = "city"
            await msg.answer("🏙 Укажи свой город:")
        elif step == "city":
            users[user_id]["city"] = msg.text
            users[user_id]["step"] = "interests"
            await msg.answer("💬 Напиши свои интересы:")
        elif step == "interests":
            users[user_id]["interests"] = msg.text
            users[user_id]["step"] = "done"
            save_users(users)
            await msg.answer("✅ Анкета создана! Нажми '📋 Смотреть анкеты' или введи /browse")
    else:
        await msg.answer("Напиши /start чтобы создать анкету.")
        
