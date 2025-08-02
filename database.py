from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Patient, Status
from config import DATABASE_URL
from utils import generate_patient_id

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    """Создаёт все таблицы, если их ещё нет."""
    Base.metadata.create_all(engine)

def add_patient(full_name, timezone, medications, schedules):
    """Создание нового пациента. Возвращает patient_id."""
    session = Session()
    patient_id = generate_patient_id()
    patient = Patient(
        id=patient_id,
        full_name=full_name,
        timezone=timezone,
        telegram_id=None,
        medications=medications,
        schedules=schedules
    )
    session.add(patient)
    session.commit()
    session.close()
    return patient_id

def get_patient_by_id(patient_id):
    """Получить пациента по ID."""
    session = Session()
    patient = session.query(Patient).filter_by(id=patient_id).first()
    session.close()
    return patient

def update_patient_telegram_id(patient_id, telegram_id):
    """Привязать Telegram ID к пациенту."""
    session = Session()
    patient = session.query(Patient).filter_by(id=patient_id).first()
    if patient:
        patient.telegram_id = telegram_id
        session.commit()
    session.close()

def add_status(patient_id, medication, scheduled_time, status, comment=None):
    """Записать статус приёма лекарства (принял/пропустил и др.)."""
    session = Session()
    status_entry = Status(
        patient_id=patient_id,
        medication=medication,
        scheduled_time=scheduled_time,
        status=status,
        comment=comment
    )
    session.add(status_entry)
    session.commit()
    session.close()

def get_patients():
    """Получить всех пациентов."""
    session = Session()
    patients = session.query(Patient).all()
    session.close()
    return patients

def get_statuses(patient_id):
    """Получить все статусы по пациенту."""
    session = Session()
    statuses = session.query(Status).filter_by(patient_id=patient_id).all()
    session.close()
    return statuses

def update_patient_schedule(patient_id, schedules):
    """Обновить расписание пациента."""
    session = Session()
    patient = session.query(Patient).filter_by(id=patient_id).first()
    if patient:
        patient.schedules = schedules
        session.commit()
    session.close()

def update_patient_medications(patient_id, medications):
    """Обновить список лекарств пациента."""
    session = Session()
    patient = session.query(Patient).filter_by(id=patient_id).first()
    if patient:
        patient.medications = medications
        session.commit()
    session.close()

def update_patient_timezone(patient_id, timezone):
    # если используешь пакеты; иначе просто импортируй сверху Session, Patient
    session = Session()
    patient = session.query(Patient).filter_by(id=patient_id).first()
    if patient:
        patient.timezone = timezone
        session.commit()
    session.close()


def update_patient_schedules(patient_id, schedules):
     # если используешь пакеты; иначе просто импортируй сверху Session, Patient
    session = Session()
    patient = session.query(Patient).filter_by(id=patient_id).first()
    if patient:
        patient.schedules = schedules
        session.commit()
    session.close()
