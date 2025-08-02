# patient_handlers.py

from aiogram import types, Dispatcher
from database import get_patient_by_id, update_patient_telegram_id
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import Dispatcher
from gsheets import log_to_google_sheets  # путь к твоей функции, если она в gsheets.py
from database import get_patient_by_id    # чтобы получить пациента по id

class RegisterStates(StatesGroup):
    wait_id = State()

async def start(message: types.Message):
    await message.answer("Введите ваш ID пациента (выдан администратором):")
    await RegisterStates.wait_id.set()

async def register_patient(message: types.Message, state: FSMContext):
    patient_id = message.text.strip()
    patient = get_patient_by_id(patient_id)
    if not patient:
        await message.answer("ID не найден. Обратитесь к вашему врачу или администратору.")
        return
    update_patient_telegram_id(patient_id, message.from_user.id)
    await message.answer(f"Регистрация завершена! Ваш профиль: {patient.full_name}, ваш часовой пояс: {patient.timezone}")
    await state.finish()

def register_patient_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands="start", state="*")
    dp.register_message_handler(register_patient, state=RegisterStates.wait_id)
    # callback для Принял/Отклонил
    dp.register_callback_query_handler(
        reminder_callback_handler,
        lambda call: call.data.startswith("accepted:") or call.data.startswith("declined:")
    )

async def reminder_callback_handler(call: types.CallbackQuery):
    action, patient_id, med_name = call.data.split(":")
    patient = get_patient_by_id(patient_id)
    if not patient:
        await call.answer("Пациент не найден.")
        return

    # Записать статус в Google Таблицу!
    log_to_google_sheets(patient, med_name, action)

    if action == "accepted":
        await call.answer("Отмечено: принято ✅")
        await call.message.edit_reply_markup(reply_markup=None)
    elif action == "declined":
        await call.answer("Отмечено: отклонено ❌")
        await call.message.edit_reply_markup(reply_markup=None)


def register_patient(dp: Dispatcher):
    dp.register_callback_query_handler(reminder_callback_handler, lambda call: call.data.startswith("accepted:") or call.data.startswith("declined:"))