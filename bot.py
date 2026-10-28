import asyncio
import logging
import random
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "9008195461:AAHFS0rRl-cwzNk5rQo9n0p-wbqsRManwMA"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            nickname TEXT,
            age INTEGER,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_user(user_id, username, nickname, age):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, username, nickname, age)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, nickname, age))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT nickname, age, registered_at FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

init_db()

class Registration(StatesGroup):
    nickname = State()
    age = State()

def get_main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Кинуть кубик", callback_data="dice"),
                InlineKeyboardButton(text="🔮 Пожелание дня", callback_data="prediction")
            ],
            [
                InlineKeyboardButton(text="🔢 Случайное число", callback_data="random_number"),
                InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")
            ]
        ]
    )

WISHES = [
    "Сегодня идеальный день, чтобы закрыть все долги по учёбе и коду!",
    "Твой код скомпилируется с первого раза без предупреждений.",
    "Отличный момент выпить кофе и наконец-то задеплоить проект.",
    "Звёзды говорят: стажировка в Innowise ближе, чем кажется 😉",
    "Не бойся рефакторить старое — сегодня всё пройдёт гладко."
]

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        nickname, _, _ = user
        await message.answer(
            f"С возвращением, **{nickname}**! ✨\nВыбирай действие в меню ниже:",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
    else:
        await state.set_state(Registration.nickname)
        await message.answer(
            "👋 Привет! Добро пожаловать в систему.\n"
            "Давай пройдём быструю регистрацию. Введи свой **никнейм**:"
        )

@dp.message(Registration.nickname)
async def process_nickname(message: types.Message, state: FSMContext):
    nickname = message.text.strip()
    if len(nickname) < 2 or len(nickname) > 30:
        await message.answer("⚠️ Длина никнейма должна быть от 2 до 30 символов. Попробуй ещё раз:")
        return

    await state.update_data(nickname=nickname)
    await state.set_state(Registration.age)
    await message.answer(f"Отлично, {nickname}! А сколько тебе лет?")

@dp.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введи возраст числом (например, 18):")
        return

    age = int(message.text)
    if age < 12 or age > 100:
        await message.answer("⚠️ Укажи корректный возраст (от 12 до 100):")
        return

    data = await state.get_data()
    nickname = data["nickname"]

    save_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "Unknown",
        nickname=nickname,
        age=age
    )
    await state.clear()

    await message.answer(
        f"🎉 Регистрация успешно завершена!\n"
        f"Добро пожаловать в клуб, {nickname}.\n\n"
        f"Теперь тебе доступен весь функционал:",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

@dp.callback_query(F.data == "dice")
async def handle_dice(callback: types.CallbackQuery):
    await callback.message.answer("🎲 Бросаем кубик...")
    await callback.message.answer_dice(emoji="🎲")
    await callback.answer()

@dp.callback_query(F.data == "prediction")
async def handle_prediction(callback: types.CallbackQuery):
    prediction = random.choice(WISHES)
    await callback.message.answer(f"✨ **Пожелание на сегодня:**\n{prediction}", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "random_number")
async def handle_random(callback: types.CallbackQuery):
    val = random.randint(1, 100)
    await callback.message.answer(f"🔢 Твоё число удачи: **{val}** (из 100)", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def handle_profile(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id)
    if user:
        nickname, age, reg_date = user
        text = (
            "📋 **Твой профиль:**\n\n"
            f"👤 Никнейм: `{nickname}`\n"
            f"🎂 Возраст: `{age}`\n"
            f"📅 Дата регистрации: `{reg_date}`"
        )
    else:
        text = "Профиль не найден. Пройди регистрацию через /start."

    await callback.message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())
    await callback.answer()

async def main():
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())