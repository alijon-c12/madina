import asyncio
import logging
from typing import Optional
import google.generativeai as genai
from config import GEMINI_API_KEY, DEFAULT_AI_MODEL, DEFAULT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self, default_api_key: Optional[str] = None):
        self.default_api_key = default_api_key or GEMINI_API_KEY

    def _get_api_key(self, custom_key: Optional[str] = None) -> Optional[str]:
        return custom_key.strip() if (custom_key and custom_key.strip()) else self.default_api_key

    def _sync_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        key = self._get_api_key(api_key)
        if not key:
            return (
                "⚠️ **Google Gemini API kaliti o'rnatilmagan!**\n\n"
                "Sun'iy intellekt to'liq ishlashi uchun bepul API kalit kerak:\n"
                "1. [aistudio.google.com](https://aistudio.google.com/) saytiga kiring (bepul).\n"
                "2. 'Get API Key' tugmasini bosing va kalitni nusxalang.\n"
                "3. Boshqaruvchi botda '⚙️ AI Sozlamalari' bo'limi orqali yoki `.env` faylida `GEMINI_API_KEY` ga yozing."
            )

        try:
            genai.configure(api_key=key)
            chosen_model = model_name or DEFAULT_AI_MODEL
            sys_instruction = system_prompt or DEFAULT_SYSTEM_PROMPT

            # Gemini modelini yaratish
            try:
                model = genai.GenerativeModel(
                    model_name=chosen_model,
                    system_instruction=sys_instruction
                )
                response = model.generate_content(prompt)
            except Exception as e:
                # Agar model nomi eski/yangi bo'lsa fallback
                logger.warning(f"Model {chosen_model} bilan xatolik: {e}. 'gemini-1.5-flash' ga o'tilmoqda.")
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=sys_instruction)
                response = model.generate_content(prompt)

            if response and response.text:
                return response.text.strip()
            else:
                return "Kechirasiz, sun'iy intellekt javob qaytara olmadi (javob bo'sh)."

        except Exception as err:
            err_str = str(err)
            logger.error(f"Gemini API xatoligi: {err_str}")
            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                return "❌ Kiritilgan Gemini API kaliti yaroqsiz! Iltimos, kalitni tekshiring."
            elif "RESOURCE_EXHAUSTED" in err_str or "Quota exceeded" in err_str:
                return "⏳ API so'rovlar limiti to'ldi. Birozdan so'ng qayta urinib ko'ring."
            return f"❌ AI xatosi yuz berdi: {err_str[:200]}"

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> str:
        """Asinxron ravishda AI javobini olish"""
        return await asyncio.to_thread(
            self._sync_generate, prompt, system_prompt, api_key, model_name
        )

    async def summarize(self, text: str, api_key: Optional[str] = None) -> str:
        prompt = (
            "Quyidagi matnning asosiy mazmunini o'zbek tilida qisqa, aniq va lo'nda qilib xulosa (konspekt) qilib bering:\n\n"
            f"{text}"
        )
        return await self.generate_response(prompt, api_key=api_key)

    async def translate(self, text: str, target_lang: str = "o'zbek", api_key: Optional[str] = None) -> str:
        prompt = (
            f"Quyidagi matnni professional va tabiiy ohangda {target_lang} tiliga tarjima qiling. "
            f"Faqat tarjimaning o'zini qaytaring:\n\n{text}"
        )
        return await self.generate_response(prompt, api_key=api_key)

    async def fix_grammar(self, text: str, api_key: Optional[str] = None) -> str:
        prompt = (
            "Quyidagi matndagi barcha imlo, tinish belgilari va grammatik xatolarni to'g'irlab, "
            "ravon va chiroyli shaklini yozib bering. Kerak bo'lsa tuzatilgan joylarini qisqacha ko'rsating:\n\n"
            f"{text}"
        )
        return await self.generate_response(prompt, api_key=api_key)

    async def write_code(self, task: str, language: str = "python", api_key: Optional[str] = None) -> str:
        prompt = (
            f"Quyidagi vazifa bo'yicha {language} dasturlash tilida sifatli, toza va to'liq ishlaydigan kod yozib bering. "
            f"Kod ichida zarur tushuntirish va izohlar bo'lsin:\n\n{task}"
        )
        return await self.generate_response(prompt, api_key=api_key)


# Global yagona instansiya
ai_service = AIEngine()
