import json
import os
from aiogram import Bot, Dispatcher, executor, types

TOKEN = os.getenv("8018604636:AAEmP81mU4rYjhLel6_Q7jVYcpIfNUMcBHQ")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DB_FILE = "users.json"

if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({}, f)

def load_users():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(DB_FILE, "w") as f:
        json.dump(users, f, indent=4)

@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    user_id = str(msg.from_user.id)
    users = load_users()

    if user_id not in users:
        users[user_id] = {"step": "name"}
        save_users(users)
        await msg.answer("👋 Привет! Давай создадим твою анкету.\nКак тебя зовут?")
    else:
        await msg.answer("Ты уже зарегистрирован! Отправь /browse чтобы смотреть анкеты.")

@dp.message_handler(commands=["browse"])
async def browse_profiles(msg: types.Message):
    user_id = str(msg.from_user.id)
    users = load_users()

    for uid, data in users.items():
        if uid != user_id and "name" in data:
            await msg.answer(
                f"🧑 Имя: {data['name']}\n📍 Город: {data['city']}\n🎯 Интересы: {data['interests']}\n"
                f"👉 [❤️ Лайк]   [⏭ Пропустить]"
            )
            return
    await msg.answer("Пока нет других анкет 😢")

@dp.message_handler()
async def form_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    users = load_users()

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
            await msg.answer("✅ Анкета создана! Теперь ты можешь смотреть анкеты /browse")
            save_users(users)
    else:
        await msg.answer("Напиши /start чтобы создать анкету.")

