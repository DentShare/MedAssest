import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Путь до твоего credentials.json
GS_CREDENTIALS = 'credentials.json'
SPREADSHEET_ID = '1OMWq2aIb0qo-X9tXKh6AHb22MfuEErr0ijN7zrGqDms'  # Только ID, без всего пути

scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file(GS_CREDENTIALS, scopes=scopes)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

def log_to_google_sheets(patient, med_name, status):
    now = datetime.now().strftime('%Y-%m-%d')
    tme = datetime.now().strftime('%H:%M')
    row = [
        now,  # Дата
        tme,  # Время
        getattr(patient, 'full_name', str(patient)),  # Имя пациента
        getattr(patient, 'id', '-'),  # ID пациента
        med_name,  # Лекарство
        status     # Статус
    ]
    sheet.append_row(row)
