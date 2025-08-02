# bot.py

import asyncio
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import API_TOKEN
from database import init_db
from admin_handlers import register_admin
from patient_handlers import register_patient_handlers
from scheduler import schedule_reminders, scheduler

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


async def on_startup(dispatcher):
    # Здесь всё, что требует уже работающего event loop
    schedule_reminders()
    scheduler.start()
    print("Scheduler started!")

if __name__ == "__main__":
    # 1. Инициализация базы данных
    init_db()

    # 2. Инициализация бота и диспетчера
    bot = Bot(token=API_TOKEN, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())

    # 3. Регистрируем хендлеры
    register_admin(dp)
    register_patient_handlers(dp)

    # 4. Запуск polling и планировщика через on_startup
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
