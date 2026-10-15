# 🤖 Telegram AI Assistant — Shaxsiy Akkauntga Sun'iy Intellekt Ulagich

Ushbu dastur Telegram akkauntingizga **Google Gemini** sun'iy intellektini avtomatik ulab beradi. Siz botga faqat **API ID** va **API HASH** (hamda telefon raqam va tasdiqlash kodi)ni taqdim etasiz, qolgan barcha jarayonni tizim avtomatlashtirilgan tarzda bajaradi!

---

## 🌟 Asosiy Imkoniyatlar

1. **💬 Saved Messages (Saqlangan xabarlar)da shaxsiy AI:**
   - O'zingizning Saqlangan xabarlaringizga xuddi ChatGPT / Gemini kabi istalgan savol yoki topshiriq yozasiz, AI sizga darhol javob beradi.
2. **⚡ Istalgan chatda tezkor AI buyruqlari:**
   - `.ai <savol>` — Guruhlar va shaxsiy chatlarda sun'iy intellektdan javob olish.
   - `.xulosa` — Uzun xabarga Reply qilib yuborsangiz, asosiy mohiyatini qisqa konspekt qilib beradi.
   - `.tarjima <til>` — Xabarga Reply qilib yuborsangiz, ko'rsatilgan tilga (uz, ru, en...) sifatli tarjima qiladi.
   - `.tuzat` — Xabarga Reply qilsangiz, imlo va grammatik xatolarini to'g'rilab beradi.
   - `.kod <til> <vazifa>` — Dasturlash kodini yozib beradi.
3. **📩 Lichkadagi Aqlli Avto-javob (Auto-reply in PM):**
   - Agar boshqa odam sizga lichkada yozsa va siz band bo'lsangiz, AI sizning nomingizdan muloyim va mazmunli javob yozadi (sozlamalardan yoqish/o'chirish mumkin).
4. **🎛 To'liq Telegram Boshqaruvchi Bot:**
   - Yangi akkauntlarni ulash, to'xtatish, qayta yoqish, sozlamalar va shaxsiy promptlarni o'zgartirish qulay tugmalar orqali amalga oshiriladi.

---

## 📁 Loyiha Tuzilishi (`C:\Users\User\Desktop\Abdumalikova`)

- `bot.py` — Telegram Boshqaruvchi Boti (Interaktiv menyu orqali ulash).
- `cli_connect.py` — Terminal orqali to'g'ridan-to'g'ri akkauntni ulash.
- `runner.py` — Saqlangan barcha akkauntlar uchun doimiy fon xizmati.
- `ai_engine.py` — Google Gemini AI integratsiyasi.
- `userbot_client.py` — Akkaunt ichidagi xabarlar va buyruqlar ishlovchisi.
- `userbot_manager.py` — Userbot sessiyalarini boshqarish tizimi.
- `database.py` — SQLite ma'lumotlar bazasi (`data.db`).
- `config.py` — Sozlamalar va konfiguratsiya.
- `.env` — Token va API kalitlar fayli.
- `start_bot.bat` — Windows da 1-bosish orqali Botni ishga tushirish.
- `start_cli.bat` — Windows da Terminal ulagichni ishga tushirish.
- `start_runner.bat` — Windows da Fon xizmatini ishga tushirish.

---

## 🔑 1. Telegram API ID va API HASH olish (1 daqiqa)

1. Brauzerda rasmiy **[https://my.telegram.org](https://my.telegram.org)** saytiga kiring.
2. Telefon raqamingizni kiriting va Telegram ilovangizga kelgan kodni yozib tizimga kiring.
3. **"API development tools"** bo'limini tanlang.
4. **App title** va **Short name** maydonlariga istalgan so'z yozing (masalan: `MyAI` va `myai123`).
5. **"Create application"** tugmasini bosing.
6. Ekranda sizning shaxsiy **`api_id`** (raqam) va **`api_hash`** (harf va raqamlar qatori) ko'rinadi.

---

## 🧠 2. Bepul Google Gemini API Kalitini Olish (Mutlaqo bepul)

1. **[https://aistudio.google.com/](https://aistudio.google.com/)** saytiga kiring.
2. Google akkuntingiz bilan kiring va **"Get API key"** tugmasini bosing.
3. Yaratilgan kalitni nusxalang va `.env` faylidagi `GEMINI_API_KEY=` qatoriga qo'ying (yoki bot ichida sozlamalardan kiriting).

---

## 🤖 3. Telegram Boshqaruvchi Botini Ishga Tushirish

1. Telegramda **[@BotFather](https://t.me/BotFather)** botiga kiring va `/newbot` buyrug'i orqali yangi bot yarating.
2. BotFather bergan token `.env` fayliga allaqachon muvaffaqiyatli kiritildi:
   ```env
   BOT_TOKEN=8870242821:AAHDqVa0KfjfdtG0akL1IWR7kI1luWoS7LM
   GEMINI_API_KEY=YOUR_GEMINI_KEY
   AI_MODEL=gemini-1.5-flash
   ```
3. `start_bot.bat` faylini ikki marta bosing (yoki terminalda `python bot.py` deb yozing).
4. O'z botingizga kiring va `/start` buyrug'ini yuboring.
5. **"🚀 Akkauntni Ulash"** tugmasini bosing:
   - Bot `API_ID` so'raydi -> yuborasiz.
   - Bot `API_HASH` so'raydi -> yuborasiz.
   - Bot telefon raqamingizni so'raydi -> yuborasiz.
   - Telegramga kelgan tasdiqlash kodini yuborasiz.
   - (Agar bo'lsa) 2FA parolini yuborasiz.
6. ✅ **Tayyor! Akkauntingizga sun'iy intellekt avtomatik ulandi va ishga tushdi.**

---

## 💻 4. Muqobil Variant: Terminal Orqali Tezkor Ulash

Agar Telegram Boshqaruvchi Bot ochishni xohlamasangiz, to'g'ridan-to'g'ri terminal orqali ham ulashingiz mumkin:
1. `start_cli.bat` ni bosing (yoki `python cli_connect.py`).
2. Terminal so'ragan API_ID, API_HASH, raqam va kodni kiriting.
3. AI yordamchi darhol akkauntingizda ishga tushadi!

---

## 📋 Foydalanish Buyruqlari

| Buyruq | Izoh | Qayerda ishlaydi |
|---|---|---|
| Har qanday matn | Saved Messages ichida to'g'ridan-to'g'ri AI suhbat | Saqlangan xabarlar |
| `.ai <savol>` | Sun'iy intellektga savol berish | Istalgan chat / guruh |
| `.xulosa` | Reply qilingan xabarni qisqacha mazmunini chiqarish | Istalgan chat |
| `.tarjima <til>` | Reply qilingan xabarni tarjima qilish (masalan `.tarjima en`) | Istalgan chat |
| `.tuzat` | Reply qilingan xabardagi grammatik xatolarni tuzatish | Istalgan chat |
| `.kod <til> <vazifa>` | Dasturlash kodini yaratish (masalan `.kod python kalkulyator`) | Istalgan chat |
| `.avtojavob on/off` | Lichkaga kelgan xabarlarga avto-javobni yoqish/o'chirish | Istalgan chat |
| `.toxtat` | AI yordamchini vaqtincha to'xtatish (muzlatish) | Istalgan chat |
| `.chiqish` | AI yordamchini akkauntdan butunlay chiqarib yuborish | Istalgan chat |
| `.holat` | AI yordamchi holati va sozlamalarini ko'rish | Istalgan chat |
| `.yordam` | Barcha buyruqlar ro'yxatini ko'rish | Istalgan chat |
