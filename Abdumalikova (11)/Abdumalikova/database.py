import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import DATABASE_PATH

logger = logging.getLogger(__name__)


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Ma'lumotlar bazasini initsializatsiya qilish"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                api_id INTEGER NOT NULL,
                api_hash TEXT NOT NULL,
                phone TEXT NOT NULL,
                first_name TEXT,
                username TEXT,
                session_string TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                auto_reply_pm INTEGER DEFAULT 0,
                auto_reply_saved INTEGER DEFAULT 1,
                system_prompt TEXT,
                custom_gemini_key TEXT,
                ai_model TEXT DEFAULT 'gemini-1.5-flash',
                created_at TEXT,
                last_active_at TEXT
            )
        """)
        conn.commit()
    logger.info("Ma'lumotlar bazasi tayyorlandi.")


def save_user_session(
    telegram_id: int,
    api_id: int,
    api_hash: str,
    phone: str,
    session_string: str,
    first_name: str = "",
    username: str = ""
) -> bool:
    """Foydalanuvchi sessiyasini saqlash yoki yangilash"""
    now = datetime.now().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (
                telegram_id, api_id, api_hash, phone, first_name, username,
                session_string, is_active, created_at, last_active_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                api_id = excluded.api_id,
                api_hash = excluded.api_hash,
                phone = excluded.phone,
                first_name = excluded.first_name,
                username = excluded.username,
                session_string = excluded.session_string,
                is_active = 1,
                last_active_at = excluded.last_active_at
        """, (telegram_id, api_id, api_hash, phone, first_name, username, session_string, now, now))
        conn.commit()
        return True


def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """Foydalanuvchini ID bo'yicha olish"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def get_all_active_users() -> List[Dict[str, Any]]:
    """Barcha faol foydalanuvchilar sessiyalarini olish"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_active = 1")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def update_user_settings(telegram_id: int, **kwargs) -> bool:
    """Foydalanuvchi sozlamalarini yangilash"""
    allowed_keys = {
        "auto_reply_pm",
        "auto_reply_saved",
        "system_prompt",
        "custom_gemini_key",
        "ai_model",
        "is_active",
        "last_active_at",
    }
    updates = []
    values = []
    for k, v in kwargs.items():
        if k in allowed_keys:
            updates.append(f"{k} = ?")
            values.append(v)

    if not updates:
        return False

    values.append(telegram_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(values))
        conn.commit()
        return True


def set_user_active_status(telegram_id: int, is_active: bool) -> bool:
    """Foydalanuvchi faolligini yoqish/o'chirish"""
    return update_user_settings(telegram_id, is_active=1 if is_active else 0)


def update_user_session_string(telegram_id: int, new_session_string: str) -> bool:
    """Sessiya satrini bazada yangilash"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET session_string = ?, last_active_at = ? WHERE telegram_id = ?",
            (new_session_string, datetime.now().isoformat(), telegram_id)
        )
        conn.commit()
        return True


def delete_user_session(telegram_id: int) -> bool:
    """Foydalanuvchi sessiyasini o'chirish"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        conn.commit()
        return True


def reset_all_sessions() -> bool:
    """Barcha sessiyalarni butunlay tozalash"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("VACUUM")
        conn.commit()
        return True


# Fayl yuklanganda bazani tekshirish
init_db()
