import asyncio
import logging
from typing import Dict, Optional
import database
from userbot_client import UserbotSession

logger = logging.getLogger(__name__)


class UserbotManager:
    def __init__(self):
        self.sessions: Dict[int, UserbotSession] = {}

    def is_running(self, telegram_id: int) -> bool:
        session = self.sessions.get(telegram_id)
        return bool(session and session.is_running and session.client and session.client.is_connected())

    async def start_userbot(self, telegram_id: int) -> bool:
        """Foydalanuvchi userbotini ishga tushirish"""
        user_data = database.get_user(telegram_id)
        if not user_data:
            logger.error(f"Foydalanuvchi topilmadi: {telegram_id}")
            return False

        # Agar avvaldan ishlab turgan bo'lsa to'xtatamiz
        if telegram_id in self.sessions:
            await self.stop_userbot(telegram_id)

        session = UserbotSession(user_data)
        success = await session.start()
        if success:
            self.sessions[telegram_id] = session
            database.set_user_active_status(telegram_id, True)
            return True
        else:
            return False

    async def stop_userbot(self, telegram_id: int) -> bool:
        """Foydalanuvchi userbotini to'xtatish"""
        session = self.sessions.get(telegram_id)
        if session:
            await session.stop()
            del self.sessions[telegram_id]
        database.set_user_active_status(telegram_id, False)
        return True

    async def restart_userbot(self, telegram_id: int) -> bool:
        """Qayta ishga tushirish"""
        await self.stop_userbot(telegram_id)
        return await self.start_userbot(telegram_id)

    async def logout_userbot(self, telegram_id: int) -> bool:
        """Akkauntdan butunlay chiqarib yuborish va Telegram sessiyasini tugatish"""
        session = self.sessions.get(telegram_id)
        if session:
            await session.logout_and_clear()
            self.sessions.pop(telegram_id, None)
        else:
            user_data = database.get_user(telegram_id)
            if user_data:
                try:
                    from telethon import TelegramClient
                    from telethon.sessions import StringSession
                    c = TelegramClient(StringSession(user_data["session_string"]), user_data["api_id"], user_data["api_hash"])
                    await c.connect()
                    if await c.is_user_authorized():
                        await c.log_out()
                    await c.disconnect()
                except Exception as e:
                    logger.warning(f"Logout xatosi: {e}")

        from session_store import session_store
        session_store.remove(telegram_id)
        database.delete_user_session(telegram_id)
        logger.info(f"Foydalanuvchi {telegram_id} sessiyasi to'liq chiqarildi.")
        return True

    async def start_all_saved(self):
        """Tizim yoqilganda barcha saqlangan faol userbotlarni ishga tushirish"""
        active_users = database.get_all_active_users()
        logger.info(f"Bazadagi faol sessiyalar soni: {len(active_users)}")
        for u in active_users:
            tid = u["telegram_id"]
            try:
                logger.info(f"Avtomatik ishga tushirilmoqda: {tid}")
                asyncio.create_task(self.start_userbot(tid))
            except Exception as e:
                logger.error(f"{tid} ni ishga tushirishda xatolik: {e}")


manager = UserbotManager()
