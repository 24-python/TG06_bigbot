import asyncio
import os  # Для работы с переменными окружения
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

import sqlite3
import aiohttp
import logging
import requests
import random
from dotenv import load_dotenv
load_dotenv()

# Получаем токен из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Токен бота не найден! Установите переменную окружения BOT_TOKEN.")

# Создаём бота и диспетчер
bot = Bot(token=TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

# Кнопки меню
button_registr = KeyboardButton(text="Регистрация в телеграм-боте")
button_exchange_rates = KeyboardButton(text="Курс валют")
button_tips = KeyboardButton(text="Советы по экономии")
button_finances = KeyboardButton(text="Личные финансы")

keyboards = ReplyKeyboardMarkup(keyboard=[
    [button_registr, button_exchange_rates],
    [button_tips, button_finances]
    ], resize_keyboard=True)

# Подключение к базе данных
conn = sqlite3.connect('user.db')
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    telegram_id INTEGER UNIQUE,
    name TEXT,
    category1 TEXT,
    category2 TEXT,
    category3 TEXT,
    expenses1 REAL,
    expenses2 REAL,
    expenses3 REAL
    )
''')
conn.commit()

# Машина состояний для финансовых категорий
class FinancesForm(StatesGroup):
    category1 = State()
    expenses1 = State()
    category2 = State()
    expenses2 = State()
    category3 = State()
    expenses3 = State()

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет! Я ваш личный финансовый помощник! Выберите одну из опций в меню:', reply_markup=keyboards)

# Обработчик регистрации
@dp.message(F.text == 'Регистрация в телеграм-боте')
async def registration(message: Message):
    telegram_id = message.from_user.id
    name = message.from_user.full_name
    cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
    user = cursor.fetchone()
    if user:
        await message.answer('Вы уже зарегистрированы!')
    else:
        cursor.execute('''INSERT INTO users (telegram_id, name) VALUES (?, ?)''', (telegram_id, name))
        conn.commit()
        await message.answer('Вы успешно зарегистрированы!')

# Обработчик "Курс валют"
@dp.message(F.text == 'Курс валют')
async def exchange_rates(message: Message):
    url = 'https://v6.exchangerate-api.com/v6/93f384604322ccdaceacb874/latest/USD'
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            await message.answer('Произошла ошибка при получении курса валют')
            return
        usd_to_rub = data['conversion_rates']['RUB']
        eur_to_usd = data['conversion_rates']['EUR']
        eur_to_rub = eur_to_usd * usd_to_rub
        await message.answer(f'Курс доллара к рублю: {usd_to_rub:.2f}\nКурс евро к рублю: {eur_to_rub:.2f}')
    except:
        await message.answer('Произошла ошибка при получении курса валют')

# Обработчик "Советы по экономии"
@dp.message(F.text == 'Советы по экономии')
async def send_tips(message: Message):
    tips = [
        'Планируйте бюджет 📝\nЗаписывайте доходы и расходы, чтобы понимать, куда уходят деньги.',
        'Следите за акциями и скидками 🛒\nПокупайте товары по акциям, используйте кэшбэк.',
        'Готовьте дома 🍳\nДомашняя еда дешевле и полезнее, чем кафе и рестораны.',
        'Откладывайте часть дохода 💰\nСтарайтесь откладывать хотя бы 10% от зарплаты.',
        'Покупайте б/у вещи 👕📱\nМногие вещи можно купить в хорошем состоянии с рук.',
    ]
    tip = random.choice(tips)
    await message.answer(tip)

# Обработчик "Личные финансы"
@dp.message(F.text == 'Личные финансы')
async def send_finances(message: Message, state: FSMContext):
    await state.set_state(FinancesForm.category1)
    await message.reply('Введите первую категорию расходов:')

@dp.message(FinancesForm.category1)
async def send_finances(message: Message, state: FSMContext):
    await state.update_data(category1=message.text)
    await state.set_state(FinancesForm.expenses1)
    await message.reply('Введите сумму расходов на эту категорию:')

@dp.message(FinancesForm.expenses1)
async def send_finances(message: Message, state: FSMContext):
    await state.update_data(expenses1=float(message.text))
    await state.set_state(FinancesForm.category2)
    await message.reply('Введите вторую категорию расходов:')

@dp.message(FinancesForm.category2)
async def send_finances(message: Message, state: FSMContext):
    await state.update_data(category2=message.text)
    await state.set_state(FinancesForm.expenses2)
    await message.reply('Введите сумму расходов на эту категорию:')

@dp.message(FinancesForm.expenses2)
async def send_finances(message: Message, state: FSMContext):
    await state.update_data(expenses2=float(message.text))
    await state.set_state(FinancesForm.category3)
    await message.reply('Введите третью категорию расходов:')

@dp.message(FinancesForm.category3)
async def send_finances(message: Message, state: FSMContext):
    await state.update_data(category3=message.text)
    await state.set_state(FinancesForm.expenses3)
    await message.reply('Введите сумму расходов на эту категорию:')

@dp.message(FinancesForm.expenses3)
async def send_finances(message: Message, state: FSMContext):
    await state.update_data(expenses3=float(message.text))
    data = await state.get_data()
    telegram_id = message.from_user.id
    cursor.execute('''UPDATE users SET category1 = ?, expenses1 = ?, category2 = ?, expenses2 = ?, category3 = ?, expenses3 = ? WHERE telegram_id = ?''',
                   (data['category1'], data['expenses1'], data['category2'], data['expenses2'], data['category3'], float(message.text), telegram_id))
    conn.commit()
    await state.clear()
    await message.answer('Категории и расходы успешно добавлены в базу данных!')

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
