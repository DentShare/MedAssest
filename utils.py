# utils.py

import uuid

def generate_patient_id():
    # Генерирует короткий уникальный идентификатор пациента (8 символов)
    return str(uuid.uuid4())[:8]
