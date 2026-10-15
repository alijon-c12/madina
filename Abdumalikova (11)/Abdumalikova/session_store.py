import os
import sqlite3
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import BASE_DIR, DATABASE_PATH
import database

logger = logging.getLogger(__name__)

# Sessiyalar zaxirasi saqlanadigan jild
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


class SessionStore:
    """Telegram sessiyalarini xavfsiz boshqarish va yangilash tizimi"""

    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        self._ensure_storage()

    def _ensure_storage(self):
        """Sessiyalar jildi va bazani tekshirish"""
        self.sessions_dir.mkdir(exist_ok=True)
        database.init_db()

    def save(
        self,
        telegram_id: int,
        api_id: int,
        api_hash: str,
        phone: str,
        session_string: str,
        first_name: str = "",
        username: str = ""
    ) -> bool:
        """Yangi sessiyani bazaga va faylga saqlash"""
        try:
            # 1. Ma'lumotlar bazasiga saqlash
            success = database.save_user_session(
                telegram_id=telegram_id,
                api_id=api_id,
                api_hash=api_hash,
                phone=phone,
                session_string=session_string,
                first_name=first_name,
                username=username
            )

            # 2. Fayl shaklida zaxira nusxasini saqlash
            backup_file = self.sessions_dir / f"{telegram_id}.session_string"
            backup_file.write_text(session_string, encoding="utf-8")

            logger.info(f"✅ Sessiya saqlandi va zaxiralandi: {telegram_id}")
            return success
        except Exception as e:
            logger.error(f"Sessiyani saqlashda xatolik: {e}")
            return False

    def get(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Foydalanuvchi sessiya ma'lumotlarini olish"""
        user = database.get_user(telegram_id)
        if user:
            return user

        # Agar bazada bo'lmasa, zaxira fayldan tekshirish
        backup_file = self.sessions_dir / f"{telegram_id}.session_string"
        if backup_file.exists():
            session_str = backup_file.read_text(encoding="utf-8").strip()
            return {"telegram_id": telegram_id, "session_string": session_str}

        return None

    def update_session_string(self, telegram_id: int, new_session_string: str) -> bool:
        """Mavjud sessiya kalitini yangilash"""
        try:
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET session_string = ? WHERE telegram_id = ?",
                    (new_session_string, telegram_id)
                )
                conn.commit()

            backup_file = self.sessions_dir / f"{telegram_id}.session_string"
            backup_file.write_text(new_session_string, encoding="utf-8")
            logger.info(f"🔄 Sessiya satri yangilandi: {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Sessiya yangilashda xato: {e}")
            return False

    def remove(self, telegram_id: int) -> bool:
        """Sessiyani butunlay o'chirish"""
        try:
            database.delete_user_session(telegram_id)
            backup_file = self.sessions_dir / f"{telegram_id}.session_string"
            if backup_file.exists():
                backup_file.unlink()
            logger.info(f"🗑 Sessiya o'chirildi: {telegram_id}")
            return True
        except Exception as e:
            logger.error(f"Sessiyani o'chirishda xatolik: {e}")
            return False

    def refresh_store(self) -> Dict[str, Any]:
        """
        Barcha sessiyalar omborini yangilash, optimallashtirish va tozalash
        """
        try:
            # 1. Bazani tozalash va ixchamlashtirish (VACUUM)
            with database.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                conn.commit()

            # 2. Bazadagi barcha faol sessiyalarni zaxira bilan sinxronlashtirish
            users = database.get_all_active_users()
            synced_count = 0
            for u in users:
                tid = u["telegram_id"]
                s_str = u.get("session_string")
                if s_str:
                    f_path = self.sessions_dir / f"{tid}.session_string"
                    f_path.write_text(s_str, encoding="utf-8")
                    synced_count += 1

            # 3. Yetim (orphan) zaxira fayllarni tozalash
            active_ids = {u["telegram_id"] for u in users}
            deleted_files = 0
            for p in self.sessions_dir.glob("*.session_string"):
                try:
                    file_id = int(p.stem)
                    if file_id not in active_ids:
                        p.unlink()
                        deleted_files += 1
                except ValueError:
                    pass

            result = {
                "success": True,
                "active_sessions": len(users),
                "synced_files": synced_count,
                "cleaned_files": deleted_files,
                "database_size": os.path.getsize(DATABASE_PATH) if os.path.exists(DATABASE_PATH) else 0
            }
            logger.info(f"✨ Session store muvaffaqiyatli yangilandi: {result}")
            return result
        except Exception as e:
            logger.error(f"Session store ni yangilashda xatolik: {e}")
            return {"success": False, "error": str(e)}

    async def verify_session_active(self, telegram_id: int) -> bool:
        """Sessiyaning yaroqli ekanligini Telegram orqali tekshirish"""
        user = self.get(telegram_id)
        if not user or not user.get("session_string"):
            return False

        try:
            client = TelegramClient(
                StringSession(user["session_string"]),
                user["api_id"],
                user["api_hash"]
            )
            await client.connect()
            is_auth = await client.is_user_authorized()
            if is_auth:
                # Yangilangan sessiya satrini saqlab qo'yish
                new_str = client.session.save()
                if new_str != user["session_string"]:
                    self.update_session_string(telegram_id, new_str)
            await client.disconnect()
            return is_auth
        except Exception as e:
            logger.warning(f"Sessiyani tekshirishda xatolik ({telegram_id}): {e}")
            return False


# Global session store instansiyasi
session_store = SessionStore()
