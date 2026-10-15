import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# .env faylini yuklash
load_dotenv(BASE_DIR / ".env")

# Boshqaruvchi Bot tokeni (Telegram @BotFather dan olinadi)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Boshqaruvchi bot uchun ixtiyoriy fallback API_ID va API_HASH
# (Agar mavjud bo'lsa, foydalanuvchilar o'z API_ID sini kiritmasa ham ishlatishi mumkin)
DEFAULT_API_ID = os.getenv("API_ID", "").strip()
DEFAULT_API_HASH = os.getenv("API_HASH", "").strip()

# Google Gemini API Kaliti (https://aistudio.google.com/ bepul olish mumkin)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Default AI Modeli
DEFAULT_AI_MODEL = os.getenv("AI_MODEL", "gemini-1.5-flash").strip()

# SQLite Ma'lumotlar bazasi fayli
DATABASE_PATH = BASE_DIR / "data.db"

# Standart AI Tizim Prompti
DEFAULT_SYSTEM_PROMPT = (
    "Siz foydalanuvchining shaxsiy Telegram sun'iy intellekt yordamchisisiz. "
    "Foydalanuvchiga va uning suhbatdoshlariga doimo xushmuomala, samimiy, aniq, "
    "lo'nda va foydali javoblar bering. O'zbek tilida tabiiy va ravon yozing. "
    "Agar foydalanuvchi boshqa tilda murojaat qilsa, o'sha tilda javob bering. "
    "Matnlarni chiroyli formatda (markdown, qisqa abzaslar, kerak bo'lsa ro'yxat) taqdim eting."
)

# Buyruq prefikslari
COMMAND_PREFIXES = (".ai", "!ai", "/ai")
