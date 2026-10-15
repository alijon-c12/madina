import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

import config
import database
from userbot_manager import manager


async def cli_login():
    print("=" * 60)
    print("🤖 TELEGRAM AKKAUNTGA AI ULASH (TERMINAL ORQALI)")
    print("=" * 60)

    # API ID
    api_id_str = input("1. Telegram API_ID ni kiriting: ").strip()
    if not api_id_str.isdigit():
        print("❌ API_ID faqat sonlardan iborat bo'lishi kerak!")
        return
    api_id = int(api_id_str)

    # API HASH
    api_hash = input("2. Telegram API_HASH ni kiriting: ").strip()
    if len(api_hash) < 16:
        print("❌ API_HASH noto'g'ri!")
        return

    # Telefon
    phone = input("3. Telefon raqamingizni kiriting (+998...): ").strip()

    print("\n⏳ Telegram serveriga ulanmoqda va tasdiqlash kodi yuborilmoqda...")
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()

    if not await client.is_user_authorized():
        res = await client.send_code_request(phone)
        code = input("\n4. Telegramga kelgan tasdiqlash kodini kiriting: ").strip()
        code = code.replace(" ", "")

        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=res.phone_code_hash)
        except SessionPasswordNeededError:
            pwd = input("\n5. Ikki bosqichli tekshiruv (2FA) parolini kiriting: ").strip()
            await client.sign_in(password=pwd)

    me = await client.get_me()
    session_str = client.session.save()
    await client.disconnect()

    print("\n" + "=" * 60)
    print(f"✅ Muvaffaqiyatli ulandi: {me.first_name} (@{me.username or 'yo`q'}) [{me.id}]")
    print("=" * 60)

    # Bazaga saqlash
    database.save_user_session(
        telegram_id=me.id,
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
        session_string=session_str,
        first_name=me.first_name or "",
        username=me.username or ""
    )

    # Userbotni ishga tushirish
    print("🚀 Sun'iy Intellekt Userbot ishga tushirilmoqda...")
    await manager.start_userbot(me.id)
    print("🟢 Userbot faol! Chiqish uchun Ctrl + C bosing.\n")

    # Uzoq muddat ishlashini ta'minlash
    while True:
        await asyncio.sleep(1)


def main():
    try:
        asyncio.run(cli_login())
    except KeyboardInterrupt:
        print("\nTo'xtatildi.")


if __name__ == "__main__":
    main()
