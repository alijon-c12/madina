import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import logging
import database
from userbot_manager import manager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    print("=" * 60)
    print("🤖 TELEGRAM AI USERBOT SERVISI ISHGA TUSHMOQDA...")
    print("=" * 60)

    database.init_db()
    users = database.get_all_active_users()

    if not users:
        print("⚠️ Hozircha bazada faol akkauntlar yo'q.")
        print("Akkaunt ulash uchun 'python bot.py' yoki 'python cli_connect.py' ni ishga tushiring.")
        return

    print(f"📦 Faol akkauntlar soni: {len(users)}")
    await manager.start_all_saved()
    print("✅ Barcha AI Userbotlar ishga tushdi va xabarlarni kutmoqda...")
    print("To'xtatish uchun: Ctrl + C")

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServis to'xtatildi.")
