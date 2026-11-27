from groq import AsyncGroq


class GroqTranslationEngine:
    def __init__(self, api_key: str, model: str):
        self.client = AsyncGroq(api_key=api_key)
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

        response = await self.client.chat.completions.create(
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

        translated = response.choices[0].message.content

        if not translated or not translated.strip():
            raise ValueError("The translation provider returned empty text.")

        return translated.strip()

    async def close(self) -> None:
        await self.client.close()
