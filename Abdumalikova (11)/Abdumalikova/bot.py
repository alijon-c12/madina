import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import logging
import re
from typing import Optional

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError
)

import config
import database
from userbot_manager import manager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Suhbat holatlari (ConversationHandler states)
(
    STATE_API_ID,
    STATE_API_HASH,
    STATE_PHONE,
    STATE_CODE,
    STATE_2FA,
    STATE_SET_GEMINI_KEY,
    STATE_SET_PROMPT,
) = range(7)


def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🚀 Akkauntni Ulash"), KeyboardButton("📊 Akkaunt Holati")],
        [KeyboardButton("⏸ AI ni To'xtatish / Yoqish"), KeyboardButton("🚪 Akkauntdan Chiqarish")],
        [KeyboardButton("❓ API ID va HASH olish"), KeyboardButton("⚙️ AI Sozlamalari")],
        [KeyboardButton("📖 To'liq Yo'riqnoma")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start buyrug'i"""
    user = update.effective_user
    text = (
        f"👋 **Assalomu alaykum, {user.first_name}!**\n\n"
        "🤖 **Telegram AI Yordamchi Tizimiga xush kelibsiz!**\n\n"
        "Ushbu bot sizning shaxsiy Telegram akkauntingizga kuchli **Sun'iy Intellekt (AI)** "
        "yordamchisini avtomatik ulab beradi.\n\n"
        "✨ **Imkoniyatlar:**\n"
        "• 💾 **Saqlangan xabarlar:** O'zingizga yozgan har qanday savolingizga AI darhol javob beradi\n"
        "• ⚡ **Istalgan chatda:** `.ai <savol>` deb yozsangiz sun'iy intellekt javob qaytaradi\n"
        "• 📝 **Tezkor buyruqlar:** `.xulosa`, `.tarjima`, `.tuzat`, `.kod`\n"
        "• 📩 **Avto-javob:** Lichkangizga kelgan xabarlarga aqlli va muloyim javob berish\n\n"
        "💡 _Agar Telegram API ID va HASH kodlarini qanday olishni bilmasangiz, pastdagi **'❓ API ID va HASH olish'** tugmasini bosing._\n\n"
        "Boshlash uchun kerakli bo'limni tanlang 👇"
    )
    await update.message.reply_text(text, reply_markup=get_main_keyboard(), parse_mode="markdown")


async def api_guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """API ID va API HASH olish bo'yicha to'liq bosqichma-bosqich qo'llanma"""
    text = (
        "📘 **TELEGRAM API ID VA API HASH OLISH BO'YICHA QO'LLANMA**\n\n"
        "🔑 **API ID va API HASH nima?**\n"
        "Bu Telegram tomonidan sizning shaxsiy akkauntingizga tashqi dasturlar "
        "(masalan, bizning AI Yordamchimiz) xavfsiz ulanishi uchun beriladigan rasmiy kalitlardir. "
        "Uni olish **mutlaqo bepul** va bor-yo'g'i **1 daqiqa** vaqt oladi!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔹 **1-QADAM: Rasmiy saytga kiring**\n"
        "Brauzeringizda (Chrome, Safari, Opera yoki telefon brauzerida) quyidagi rasmiy manzilni oching:\n"
        "👉 **https://my.telegram.org**\n\n"
        "🔹 **2-QADAM: Akkauntingizga kiring (Login)**\n"
        "• **'Your Phone Number'** maydoniga Telegram telefon raqamingizni xalqaro formatda yozing (Masalan: `+998901234567`).\n"
        "• **'Next'** tugmasini bosing.\n"
        "• Telegram ilovangizga (SMS emas, rasmiy Telegram chatiga) tasdiqlash kodi keladi.\n"
        "• Ushbu kodni **'Confirmation code'** maydoniga yozing va **'Sign In'** tugmasini bosing.\n\n"
        "🔹 **3-QADAM: API bo'limiga o'ting**\n"
        "• Ochilgan sahifada birinchi bo'lib turgan **'API development tools'** tugmasini bosing.\n\n"
        "🔹 **4-QADAM: Yangi ilova shaklini to'ldiring**\n"
        "• **App title:** Istalgan nom yozing (Masalan: `MyAI` yoki `Yordamchi`)\n"
        "• **Short name:** Istalgan qisqa nom yozing (Masalan: `myai99`)\n"
        "• _URL va boshqa qatorlarni bo'sh qoldirsangiz ham bo'ladi._\n"
        "• Sahifa pastidagi **'Create application'** ko'k tugmasini bosing.\n\n"
        "🔹 **5-QADAM: Tayyor! Kalitlarni nusxalang:**\n"
        "Sahifada ikkita asosiy qator chiqadi:\n"
        "🆔 **App api_id:** `12345678` (faqat raqamlar)\n"
        "🔑 **App api_hash:** `0123456789abcdef0123456789abcdef` (32 ta belgi)\n\n"
        "Ushbu kodlarni nusxalab oling va botdagi **'🚀 Akkauntni Ulash'** tugmasini bosing!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

    kb = [
        [InlineKeyboardButton("🌐 my.telegram.org saytini ochish", url="https://my.telegram.org")],
        [InlineKeyboardButton("🚀 Akkauntni Ulashni Boshlash", callback_data="start_connect")]
    ]
    markup = InlineKeyboardMarkup(kb)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            text, parse_mode="markdown", reply_markup=markup, disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="markdown", reply_markup=markup, disable_web_page_preview=True
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Umumiy to'liq yo'riqnoma ko'rsatish"""
    text = (
        "📖 **TELEGRAM AI YORDAMCHI — TO'LIQ YO'RIQNOMA**\n\n"
        "📌 **1. API ID va API HASH:**\n"
        "Ushbu kalitlar [my.telegram.org](https://my.telegram.org) saytidan olinadi.\n"
        "Batafsil qo'llanma uchun pastdagi **'❓ API ID va HASH olish'** tugmasini bosing.\n\n"
        "📌 **2. Bepul Google Gemini API kalitini olish:**\n"
        "1. **[aistudio.google.com](https://aistudio.google.com/)** saytiga kiring.\n"
        "2. Google hisobingiz bilan kiring va **'Get API key'** tugmasini bosing.\n"
        "3. Kalitni nusxalab, botdagi **'⚙️ AI Sozlamalari'** bo'limiga kiriting.\n\n"
        "📌 **3. Akkauntingizdan foydalanish:**\n"
        "Akkaunt ulangandan so'ng:\n"
        "• **Saved Messages (Saqlangan xabarlar)** ga o'ting va xuddi ChatGPT bilan gaplashgandek savol yozing!\n"
        "• Istalgan guruh yoki shaxsiy chatda `.ai <savol>` deb yozing.\n"
        "• Istalgan xabarga reply qilib `.xulosa` yoki `.tarjima` deb yozing.\n"
        "• Lichkaga kelgan xabarlarga avto-javob berish uchun sozlamalardan yoqing."
    )
    kb = [
        [InlineKeyboardButton("❓ API ID va HASH olish bo'yicha qo'llanma", callback_data="show_api_guide")],
        [InlineKeyboardButton("🚀 Akkauntni Ulash", callback_data="start_connect")]
    ]
    await update.message.reply_text(
        text, parse_mode="markdown", reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True
    )


# ==========================================
# AKKAUNTNI ULASH (CONVERSATION HANDLER)
# ==========================================

async def connect_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ulash jarayonini boshlash"""
    uid = update.effective_user.id
    existing = database.get_user(uid)

    if existing and manager.is_running(uid):
        kb = [
            [InlineKeyboardButton("🔄 Qayta ulash", callback_data="reconnect_force")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]
        ]
        if update.callback_query:
            await update.callback_query.message.reply_text(
                "⚠️ Sizning akkauntingiz allaqachon ulangan va ishlab turibdi!\n"
                "Uni qayta ulamoqchimisiz?",
                reply_markup=InlineKeyboardMarkup(kb)
            )
        else:
            await update.message.reply_text(
                "⚠️ Sizning akkauntingiz allaqachon ulangan va ishlab turibdi!\n"
                "Uni qayta ulamoqchimisiz?",
                reply_markup=InlineKeyboardMarkup(kb)
            )
        return ConversationHandler.END

    cancel_kb = ReplyKeyboardMarkup([[KeyboardButton("❌ Bekor qilish")]], resize_keyboard=True)
    guide_inline = InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ API ID va HASH qanday olinadi? (Yo'riqnoma)", callback_data="show_api_guide")],
        [InlineKeyboardButton("🌐 my.telegram.org saytiga o'tish", url="https://my.telegram.org")]
    ])

    msg_text = (
        "🚀 **Telegram Akkauntni Ulash — 1-QADAM**\n\n"
        "Iltimos, Telegram `API_ID` raqamingizni kiriting:\n"
        "(Masalan: `23456789`)\n\n"
        "💡 _Agar hali API ID va API HASH olmagan bo'lsangiz, pastdagi yo'riqnoma tugmasini bosing:_ 👇"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(msg_text, parse_mode="markdown", reply_markup=cancel_kb)
        await update.callback_query.message.reply_text("Yordam kerakmi?", reply_markup=guide_inline)
    else:
        await update.message.reply_text(msg_text, parse_mode="markdown", reply_markup=cancel_kb)
        await update.message.reply_text("Yordam kerakmi?", reply_markup=guide_inline)

    return STATE_API_ID


async def connect_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    # Agar foydalanuvchi yo'riqnoma so'rasa yoki noto'g'ri matn yozsa
    if text in ("❓ API ID va HASH olish", "API ID va HASH olish", "qanday", "guide", "help") or not text.isdigit():
        if text not in ("❓ API ID va HASH olish", "API ID va HASH olish"):
            await update.message.reply_text("❌ Xato! API ID faqat raqamlardan iborat bo'lishi kerak.")
        await api_guide_command(update, context)
        await update.message.reply_text(
            "💡 Yuqoridagi yo'riqnomadan so'ng, Telegram `API_ID` raqamingizni kiriting (Masalan: `23456789`):"
        )
        return STATE_API_ID

    clean_id = re.sub(r"\D", "", text)
    if not clean_id:
        await update.message.reply_text("❌ Xato! API ID faqat raqamlardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return STATE_API_ID

    context.user_data["api_id"] = int(clean_id)
    await update.message.reply_text(
        f"✅ API ID qabul qilindi: `{clean_id}`\n\n"
        "🔑 **2-QADAM: Telegram `API_HASH` kodini kiriting:**\n"
        "(Masalan: `a1b2c3d4e5f67890abcdef1234567890`)",
        parse_mode="markdown"
    )
    return STATE_API_HASH


async def connect_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    clean_hash = re.sub(r"[\s\'\"]", "", text)
    if len(clean_hash) < 16:
        await update.message.reply_text("❌ Xato! API HASH juda qisqa yoki noto'g'ri ko'rinadi. Qaytadan kiriting:")
        return STATE_API_HASH

    context.user_data["api_hash"] = clean_hash

    phone_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Raqamimni yuborish", request_contact=True)], [KeyboardButton("❌ Bekor qilish")]],
        resize_keyboard=True
    )
    await update.message.reply_text(
        "✅ API HASH qabul qilindi.\n\n"
        "📱 **3-QADAM: Telefon raqamingizni kiriting:**\n"
        "Pastdagi tugmani bosing yoki raqamni xalqaro formatda yozing (masalan: `+998901234567`):",
        parse_mode="markdown",
        reply_markup=phone_kb
    )
    return STATE_PHONE


async def connect_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    else:
        text = update.message.text.strip()
        if text == "❌ Bekor qilish":
            await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=get_main_keyboard())
            return ConversationHandler.END

        digits = re.sub(r"\D", "", text)
        if len(digits) == 9:  # Masalan: 901234567
            phone = "+998" + digits
        elif len(digits) == 12 and digits.startswith("998"):  # Masalan: 998901234567
            phone = "+" + digits
        elif len(digits) == 11 and digits.startswith("8"):  # Masalan: 89012345678
            phone = "+7" + digits[1:]
        elif not text.startswith("+"):
            phone = "+" + digits
        else:
            phone = "+" + digits

    context.user_data["phone"] = phone
    api_id = context.user_data["api_id"]
    api_hash = context.user_data["api_hash"]

    wait_msg = await update.message.reply_text(
        f"⏳ Telegram serveri ({phone}) bilan bog'lanilmoqda...",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("❌ Bekor qilish")]], resize_keyboard=True)
    )

    try:
        # Vaqtinchalik Telethon mijozi yaratish
        client = TelegramClient(StringSession(), api_id, api_hash)
        await client.connect()

        code_res = await client.send_code_request(phone)
        context.user_data["temp_client"] = client
        context.user_data["phone_code_hash"] = code_res.phone_code_hash

        # Kod qayerga borganini aniqlash
        from telethon.tl.types.auth import SentCodeTypeApp, SentCodeTypeSms, SentCodeTypeCall
        if isinstance(code_res.type, SentCodeTypeApp):
            dest_info = (
                "📱 **KOD TELEGRAM ILOVANGIZGA YUBORILDI!**\n"
                "👉 Telefoningizdagi **'Telegram'** (ko'k galochkali rasmiy chat)ni oching. Kod aynan o'sha yerda!\n"
                "*(Telegram kodni SIM-kartaga SMS qilib emas, Telegram ilovasi ichidagi rasmiy chatga yuboradi)*"
            )
        elif isinstance(code_res.type, SentCodeTypeSms):
            dest_info = "📩 **KOD TELEFONINGIZGA SMS XABAR ORQALI YUBORILDI!**\nTelefoningizdagi SMS larni tekshiring."
        elif isinstance(code_res.type, SentCodeTypeCall):
            dest_info = "📞 **TELEFONINGIZGA QO'NG'IROQ BO'LMOQDA!**\nQo'ng'iroqqa javob berib kodni eshiting."
        else:
            dest_info = "📲 **Telegram ilovangizdagi rasmiy chatni yoki SMS xabarlarni tekshiring.**"

        logger.info(f"API_ID: {api_id}, Phone: {phone}, SentCode type: {type(code_res.type)}, timeout: {getattr(code_res, 'timeout', None)}")

        resend_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📩 Kod kelmadimi? SMS orqali so'rash", callback_data="resend_sms")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]
        ])

        await wait_msg.delete()
        step4_text = (
            f"📨 **TASDIQLASH KODI YUBORILDI!**\n\n"
            f"📞 **Raqam:** `{phone}`\n\n"
            f"{dest_info}\n\n"
            "🔢 **4-QADAM: Ushbu kelgan kodni kiriting:**\n"
            "*(Kodni kiritishda raqamlar orasida bo'sh joy qoldirib yozing: `1 2 3 4 5` yoki `12345`)*\n\n"
            "💡 _Agar Telegram chatiga kod kelmagan bo'lsa, pastdagi **'📩 SMS orqali so'rash'** tugmasini bosing:_"
        )
        await update.message.reply_text(
            step4_text,
            parse_mode="markdown",
            reply_markup=resend_kb
        )
        return STATE_CODE

    except Exception as e:
        err_str = str(e)
        logger.error(f"Kodni so'rashda xatolik: {err_str}")
        await wait_msg.delete()

        if "api_id/api_hash" in err_str or "ApiIdInvalidError" in err_str:
            error_details = (
                "❌ **Telegram API ID yoki API HASH noto'g'ri kiritildi!**\n\n"
                "Iltimos, **[my.telegram.org](https://my.telegram.org)** saytiga kirib:\n"
                "1. `API_ID` faqat raqam ekanligini (masalan: `33543604`);\n"
                "2. `API_HASH` aynan 32 ta belgidan iboratligini tekshirib, qaytadan kiriting."
            )
        elif "PHONE_NUMBER_INVALID" in err_str:
            error_details = f"❌ **Telefon raqam noto'g'ri ko'rinadi:** `{phone}`\nIltimos, haqiqiy raqamingizni kiriting."
        elif "FLOOD_WAIT" in err_str:
            error_details = "⏳ **Telegram vaqtinchalik cheklov qo'ydi (FloodWait).**\nBir necha daqiqa kutib qayta urinib ko'ring."
        else:
            error_details = f"❌ **Xatolik yuz berdi:** {err_str}\n\nIltimos, API ID, HASH va raqamingizni tekshiring."

        await update.message.reply_text(
            error_details,
            reply_markup=get_main_keyboard(),
            parse_mode="markdown"
        )
        return ConversationHandler.END


async def resend_sms_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    client = context.user_data.get("temp_client")
    phone = context.user_data.get("phone")

    if not client or not phone:
        await query.message.reply_text("⚠️ Aloqa uzildi. Iltimos, /start bosib qaytadan boshlang.")
        return ConversationHandler.END

    wait = await query.message.reply_text("⏳ Telegramdan SMS orqali kod so'ralmoqda...")
    try:
        code_res = await client.send_code_request(phone, force_sms=True)
        context.user_data["phone_code_hash"] = code_res.phone_code_hash
        await wait.delete()
        await query.message.reply_text(
            f"📩 **Telegram `{phone}` raqamiga SMS orqali kod yubordi!**\n\n"
            "Iltimos, telefoningizdagi oddiy **SMS xabarlarni** tekshiring va kelgan kodni kiriting:\n"
            "(Masalan: `1 2 3 4 5` yoki `12345`)",
            parse_mode="markdown"
        )
        return STATE_CODE
    except Exception as e:
        await wait.delete()
        err_msg = str(e)
        logger.warning(f"SMS so'rashda xatolik: {err_msg}")
        if "FLOOD_WAIT" in err_msg:
            await query.message.reply_text("⏳ Telegram juda ko'p urinish bo'lgani sababli vaqtinchalik cheklov qo'ydi. 1-2 daqiqa kutib qayta urinib ko'ring.")
        else:
            await query.message.reply_text(f"⚠️ Telegram SMS yuborishda xatolik: {err_msg}\nIltimos, Telegram ilovangizdagi chatni tekshiring.")
        return STATE_CODE


async def connect_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await _clean_temp_client(context)
        await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    if text.lower() in ("kod kelmadi", "kelmadi", "qayerda", "sms kelmadi", "yo'q", "yoq", "qani"):
        phone = context.user_data.get("phone", "")
        await update.message.reply_text(
            f"ℹ️ **KOD QAYERGA KELGANINI TEKSHIRING:**\n\n"
            f"Raqam: `{phone}`\n\n"
            "1. **Telegram ilovangizni** oching (telefoningizda yoki kompyuterda).\n"
            "2. Xabarlar (chatlar) ro'yxatida **'Telegram'** (ko'k belgili rasmiy xizmat xabarnomasi) chatiga kiring.\n"
            "3. Telegram kodni **SMS orqali emas**, aynan o'sha rasmiy chat ichiga yuborgan!\n"
            "4. O'sha yerdagi kodni ko'rib, bu yerga yozing.\n\n"
            "Agar boshidan boshlamoqchi bo'lsangiz, '❌ Bekor qilish' tugmasini bosing.",
            parse_mode="markdown"
        )
        return STATE_CODE

    clean_code = text.replace(" ", "").replace("-", "")
    client: Optional[TelegramClient] = context.user_data.get("temp_client")
    phone = context.user_data.get("phone")
    phone_code_hash = context.user_data.get("phone_code_hash")

    if not client or not client.is_connected():
        await update.message.reply_text("❌ Aloqa uzildi. Iltimos, /start qilib qaytadan boshlang.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    try:
        await client.sign_in(phone=phone, code=clean_code, phone_code_hash=phone_code_hash)
        # Muvaffaqiyatli kirdi!
        return await _complete_login(update, context, client)

    except SessionPasswordNeededError:
        await update.message.reply_text(
            "🔐 **Akkauntingizda Ikki bosqichli tekshiruv (2FA) paroli o'rnatilgan!**\n\n"
            "Iltimos, Telegram 2FA bulutli parolingizni kiriting:",
            parse_mode="markdown"
        )
        return STATE_2FA

    except PhoneCodeInvalidError:
        await update.message.reply_text("❌ Kiritilgan kod noto'g'ri! Iltimos, qaytadan tekshirib kiriting:")
        return STATE_CODE

    except PhoneCodeExpiredError:
        await _clean_temp_client(context)
        await update.message.reply_text("⏳ Kodning muddati o'tgan. Iltimos, boshidan boshlang.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Kirishda xatolik: {e}")
        await update.message.reply_text(f"❌ Xatolik: {e}\nQaytadan urinib ko'ring:")
        return STATE_CODE


async def connect_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "❌ Bekor qilish":
        await _clean_temp_client(context)
        await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    client: Optional[TelegramClient] = context.user_data.get("temp_client")
    if not client:
        await update.message.reply_text("❌ Aloqa uzildi. Boshidan boshlang.", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    try:
        await client.sign_in(password=text)
        return await _complete_login(update, context, client)
    except PasswordHashInvalidError:
        await update.message.reply_text("❌ Parol noto'g'ri! Qaytadan kiriting:")
        return STATE_2FA
    except Exception as e:
        logger.error(f"2FA xatosi: {e}")
        await update.message.reply_text(f"❌ Xatolik: {e}\nQaytadan kiriting:")
        return STATE_2FA


async def _complete_login(update: Update, context: ContextTypes.DEFAULT_TYPE, client: TelegramClient):
    """Muvaffaqiyatli kirilganda sessiyani saqlash va userbotni ishga tushirish"""
    try:
        me = await client.get_me()
        session_str = client.session.save()
        uid = update.effective_user.id
        api_id = context.user_data["api_id"]
        api_hash = context.user_data["api_hash"]
        phone = context.user_data["phone"]

        # Session Store orqali xavfsiz saqlash va zaxiralash
        from session_store import session_store
        session_store.save(
            telegram_id=uid,
            api_id=api_id,
            api_hash=api_hash,
            phone=phone,
            session_string=session_str,
            first_name=me.first_name or "",
            username=me.username or ""
        )

        # Vaqtinchalik mijozni to'xtatish
        await client.disconnect()
        context.user_data.pop("temp_client", None)

        # Manager orqali doimiy userbotni yoqish
        started = await manager.start_userbot(uid)

        success_msg = (
            "🎉 **TABRIKLAYMIZ! AKKAUNTINGIZGA AI YORDAMCHI UL㚅NDI!**\n\n"
            f"👤 **Ulangan profil:** {me.first_name} (@{me.username or 'yo`q'})\n"
            f"📱 **Raqam:** `{phone}`\n"
            f"🤖 **Holati:** {'Faol va Ishlamoqda ✅' if started else 'Saqlandi'}\n\n"
            "✨ **Endi nima qila olasiz?**\n"
            "1️⃣ O'zingizning **Saved Messages (Saqlangan xabarlar)** gatingizga kiring va har qanday savolingizni yozing — AI sizga darhol javob beradi!\n"
            "2️⃣ Istalgan chatda yoki guruhda `.ai <savol>` deb yozsangiz sun'iy intellekt xabaringizni tahlil qilib javob beradi.\n"
            "3️⃣ Istalgan xabarga **Reply** qilib `.xulosa` yoki `.tarjima` deb yozing.\n\n"
            "⚙️ Sozlamalarni o'zgartirish uchun **'AI Sozlamalari'** bo'limiga kiring."
        )
        await update.message.reply_text(success_msg, parse_mode="markdown", reply_markup=get_main_keyboard())
        return ConversationHandler.END

    except Exception as e:
        logger.error(f"Complete login error: {e}")
        await update.message.reply_text(f"❌ Xatolik yuz berdi: {e}", reply_markup=get_main_keyboard())
        return ConversationHandler.END


async def _clean_temp_client(context: ContextTypes.DEFAULT_TYPE):
    client = context.user_data.get("temp_client")
    if client:
        try:
            await client.disconnect()
        except Exception:
            pass
        context.user_data.pop("temp_client", None)


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _clean_temp_client(context)
    await update.message.reply_text("Jarayon bekor qilindi.", reply_markup=get_main_keyboard())
    return ConversationHandler.END


# ==========================================
# AKKAUNT HOLATI VA BOSHQARUV (TO'XTATISH / CHIQARISH)
# ==========================================

async def toggle_ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI yordamchini vaqtincha to'xtatish yoki qayta yoqish"""
    uid = update.effective_user.id
    user = database.get_user(uid)
    if not user:
        await update.message.reply_text("⚠️ Sizda hali ulangan akkaunt yo'q. Avval '🚀 Akkauntni Ulash' orqali ulang.", reply_markup=get_main_keyboard())
        return

    is_active = manager.is_running(uid)
    if is_active:
        await manager.stop_userbot(uid)
        await update.message.reply_text(
            "🔴 **Sun'iy Intellekt vaqtincha to'xtatildi!**\n\n"
            "• Akkauntingizdagi xabarlarga va buyruqlarga endi AI javob bermaydi.\n"
            "• Sessiyangiz saqlanib turibdi (qaytadan kod kiritish shart emas).\n"
            "• Qayta yoqish uchun yana shu **'⏸ AI ni To'xtatish / Yoqish'** tugmasini bosing.",
            reply_markup=get_main_keyboard(),
            parse_mode="markdown"
        )
    else:
        success = await manager.start_userbot(uid)
        if success:
            await update.message.reply_text(
                "🟢 **Sun'iy Intellekt qayta ishga tushirildi!**\n\n"
                "AI yordamchi akkauntingizda yana faol ishlamoqda ✅",
                reply_markup=get_main_keyboard(),
                parse_mode="markdown"
            )
        else:
            await update.message.reply_text("❌ Qayta ishga tushirishda xatolik yuz berdi. Akkauntni qayta ulashga urinib ko'ring.", reply_markup=get_main_keyboard())


async def logout_confirm_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI yordamchini akkauntdan butunlay chiqarib yuborishni tasdiqlash"""
    uid = update.effective_user.id
    user = database.get_user(uid)
    if not user:
        await update.message.reply_text("⚠️ Sizda hozir ulangan akkaunt yo'q.", reply_markup=get_main_keyboard())
        return

    kb = [
        [InlineKeyboardButton("🚪 Ha, Akkauntdan Butunlay Chiqarish", callback_data=f"confirm_logout_{uid}")],
        [InlineKeyboardButton("⏸ Shunchaki vaqtincha to'xtatish", callback_data=f"toggle_active_{uid}")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]
    ]
    msg = (
        "⚠️ **SUN'IY INTELLEKTNI AKKAUNTDAN CHIQARIB YUBORISH**\n\n"
        f"👤 **Profil:** {user.get('first_name')} (`{user.get('phone')}`)\n\n"
        "Rostdan ham Sun'iy Intellektni akkauntingizdan butunlay chiqarib yubormoqchimisiz?\n\n"
        "• Telegram ilovangizdagi **faol qurilmalar (sessiya) ro'yxatidan rasman o'chiriladi**.\n"
        "• AI barcha xabarlar va buyruqlarga javob berishdan to'xtaydi.\n"
        "• Kerak bo'lmagan paytda chiqarib yuborish juda xavfsiz va to'g'ri qaror.\n\n"
        "Quyidagilardan birini tanlang:"
    )
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode="markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = database.get_user(uid)

    if not user:
        kb = [[InlineKeyboardButton("🚀 Akkauntni Ulash", callback_data="start_connect")]]
        await update.message.reply_text(
            "ℹ️ Hozircha sizning akkauntingiz ulanmagan.\n"
            "Sun'iy intellektni ulash uchun '🚀 Akkauntni Ulash' tugmasini bosing.",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    is_active = manager.is_running(uid)
    status_icon = "🟢 Faol (Ishlamoqda)" if is_active else "🔴 To'xtatilgan"
    auto_pm = "Yoqilgan ✅" if user.get("auto_reply_pm") == 1 else "O'chirilgan ❌"
    auto_saved = "Yoqilgan ✅" if user.get("auto_reply_saved", 1) == 1 else "O'chirilgan ❌"

    msg = (
        "📊 **AKKAUNT VA AI YORDAMCHI HOLATI**\n\n"
        f"👤 **Profil:** {user.get('first_name')} (@{user.get('username') or 'yo`q'})\n"
        f"📱 **Raqam:** `{user.get('phone')}`\n"
        f"⚡ **Holat:** {status_icon}\n"
        f"🧠 **AI Modeli:** `{user.get('ai_model')}`\n"
        f"📩 **PM Avto-javob:** {auto_pm}\n"
        f"💾 **Saqlangan xabarlar:** {auto_saved}\n"
        f"🔑 **Shaxsiy Gemini API kalit:** {'Kiritilgan ✅' if user.get('custom_gemini_key') else 'Standart kalit ishlatilmoqda'}\n"
    )

    kb = [
        [
            InlineKeyboardButton("⏸ To'xtatish" if is_active else "▶️ Ishga tushirish", callback_data=f"toggle_active_{uid}"),
            InlineKeyboardButton("🔄 Qayta yuklash", callback_data=f"restart_{uid}")
        ],
        [InlineKeyboardButton("🚪 Akkauntdan Chiqarish (Uzish)", callback_data=f"logout_{uid}")]
    ]
    await update.message.reply_text(msg, parse_mode="markdown", reply_markup=InlineKeyboardMarkup(kb))


# ==========================================
# AI SOZLAMALARI
# ==========================================

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = database.get_user(uid)

    if not user:
        await update.message.reply_text(
            "⚠️ Sozlamalarni ko'rish uchun avval akkauntingizni ulang!",
            reply_markup=get_main_keyboard()
        )
        return

    auto_pm_status = "O'chirish ❌" if user.get("auto_reply_pm") == 1 else "Yoqish ✅"
    auto_saved_status = "O'chirish ❌" if user.get("auto_reply_saved", 1) == 1 else "Yoqish ✅"

    msg = (
        "⚙️ **AI YORDAMCHI SOZLAMALARI**\n\n"
        f"• **Lichkadagi Avto-javob (PM):** {'Yoqilgan ✅' if user.get('auto_reply_pm') == 1 else 'O`chirilgan ❌'}\n"
        f"• **Saqlangan xabarlar AI:** {'Yoqilgan ✅' if user.get('auto_reply_saved', 1) == 1 else 'O`chirilgan ❌'}\n"
        f"• **AI Modeli:** `{user.get('ai_model')}`\n"
        f"• **Shaxsiy Prompt:** {('O`rnatilgan: ' + user.get('system_prompt')[:50] + '...') if user.get('system_prompt') else 'Standart rejim'}\n\n"
        "O'zgartirish uchun quyidagi tugmalardan birini bosing:"
    )

    kb = [
        [InlineKeyboardButton(f"📩 PM Avto-javob: {auto_pm_status}", callback_data=f"toggle_pm_{uid}")],
        [InlineKeyboardButton(f"💾 Saqlangan xabarlar: {auto_saved_status}", callback_data=f"toggle_saved_{uid}")],
        [InlineKeyboardButton("🔑 Gemini API Kalitini Kiritish", callback_data=f"set_key_{uid}")],
        [InlineKeyboardButton("📝 AI Xarakterini (Prompt) O'zgartirish", callback_data=f"set_prompt_{uid}")],
        [InlineKeyboardButton("🔄 Session Store ni Yangilash", callback_data="refresh_store")]
    ]
    await update.message.reply_text(msg, parse_mode="markdown", reply_markup=InlineKeyboardMarkup(kb))


# ==========================================
# CALLBACK QUERY (TUGMALAR) HANDLER
# ==========================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = update.effective_user.id

    if data.startswith("toggle_active_"):
        is_active = manager.is_running(uid)
        if is_active:
            await manager.stop_userbot(uid)
            await query.edit_message_text("🔴 Akkaunt AI yordamchisi to'xtatildi.")
        else:
            await manager.start_userbot(uid)
            await query.edit_message_text("🟢 Akkaunt AI yordamchisi ishga tushirildi!")

    elif data.startswith("restart_"):
        await query.edit_message_text("🔄 Qayta yuklanmoqda...")
        await manager.restart_userbot(uid)
        await query.message.reply_text("✅ Userbot muvaffaqiyatli qayta ishga tushirildi!")

    elif data.startswith("logout_"):
        uid = int(data.split("_")[1])
        user = database.get_user(uid)
        kb = [
            [InlineKeyboardButton("🚪 Ha, Butunlay Chiqarish", callback_data=f"confirm_logout_{uid}")],
            [InlineKeyboardButton("⏸ Shunchaki vaqtincha to'xtatish", callback_data=f"toggle_active_{uid}")],
            [InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_action")]
        ]
        await query.message.reply_text(
            "⚠️ **SUN'IY INTELLEKTNI AKKAUNTDAN CHIQARIB YUBORISH**\n\n"
            "Rostdan ham Sun'iy Intellektni akkauntingizdan butunlay chiqarib yubormoqchimisiz?\n\n"
            "• Telegram ilovangizdagi **faol qurilmalar (sessiya) ro'yxatidan rasman o'chiriladi**.\n"
            "• AI barcha xabarlar va buyruqlarga javob berishni to'xtatadi.\n"
            "• Keyinroq yana kerak bo'lsa, istalgan payt qaytadan ulashingiz mumkin.\n\n"
            "Agar shunchaki vaqtincha xalaqit bermasligini xohlasangiz, '⏸ Shunchaki vaqtincha to'xtatish' tugmasini bosing.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="markdown"
        )

    elif data.startswith("confirm_logout_"):
        uid = int(data.split("_")[2])
        await query.edit_message_text("⏳ Akkauntdan rasman log out qilinmoqda...")
        await manager.logout_userbot(uid)
        await query.message.reply_text(
            "✅ **Sun'iy Intellekt akkauntingizdan butunlay chiqarib yuborildi!**\n\n"
            "• Telegram ilovangizdagi sessiya to'liq yopildi.\n"
            "• Baza va zaxiradan barcha ma'lumotlar tozalandi.\n\n"
            "Qachondir yana kerak bo'lsa, '🚀 Akkauntni Ulash' orqali qayta ulashingiz mumkin.",
            reply_markup=get_main_keyboard(),
            parse_mode="markdown"
        )

    elif data.startswith("toggle_pm_"):
        user = database.get_user(uid)
        new_val = 0 if user.get("auto_reply_pm") == 1 else 1
        database.update_user_settings(uid, auto_reply_pm=new_val)
        txt = "Yoqildi ✅" if new_val == 1 else "O'chirildi ❌"
        await query.edit_message_text(f"📩 Lichkadagi (PM) avto-javob: **{txt}**", parse_mode="markdown")

    elif data.startswith("toggle_saved_"):
        user = database.get_user(uid)
        new_val = 0 if user.get("auto_reply_saved", 1) == 1 else 1
        database.update_user_settings(uid, auto_reply_saved=new_val)
        txt = "Yoqildi ✅" if new_val == 1 else "O'chirildi ❌"
        await query.edit_message_text(f"💾 Saqlangan xabarlardagi AI: **{txt}**", parse_mode="markdown")

    elif data.startswith("set_key_"):
        context.user_data["awaiting_key"] = True
        await query.message.reply_text(
            "🔑 **Google Gemini API kalitingizni yuboring:**\n\n"
            "Agar hali olmagan bo'lsangiz, [aistudio.google.com](https://aistudio.google.com/) saytidan 1 daqiqada bepul olishingiz mumkin.\n"
            "Kalitni bekor qilish uchun `/cancel` deb yozing.",
            parse_mode="markdown"
        )

    elif data.startswith("set_prompt_"):
        context.user_data["awaiting_prompt"] = True
        await query.message.reply_text(
            "📝 **AI uchun yangi xarakter (System Prompt) yuboring:**\n\n"
            "Misol:\n"
            "`Siz Abdumalikning yordamchisisiz. Qisqa va hazilomuz javob bering.`\n\n"
            "Standart holatga qaytarish uchun `reset` deb yuboring.",
            parse_mode="markdown"
        )

    elif data == "show_api_guide":
        await api_guide_command(update, context)

    elif data == "refresh_store":
        from session_store import session_store
        res = session_store.refresh_store()
        kb_size = round(res.get('database_size', 0) / 1024, 2)
        txt = (
            "✨ **SESSION STORE MUVAFFAQIYATLI YANGILANDI!**\n\n"
            f"📦 **Faol sessiyalar:** {res.get('active_sessions', 0)} ta\n"
            f"💾 **Zaxiralangan fayllar:** {res.get('synced_files', 0)} ta\n"
            f"🧹 **Tozalangan eski fayllar:** {res.get('cleaned_files', 0)} ta\n"
            f"⚡ **Baza hajmi:** {kb_size} KB\n\n"
            "Barcha sessiyalar sinxronlandi va ombor optimallashtirildi!"
        )
        await query.message.reply_text(txt, parse_mode="markdown")

    elif data == "cancel_action":
        await query.edit_message_text("Bekor qilindi.")


# ==========================================
# MATNLI XABARLARNI QABUL QILISH (Sozlamalar uchun)
# ==========================================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    uid = update.effective_user.id

    if text in ("🚀 Akkauntni Ulash", "Akkauntni Ulash"):
        return await connect_start(update, context)
    elif text in ("📊 Akkaunt Holati", "Akkaunt Holati"):
        return await status_command(update, context)
    elif text in ("⏸ AI ni To'xtatish / Yoqish", "AI ni To'xtatish", "AI ni Yoqish", "/pause", "/toggle"):
        return await toggle_ai_command(update, context)
    elif text in ("🚪 Akkauntdan Chiqarish", "Akkauntdan Chiqarish", "Chiqarish", "Uzish", "/logout", "/disconnect"):
        return await logout_confirm_command(update, context)
    elif text in ("⚙️ AI Sozlamalari", "AI Sozlamalari"):
        return await settings_command(update, context)
    elif text in ("❓ API ID va HASH olish", "API ID va HASH olish", "API ID olish", "API HASH olish"):
        return await api_guide_command(update, context)
    elif text in ("📖 To'liq Yo'riqnoma", "📖 Yo'riqnoma", "Yo'riqnoma"):
        return await help_command(update, context)
    elif text in ("🔄 Session Store ni Yangilash", "Sessiyani yangilash", "/refresh_session"):
        from session_store import session_store
        res = session_store.refresh_store()
        kb_size = round(res.get('database_size', 0) / 1024, 2)
        txt = (
            "✨ **SESSION STORE MUVAFFAQIYATLI YANGILANDI!**\n\n"
            f"📦 **Faol sessiyalar:** {res.get('active_sessions', 0)} ta\n"
            f"💾 **Zaxiralangan fayllar:** {res.get('synced_files', 0)} ta\n"
            f"🧹 **Tozalangan eski fayllar:** {res.get('cleaned_files', 0)} ta\n"
            f"⚡ **Baza hajmi:** {kb_size} KB\n\n"
            "Barcha sessiyalar sinxronlandi va ombor optimallashtirildi!"
        )
        return await update.message.reply_text(txt, parse_mode="markdown")

    # API kalit kiritish kutilayotgan bo'lsa
    if context.user_data.get("awaiting_key"):
        if text.startswith("/cancel"):
            context.user_data["awaiting_key"] = False
            await update.message.reply_text("Bekor qilindi.", reply_markup=get_main_keyboard())
            return
        database.update_user_settings(uid, custom_gemini_key=text)
        context.user_data["awaiting_key"] = False
        await update.message.reply_text("✅ Gemini API kaliti muvaffaqiyatli saqlandi!", reply_markup=get_main_keyboard())
        return

    # Prompt kiritish kutilayotgan bo'lsa
    if context.user_data.get("awaiting_prompt"):
        if text.lower() == "reset":
            database.update_user_settings(uid, system_prompt=None)
            await update.message.reply_text("✅ Tizim prompti standart holatga qaytarildi.", reply_markup=get_main_keyboard())
        else:
            database.update_user_settings(uid, system_prompt=text)
            await update.message.reply_text("✅ Yangi AI Prompt saqlandi!", reply_markup=get_main_keyboard())
        context.user_data["awaiting_prompt"] = False
        return


# ==========================================
# DASTURNI ISHGA TUSHIRISH
# ==========================================

async def post_init(application: Application):
    """Bot ishga tushgach bazadagi barcha faol userbotlarni uyg'otish"""
    logger.info("Bot initsializatsiya qilindi. Saqlangan akkauntlar ishga tushirilmoqda...")
    await manager.start_all_saved()


def main():
    token = config.BOT_TOKEN
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("\n" + "=" * 60)
        print("❌ XATOLIK: BOT_TOKEN aniqlanmadi!")
        print("Iltimos, .env faylini oching va Telegram @BotFather dan")
        print("olingan bot tokenini kiriting:")
        print("BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ")
        print("=" * 60 + "\n")
        return

    print("🤖 Telegram AI Boshqaruvchi Bot ishga tushmoqda...")
    database.init_db()

    app = Application.builder().token(token).post_init(post_init).build()

    # Akkaunt ulash conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 Akkauntni Ulash$"), connect_start),
            CallbackQueryHandler(connect_start, pattern="^start_connect$|^reconnect_force$")
        ],
        states={
            STATE_API_ID: [
                CallbackQueryHandler(api_guide_command, pattern="^show_api_guide$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, connect_api_id)
            ],
            STATE_API_HASH: [
                CallbackQueryHandler(api_guide_command, pattern="^show_api_guide$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, connect_api_hash)
            ],
            STATE_PHONE: [
                MessageHandler(filters.CONTACT, connect_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, connect_phone)
            ],
            STATE_CODE: [
                CallbackQueryHandler(resend_sms_handler, pattern="^resend_sms$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, connect_code)
            ],
            STATE_2FA: [MessageHandler(filters.TEXT & ~filters.COMMAND, connect_2fa)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            MessageHandler(filters.Regex("^❌ Bekor qilish$"), cancel_handler)
        ],
        allow_reentry=True
    )

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("guide", api_guide_command))
    app.add_handler(CommandHandler("api_guide", api_guide_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("toggle", toggle_ai_command))
    app.add_handler(CommandHandler("pause", toggle_ai_command))
    app.add_handler(CommandHandler("logout", logout_confirm_command))
    app.add_handler(CommandHandler("disconnect", logout_confirm_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("✅ Bot muvaffaqiyatli ishga tushdi! Telegram orqali /start yuboring.")
    app.run_polling()


if __name__ == "__main__":
    main()
