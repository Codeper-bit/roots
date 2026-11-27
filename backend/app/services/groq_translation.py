import logging

import groq
from groq import AsyncGroq

from app.core.errors import UnprocessableError
from app.services.groq_errors import translate_groq_error

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 120.0
MAX_RETRIES = 2


class GroqTranslationEngine:
    def __init__(self, api_key: str, model: str):
        self.client = AsyncGroq(
            api_key=api_key,
            timeout=REQUEST_TIMEOUT_SECONDS,
            max_retries=MAX_RETRIES,
        )
        self.model = model

    async def __call__(
        self,
        *,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        language_names = {
            "yo": "Yoruba",
            "ha": "Hausa",
            "ig": "Igbo",
            "en": "English",
        }

        source_name = language_names.get(source_language, source_language)
        target_name = language_names.get(target_language, target_language)

        try:
            response = await self._complete(source_name, target_name, text)
        except groq.GroqError as exc:
            logger.warning("Groq translation failed (%s: %s)", type(exc).__name__, exc)
            raise translate_groq_error(exc, task="translation") from exc

        translated = response.choices[0].message.content if response.choices else None

        if not translated or not translated.strip():
            raise UnprocessableError("The translation service returned empty text.")

        return translated.strip()

    async def _complete(self, source_name: str, target_name: str, text: str):
        return await self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful translator for a family oral-history "
                        "preservation application. Translate faithfully from the "
                        "source language into the requested target language. "
                        "Preserve names, relationships, cultural references, "
                        "proverbs, idioms, and the speaker's meaning. Do not invent "
                        "missing context. If a phrase is ambiguous, preserve its "
                        "ambiguity as closely as possible. Return only the "
                        "translation, without commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Source language: {source_name}\n"
                        f"Target language: {target_name}\n\n"
                        f"Text to translate:\n{text}"
                    ),
                },
            ],
        )

    async def close(self) -> None:
        await self.client.close()
