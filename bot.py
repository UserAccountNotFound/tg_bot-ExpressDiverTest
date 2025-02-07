import os
import random
import sqlite3
import yaml
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Загружаем переменные окружения из файла .env
load_dotenv()

# Инициализация базы данных
def initialize_database():
    if not os.path.exists("users.db"):  # Проверяем наличие файла базы данных
        print("База данных не найдена. Создаю новую...")
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        # Создаем таблицу users, если она не существует
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      first_name TEXT NOT NULL,
                      last_name TEXT NOT NULL)''')
        conn.commit()
        conn.close()
        print("База данных успешно создана.")

# Загрузка вопросов из YAML файлов
def load_questions(course):
    with open(f'{course}.yaml', 'r') as file:
        questions = yaml.safe_load(file)
        random.shuffle(questions)  # Перемешиваем вопросы
        return questions

# Генерация PDF с результатами
def generate_pdf(user_data):
    pdf_filename = "result.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, height - 50, "Результаты теста")

    # Информация о пользователе
    c.setFont("Helvetica", 12)
    c.drawString(30, height - 80, f"Имя: {user_data['first_name']}")
    c.drawString(30, height - 100, f"Фамилия: {user_data['last_name']}")
    c.drawString(30, height - 120, f"Курс: {user_data['course']}")

    # Результаты
    c.drawString(30, height - 150, f"Правильных ответов: {user_data['score']} из {len(user_data['questions'])}")

    # Заключение
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(30, height - 180, "Спасибо за прохождение теста!")

    c.save()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Состояния для FSM (Finite State Machine)
class TestStates:
    NAME = "name"
    SURNAME = "surname"
    COURSE = "course"
    TEST = "test"

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Привет! Введите ваше имя:")
    await TestStates.NAME.set()

# Обработчик ввода имени
@dp.message_handler(state=TestStates.NAME)
async def get_name(message: types.Message, state):
    await state.update_data(first_name=message.text)
    await message.answer("Введите вашу фамилию:")
    await TestStates.SURNAME.set()

# Обработчик ввода фамилии
@dp.message_handler(state=TestStates.SURNAME)
async def get_surname(message: types.Message, state):
    await state.update_data(last_name=message.text)
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Open Water Diver"), KeyboardButton(text="Advanced Open Water Diver")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Выберите курс:", reply_markup=reply_keyboard)
    await TestStates.COURSE.set()

# Обработчик выбора курса
@dp.message_handler(state=TestStates.COURSE)
async def choose_course(message: types.Message, state):
    course = message.text
    questions = load_questions(course)
    await state.update_data(course=course, questions=questions, current_question=0, score=0)
    await ask_question(message, state)

# Задать вопрос
async def ask_question(message: types.Message, state):
    user_data = await state.get_data()
    question_data = user_data['questions'][user_data['current_question']]
    question = question_data['question']
    if question_data['type'] == 'numeric':
        await message.answer(question)
    else:
        options = question_data['options']
        random.shuffle(options)  # Перемешиваем варианты ответов (опционально)
        reply_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=option)] for option in options],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer(question, reply_markup=reply_keyboard)
    await TestStates.TEST.set()

# Проверка ответа
@dp.message_handler(state=TestStates.TEST)
async def check_answer(message: types.Message, state):
    user_data = await state.get_data()
    question_data = user_data['questions'][user_data['current_question']]
    correct_answer = str(question_data['answer'])
    user_answer = message.text

    if user_answer == correct_answer:
        await state.update_data(score=user_data['score'] + 1)

    await state.update_data(current_question=user_data['current_question'] + 1)
    user_data = await state.get_data()

    if user_data['current_question'] < len(user_data['questions']):
        await ask_question(message, state)
    else:
        await message.answer(f"Тест завершен! Ваш результат: {user_data['score']}/{len(user_data['questions'])}")
        await save_user(user_data)
        generate_pdf(user_data)  # Генерируем PDF с результатами
        with open("result.pdf", "rb") as document:
            await message.answer_document(document)
        await state.finish()

# Сохранение пользователя в базу данных
async def save_user(user_data):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (first_name, last_name) VALUES (?, ?)",
              (user_data['first_name'], user_data['last_name']))
    conn.commit()
    conn.close()

# Запуск бота
if __name__ == '__main__':
    initialize_database()  # Инициализация базы данных
    executor.start_polling(dp, skip_updates=True)
