import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_patients
from datetime import datetime, timedelta
from aiogram import Bot
from config import API_TOKEN

bot = Bot(token=API_TOKEN)
scheduler = AsyncIOScheduler()

# --- Функция отправки напоминания ---
async def send_reminder(patient_id, med_name, time_or_val):
    from database import get_patient_by_id
    patient = get_patient_by_id(patient_id)
    if not patient:
        return
    text = f"Напоминание!\nПримите лекарство: <b>{med_name}</b> в {time_or_val}"
    # Здесь можешь добавить клавиатуру "Принял/Отклонил"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Принял", callback_data=f"accepted:{patient_id}:{med_name}"),
        InlineKeyboardButton("Отклонил", callback_data=f"declined:{patient_id}:{med_name}")
    )
    await bot.send_message(
        chat_id=patient.telegram_id,
        text=text,
        reply_markup=kb,
        parse_mode='HTML'
    )

# --- Парсер расписаний (пример) ---
def parse_schedules(schedules):
    parsed = []
    for med in schedules or []:
        name = med.get("name")
        sch = med.get("schedule")
        if not sch:
            continue
        t = sch.get("times", [])
        if sch.get("type") == "daily":
            for tm in t:
                parsed.append((name, tm, None, "daily"))
        elif sch.get("type") == "weekly":
            for day in sch.get("days", []):
                for tm in t:
                    parsed.append((name, tm, day, "weekly"))
        elif sch.get("type") == "interval":
            interval = sch.get("interval_minutes", 0)
            start = sch.get("start", "now")
            parsed.append((name, interval, start, "interval"))
        elif sch.get("type") == "course":
            for tm in t:
                parsed.append((name, tm, (sch.get("start_date"), sch.get("end_date")), "course"))
        elif sch.get("type") == "once":
            for dt in sch.get("datetimes", []):
                parsed.append((name, dt, None, "once"))
    return parsed

# --- Основная функция расписания напоминаний ---
def schedule_reminders():
    for patient in get_patients():
        tz = pytz.timezone(patient.timezone)
        for med, val, extra, typ in parse_schedules(patient.schedules):
            if typ == "daily":
                hour, minute = map(int, val.split(":"))
                job_id = f"{patient.id}-{med}-daily-{hour}{minute}"
                scheduler.add_job(
                    send_reminder,
                    "cron",
                    args=[patient.id, med, val],
                    hour=hour, minute=minute,
                    timezone=tz,
                    id=job_id,
                    replace_existing=True
                )
            elif typ == "weekly":
                hour, minute = map(int, val.split(":"))
                weekday = extra  # например, "mon", "thu"
                job_id = f"{patient.id}-{med}-weekly-{weekday}-{hour}{minute}"
                scheduler.add_job(
                    send_reminder,
                    "cron",
                    args=[patient.id, med, val],
                    hour=hour, minute=minute, day_of_week=weekday,
                    timezone=tz,
                    id=job_id,
                    replace_existing=True
                )
            elif typ == "interval":
                interval = val  # минуты
                start = extra
                if start == "now":
                    start_date = datetime.now(tz)
                else:
                    today = datetime.now(tz).date()
                    hour, minute = map(int, start.split(":"))
                    start_date = tz.localize(datetime.combine(today, datetime.min.time())) \
                        .replace(hour=hour, minute=minute)
                    if start_date < datetime.now(tz):
                        start_date += timedelta(days=1)
                job_id = f"{patient.id}-{med}-interval"
                scheduler.add_job(
                    send_reminder,
                    "interval",
                    args=[patient.id, med, interval],
                    minutes=interval,
                    start_date=start_date,
                    timezone=tz,
                    id=job_id,
                    replace_existing=True
                )
            elif typ == "course":
                t = val
                start_date, end_date = extra
                d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
                d_end = datetime.strptime(end_date, "%Y-%m-%d").date()
                current = d_start
                while current <= d_end:
                    hour, minute = map(int, t.split(":"))
                    run_dt = tz.localize(datetime.combine(current, datetime.min.time())) \
                        .replace(hour=hour, minute=minute)
                    job_id = f"{patient.id}-{med}-course-{current}"
                    scheduler.add_job(
                        send_reminder,
                        "date",
                        args=[patient.id, med, t],
                        run_date=run_dt,
                        timezone=tz,
                        id=job_id,
                        replace_existing=True
                    )
                    current += timedelta(days=1)
            elif typ == "once":
                run_dt = tz.localize(datetime.strptime(val, "%Y-%m-%dT%H:%M"))
                job_id = f"{patient.id}-{med}-once-{val}"
                scheduler.add_job(
                    send_reminder,
                    "date",
                    args=[patient.id, med, val],
                    run_date=run_dt,
                    timezone=tz,
                    id=job_id,
                    replace_existing=True
                )

# --- Запуск планировщика ---
def run_scheduler():
    schedule_reminders()
    scheduler.start()
    print("Scheduler started!")

# Для aiogram on_startup:
async def on_startup(dp):
    run_scheduler()
