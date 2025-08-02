# models.py

from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(String, primary_key=True)
    full_name = Column(String)
    timezone = Column(String)
    telegram_id = Column(String, nullable=True)
    medications = Column(JSON)      # [{'name': 'Парацетамол'}, ...]
    schedules = Column(JSON)        # [{'name': 'Парацетамол', 'schedule': {...}}, ...]

class Status(Base):
    __tablename__ = 'statuses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String, ForeignKey('patients.id'))
    medication = Column(String)
    scheduled_time = Column(DateTime)
    status = Column(String)         # Принял/Пропустил/Побочные эффекты
    comment = Column(String, nullable=True)
