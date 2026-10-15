import asyncio
import logging
import time
from typing import Dict, Any, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import User

from ai_engine import ai_service
import database

logger = logging.getLogger(__name__)

# Avto-javob uchun spamdan himoya (cooldown) lug'ati: {chat_id: last_reply_timestamp}
PM_COOLDOWN: Dict[int, float] = {}
COOLDOWN_SECONDS = 60


def split_text(text: str, max_length: int = 4000):
    """Uzun matnni Telegram chekloviga (4096 ta belgi) mos ravishda bo'lish"""
    chunks = []
    while len(text) > max_length:
        split_idx = text.rfind("\n", 0, max_length)
        if split_idx == -1:
            split_idx = max_length
        chunks.append(text[:split_idx].strip())
        text = text[split_idx:].strip()
    if text:
        chunks.append(text)
    return chunks


class UserbotSession:
    def __init__(self, user_data: Dict[str, Any]):
        self.user_data = user_data
        self.telegram_id = user_data["telegram_id"]
        self.api_id = user_data["api_id"]
        self.api_hash = user_data["api_hash"]
        self.session_string = user_data["session_string"]

        self.client: Optional[TelegramClient] = None
        self.me: Optional[User] = None
        self.is_running = False

    def reload_settings(self):
        """Sozlamalarni bazadan qayta yuklash"""
        fresh = database.get_user(self.telegram_id)
        if fresh:
            self.user_data = fresh

    async def start(self):
        """Userbot mijozini ishga tushirish"""
        if self.is_running and self.client and self.client.is_connected():
            return

        logger.info(f"Foydalanuvchi {self.telegram_id} uchun Userbot ulanmoqda...")
        self.client = TelegramClient(
            StringSession(self.session_string),
            self.api_id,
            self.api_hash
        )

        await self.client.connect()
        if not await self.client.is_user_authorized():
            logger.error(f"Foydalanuvchi {self.telegram_id} sessiyasi yaroqsiz!")
            database.set_user_active_status(self.telegram_id, False)
            return False

        self.me = await self.client.get_me()
        
        # Yangilangan sessiya satrini saqlash (DC migration yoki kalit yangilanishi)
        try:
            curr_str = self.client.session.save()
            if curr_str and curr_str != self.session_string:
                self.session_string = curr_str
                database.update_user_session_string(self.telegram_id, curr_str)
                from session_store import session_store
                session_store.update_session_string(self.telegram_id, curr_str)
        except Exception as err:
            logger.warning(f"Sessiyani yangilab saqlashda ogohlantirish: {err}")

        self._register_handlers()
        self.is_running = True
        logger.info(f"✅ Userbot ishga tushdi: {self.me.first_name} (@{self.me.username or 'yo`q'}) [{self.telegram_id}]")
        return True

    async def stop(self):
        """Userbot mijozini vaqtincha to'xtatish"""
        self.is_running = False
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warning(f"Disconnect xatosi: {e}")
        logger.info(f"Userbot to'xtatildi: {self.telegram_id}")

    async def logout_and_clear(self):
        """Akkauntdan rasman log out qilish va sessiyani butunlay yopish"""
        self.is_running = False
        if self.client and self.client.is_connected():
            try:
                await self.client.log_out()
                logger.info(f"Telegram serveridan log_out qilindi: {self.telegram_id}")
            except Exception as e:
                logger.warning(f"Log out xatosi: {e}")
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
        elif self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        logger.info(f"Userbot butunlay chiqarildi: {self.telegram_id}")

    def _register_handlers(self):
        """Telegram hodisalarini tinglovchilarni ro'yxatdan o'tkazish"""
        client = self.client

        # 1. Chiqish xabarlari (Egasi tomonidan yuborilgan buyruqlar va Saved Messages)
        @client.on(events.NewMessage(outgoing=True))
        async def handle_outgoing(event):
            try:
                text = event.raw_text.strip()
                self.reload_settings()

                custom_key = self.user_data.get("custom_gemini_key")
                sys_prompt = self.user_data.get("system_prompt")
                ai_model = self.user_data.get("ai_model", "gemini-1.5-flash")

                # A) Saqlangan xabarlar (Saved Messages) da AI bilan to'g'ridan-to'g'ri suhbat
                if event.is_private and event.chat_id == self.me.id:
                    # Agar xabar AI o'zi tomonidan yozilgan bo'lsa yoki bo'sh bo'lsa o'tkazib yuborish
                    if text.startswith("🤖 [AI Yordamchi]:") or not text:
                        return

                    # Agar maxsus buyruq bo'lmasa, Saved Messages da to'g'ridan-to'g'ri AI javob beradi
                    if not text.startswith((".", "!", "/")):
                        if self.user_data.get("auto_reply_saved", 1) == 1:
                            reply_msg = await event.reply("🧠 *O'ylamoqda...*", parse_mode="markdown")
                            answer = await ai_service.generate_response(
                                prompt=text,
                                system_prompt=sys_prompt,
                                api_key=custom_key,
                                model_name=ai_model
                            )
                            chunks = split_text(answer)
                            await reply_msg.edit(f"🤖 [AI Yordamchi]:\n\n{chunks[0]}")
                            for c in chunks[1:]:
                                await client.send_message(self.me.id, c)
                            return

                # B) Buyruqlar: .ai yoki !ai yoki /ai <savol>
                if text.startswith((".ai ", "!ai ", "/ai ")):
                    prompt = text[4:].strip()
                    if not prompt:
                        await event.edit("⚠️ Iltimos, savol yoki topshiriqni ham yozing.\nMisol: `.ai O'zbekiston poytaxti qayer?`")
                        return

                    await event.edit(f"💭 *Savol:* {prompt}\n\n⏳ *AI o'ylamoqda...*", parse_mode="markdown")
                    answer = await ai_service.generate_response(
                        prompt=prompt,
                        system_prompt=sys_prompt,
                        api_key=custom_key,
                        model_name=ai_model
                    )
                    chunks = split_text(f"🤖 **AI Javobi:**\n\n{answer}")
                    await event.edit(chunks[0], parse_mode="markdown")
                    for extra in chunks[1:]:
                        await event.respond(extra)
                    return

                # C) Buyruq: .xulosa (Biron bir xabarga reply qilinganda)
                if text in (".xulosa", "!xulosa"):
                    if not event.is_reply:
                        await event.edit("⚠️ Bu buyruqni xulosa qilmoqchi bo'lgan xabarga **Reply** qilib yuboring.")
                        return

                    replied = await event.get_reply_message()
                    target_text = replied.raw_text.strip()
                    if not target_text:
                        await event.edit("⚠️ Xabarda matn topilmadi!")
                        return

                    await event.edit("📝 *Matn xulosa qilinmoqda...*", parse_mode="markdown")
                    summary = await ai_service.summarize(target_text, api_key=custom_key)
                    chunks = split_text(f"📋 **Qisqacha Xulosa:**\n\n{summary}")
                    await event.edit(chunks[0], parse_mode="markdown")
                    for extra in chunks[1:]:
                        await event.respond(extra)
                    return

                # D) Buyruq: .tarjima <til> (Reply qilingan matnni tarjima qilish)
                if text.startswith((".tarjima", "!tarjima")):
                    parts = text.split(maxsplit=1)
                    lang = parts[1].strip() if len(parts) > 1 else "o'zbek"

                    if not event.is_reply:
                        await event.edit(f"⚠️ Tarjima qilmoqchi bo'lgan xabarga **Reply** qilib yozing.\nMisol: `.tarjima rus` yoki `.tarjima ingliz`")
                        return

                    replied = await event.get_reply_message()
                    target_text = replied.raw_text.strip()
                    if not target_text:
                        await event.edit("⚠️ Tarjima qilish uchun matn topilmadi!")
                        return

                    await event.edit(f"🌐 *{lang.capitalize()} tiliga tarjima qilinmoqda...*", parse_mode="markdown")
                    translation = await ai_service.translate(target_text, target_lang=lang, api_key=custom_key)
                    chunks = split_text(f"🌐 **Tarjima ({lang}):**\n\n{translation}")
                    await event.edit(chunks[0], parse_mode="markdown")
                    for extra in chunks[1:]:
                        await event.respond(extra)
                    return

                # E) Buyruq: .tuzat (Grammatika va imloni tuzatish)
                if text in (".tuzat", "!tuzat"):
                    if not event.is_reply:
                        await event.edit("⚠️ Xatolarni tuzatmoqchi bo'lgan xabarga **Reply** qilib yuboring.")
                        return

                    replied = await event.get_reply_message()
                    target_text = replied.raw_text.strip()
                    if not target_text:
                        await event.edit("⚠️ Matn topilmadi!")
                        return

                    await event.edit("✍️ *Grammatika tekshirilmoqda va tuzatilmoqda...*", parse_mode="markdown")
                    fixed = await ai_service.fix_grammar(target_text, api_key=custom_key)
                    chunks = split_text(f"✅ **Tuzatilgan Matn:**\n\n{fixed}")
                    await event.edit(chunks[0], parse_mode="markdown")
                    for extra in chunks[1:]:
                        await event.respond(extra)
                    return

                # F) Buyruq: .kod <til> <vazifa>
                if text.startswith((".kod ", "!kod ")):
                    content = text[5:].strip()
                    parts = content.split(maxsplit=1)
                    if len(parts) == 2:
                        language = parts[0]
                        task = parts[1]
                    else:
                        language = "python"
                        task = content

                    await event.edit(f"💻 *{language} tilida kod yozilmoqda...*", parse_mode="markdown")
                    code_res = await ai_service.write_code(task, language=language, api_key=custom_key)
                    chunks = split_text(f"💻 **Dastur Kodi ({language}):**\n\n{code_res}")
                    await event.edit(chunks[0], parse_mode="markdown")
                    for extra in chunks[1:]:
                        await event.respond(extra)
                    return

                # G) Buyruq: .avtojavob on/off
                if text.startswith((".avtojavob", "!avtojavob")):
                    parts = text.split()
                    if len(parts) > 1 and parts[1].lower() in ("on", "yoq", "1", "true"):
                        database.update_user_settings(self.telegram_id, auto_reply_pm=1)
                        await event.edit("✅ **Lichkada (PM) Avto-javob yoqildi!**")
                    elif len(parts) > 1 and parts[1].lower() in ("off", "ochir", "0", "false"):
                        database.update_user_settings(self.telegram_id, auto_reply_pm=0)
                        await event.edit("❌ **Lichkada (PM) Avto-javob o'chirildi!**")
                    else:
                        status = "Yoqilgan" if self.user_data.get("auto_reply_pm") == 1 else "O'chirilgan"
                        await event.edit(f"ℹ️ Avto-javob holati: **{status}**\nO'zgartirish: `.avtojavob on` yoki `.avtojavob off`")
                    return

                # H) Buyruq: .holat
                if text in (".holat", "!holat"):
                    auto_pm = "Yoqilgan ✅" if self.user_data.get("auto_reply_pm") == 1 else "O'chirilgan ❌"
                    auto_saved = "Yoqilgan ✅" if self.user_data.get("auto_reply_saved", 1) == 1 else "O'chirilgan ❌"
                    status_text = (
                        "🤖 **TELEGRAM AI YORDAMCHI HOLATI**\n\n"
                        f"👤 **Egasi:** {self.me.first_name} (@{self.me.username or 'yo`q'})\n"
                        f"🆔 **ID:** `{self.telegram_id}`\n"
                        f"⚡ **AI Modeli:** `{ai_model}`\n"
                        f"📩 **PM Avto-javob:** {auto_pm}\n"
                        f"💾 **Saqlangan xabarlar:** {auto_saved}\n\n"
                        "💡 **Barcha buyruqlarni ko'rish:** `.yordam`"
                    )
                    await event.edit(status_text, parse_mode="markdown")
                    return

                # J) Buyruq: .toxtat (vaqtincha to'xtatish)
                if text in (".toxtat", "!toxtat", ".stop"):
                    await event.edit("🔴 **AI Yordamchi vaqtincha to'xtatildi!**\nQayta yoqish uchun boshqaruvchi botdan foydalaning.")
                    database.set_user_active_status(self.telegram_id, False)
                    await self.stop()
                    return

                # K) Buyruq: .chiqish (akkauntdan butunlay chiqarish)
                if text in (".chiqish", "!chiqish", ".logout"):
                    await event.edit("🚪 **AI Yordamchi akkauntdan chiqarilmoqda...**")
                    await self.logout_and_clear()
                    from session_store import session_store
                    session_store.remove(self.telegram_id)
                    database.delete_user_session(self.telegram_id)
                    return

                # I) Buyruq: .yordam
                if text in (".yordam", "!yordam", ".help"):
                    help_text = (
                        "🌟 **TELEGRAM AI YORDAMCHI BUYRUQLARI**\n\n"
                        "💬 **Sun'iy Intellekt bilan muloqot:**\n"
                        "• `.ai <savol>` — Istalgan chatda sun'iy intellektdan javob olish\n"
                        "• `Saved Messages (Saqlangan xabarlar)` ga to'g'ridan-to'g'ri yozsangiz AI avtomatik javob beradi\n\n"
                        "⚡ **Tezkor Vazifalar (Reply orqali):**\n"
                        "• `.xulosa` — Xabarga reply qilib yuborsangiz, qisqa konspekt qiladi\n"
                        "• `.tarjima <til>` — Xabarni istalgan tilga (uz, ru, en...) tarjima qiladi\n"
                        "• `.tuzat` — Xabardagi imlo va grammatik xatolarni tuzatadi\n"
                        "• `.kod <til> <vazifa>` — Dasturlash kodini yozib beradi\n\n"
                        "⚙️ **Boshqaruv:**\n"
                        "• `.avtojavob on/off` — Lichkadagi avto-javobni yoqish/o'chirish\n"
                        "• `.holat` — Yordamchi holati va sozlamalari\n"
                        "• `.yordam` — Ushbu menyu"
                    )
                    await event.edit(help_text, parse_mode="markdown")
                    return

            except Exception as e:
                logger.error(f"Outgoing xatolik: {e}")

        # 2. Kiruvchi xabarlar (Lichkadagi avto-javob)
        @client.on(events.NewMessage(incoming=True, func=lambda e: e.is_private))
        async def handle_incoming_pm(event):
            try:
                self.reload_settings()
                if self.user_data.get("auto_reply_pm", 0) != 1:
                    return

                # Agar xabar o'zimizdan bo'lsa yoki botlardan bo'lsa e'tiborsiz qoldirish
                sender = await event.get_sender()
                if not sender or getattr(sender, "bot", False) or sender.id == self.me.id:
                    return

                # Cooldown tekshiruvi (spam bo'lmasligi uchun)
                now = time.time()
                last_time = PM_COOLDOWN.get(sender.id, 0)
                if now - last_time < COOLDOWN_SECONDS:
                    return
                PM_COOLDOWN[sender.id] = now

                text = event.raw_text.strip()
                if not text:
                    return

                custom_key = self.user_data.get("custom_gemini_key")
                ai_model = self.user_data.get("ai_model", "gemini-1.5-flash")
                custom_prompt = (
                    f"Siz {self.me.first_name}ning shaxsiy Telegram AI yordamchisisiz. "
                    f"{self.me.first_name} hozir Telegramda band bo'lishi mumkin. "
                    "Suhbatdoshga muloyim va qisqa javob bering, savoliga yordam bering va "
                    f"kerak bo'lsa {self.me.first_name} tez orada javob yozishini bildiring."
                )

                # Javob tayyorlash
                answer = await ai_service.generate_response(
                    prompt=text,
                    system_prompt=custom_prompt,
                    api_key=custom_key,
                    model_name=ai_model
                )

                chunks = split_text(f"🤖 **[AI Avto-Javob]**:\n\n{answer}")
                await event.reply(chunks[0], parse_mode="markdown")
                for extra in chunks[1:]:
                    await client.send_message(event.chat_id, extra)

            except Exception as e:
                logger.error(f"Incoming PM xatolik: {e}")
