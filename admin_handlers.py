from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_PASSWORD
from database import add_patient, get_patient_by_id, update_patient_timezone, update_patient_medications, update_patient_schedules
import json
import pytz

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

ADMIN_SESSIONS = set()

class AdminStates(StatesGroup):
    wait_password = State()

class NewPatientStates(StatesGroup):
    full_name = State()
    timezone = State()
    medications = State()
    schedules = State()

class EditPatientStates(StatesGroup):
    waiting_for_id = State()
    choose_action = State()
    edit_timezone = State()
    edit_medications = State()
    edit_schedules = State()


# --- ADMIN AUTH ---
async def admin_start(message: types.Message):
    await message.answer("Введите пароль администратора:")
    await AdminStates.wait_password.set()

async def admin_auth(message: types.Message, state: FSMContext):
    if message.text.strip() == ADMIN_PASSWORD:
        ADMIN_SESSIONS.add(message.from_user.id)
        await message.answer(
            "Вход выполнен. Доступны команды:\n"
            "/new_patient — создать нового пациента\n"
            "/edit_patient — редактировать расписание/лекарства"
        )
        await state.finish()
    else:
        await message.answer("Неверный пароль.")

# --- NEW PATIENT FSM ---
async def new_patient(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_SESSIONS:
        await message.answer("Нет доступа. Для доступа введите /admin и пароль.")
        return
    await message.answer("ФИО пациента?")
    await NewPatientStates.full_name.set()

async def new_patient_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    # Клавиатура с кнопкой "Пропустить"
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("Пропустить"))
    await message.answer(
        "Часовой пояс пациента? (например, Europe/Moscow, Asia/Tashkent)\n"
        "Если оставить поле пустым или нажать 'Пропустить' — будет Asia/Tashkent.",
        reply_markup=kb
    )
    await NewPatientStates.timezone.set()

async def new_patient_timezone(message: types.Message, state: FSMContext):
    tz_input = message.text.strip()
    if not tz_input or tz_input.lower() == "пропустить":
        tz_input = "Asia/Tashkent"
    import pytz
    if tz_input not in pytz.all_timezones:
        await message.answer(
            "Ошибка! Некорректный часовой пояс.\n"
            "Пример: Europe/Moscow, Asia/Tashkent"
        )
        return
    await state.update_data(timezone=tz_input)
    await message.answer("Список лекарств? (через запятую)", reply_markup=types.ReplyKeyboardRemove())
    await NewPatientStates.medications.set()


async def new_patient_medications(message: types.Message, state: FSMContext):
    meds = [m.strip() for m in message.text.split(",")]
    await state.update_data(medications=[{"name": m} for m in meds])
    await message.answer(
        "Введите расписание для каждого лекарства в формате JSON:\n"
        '[{"name": "Парацетамол", "schedule": {"type": "daily", "times": ["08:00", "20:00"]}}]'
    )
    await NewPatientStates.schedules.set()

async def new_patient_schedules(message: types.Message, state: FSMContext):
    try:
        schedules = json.loads(message.text)
    except Exception:
        await message.answer("Ошибка! Повторите ввод расписания (ожидается JSON список).")
        return
    data = await state.get_data()
    timezone = data.get("timezone", "Asia/Tashkent")
    patient_id = add_patient(
        data["full_name"],
        timezone,
        data["medications"],
        schedules
    )
    await message.answer(f"Пациент создан. ID для передачи: <code>{patient_id}</code>")
    await state.finish()

# --- EDIT PATIENT FSM ---
async def edit_patient(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_SESSIONS:
        await message.answer("Нет доступа. Введите /admin и пароль.")
        return
    await message.answer("Введите ID пациента, которого хотите изменить:")
    await EditPatientStates.waiting_for_id.set()

async def edit_patient_get_id(message: types.Message, state: FSMContext):
    patient_id = message.text.strip()
    patient = get_patient_by_id(patient_id)
    if not patient:
        await message.answer("Пациент с таким ID не найден. Введите ID ещё раз:")
        return
    await state.update_data(patient_id=patient_id)
    await message.answer(
        "Что вы хотите изменить?\n"
        "1. Часовой пояс\n"
        "2. Лекарства\n"
        "3. Расписание\n"
        "Введите номер опции:"
    )
    await EditPatientStates.choose_action.set()

async def edit_patient_choose_action(message: types.Message, state: FSMContext):
    option = message.text.strip()
    if option == "1":
        await message.answer("Введите новый часовой пояс пациента (например, Europe/Moscow, Asia/Tashkent):")
        await EditPatientStates.edit_timezone.set()
    elif option == "2":
        await message.answer("Введите новый список лекарств (через запятую):")
        await EditPatientStates.edit_medications.set()
    elif option == "3":
        await message.answer("Введите новое расписание в формате JSON:")
        await EditPatientStates.edit_schedules.set()
    else:
        await message.answer("Некорректный выбор. Введите номер опции (1/2/3):")

async def edit_patient_timezone(message: types.Message, state: FSMContext):
    tz = message.text.strip()
    if tz not in pytz.all_timezones:
        await message.answer("Ошибка! Некорректный часовой пояс. Пример: Europe/Moscow, Asia/Tashkent")
        return
    data = await state.get_data()
    update_patient_timezone(data["patient_id"], tz)
    await message.answer("Часовой пояс обновлён.")
    await state.finish()

async def edit_patient_medications(message: types.Message, state: FSMContext):
    meds = [m.strip() for m in message.text.split(",")]
    meds_struct = [{"name": m} for m in meds]
    data = await state.get_data()
    update_patient_medications(data["patient_id"], meds_struct)
    await message.answer("Список лекарств обновлён.")
    await state.finish()

async def edit_patient_schedules(message: types.Message, state: FSMContext):
    try:
        schedules = json.loads(message.text)
    except Exception:
        await message.answer("Ошибка! Повторите ввод расписания (ожидается JSON список).")
        return
    data = await state.get_data()
    update_patient_schedules(data["patient_id"], schedules)
    await message.answer("Расписание обновлено.")
    await state.finish()

# --- REGISTRATION OF HANDLERS ---
def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands="admin", state="*")
    dp.register_message_handler(admin_auth, state=AdminStates.wait_password)
    dp.register_message_handler(new_patient, commands="new_patient", state="*")
    dp.register_message_handler(new_patient_full_name, state=NewPatientStates.full_name)
    dp.register_message_handler(new_patient_timezone, state=NewPatientStates.timezone)
    dp.register_message_handler(new_patient_medications, state=NewPatientStates.medications)
    dp.register_message_handler(new_patient_schedules, state=NewPatientStates.schedules)
    dp.register_message_handler(edit_patient, commands="edit_patient", state="*")
    dp.register_message_handler(edit_patient_get_id, state=EditPatientStates.waiting_for_id)
    dp.register_message_handler(edit_patient_choose_action, state=EditPatientStates.choose_action)
    dp.register_message_handler(edit_patient_timezone, state=EditPatientStates.edit_timezone)
    dp.register_message_handler(edit_patient_medications, state=EditPatientStates.edit_medications)
    dp.register_message_handler(edit_patient_schedules, state=EditPatientStates.edit_schedules)
    # ... другие хендлеры по проекту

