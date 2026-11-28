// The backend validates language codes as ^[a-z]{2,3}$ and the database
// requires them to exist in the `languages` table. There is no endpoint that
// lists that table, so these are the codes seeded by backend/sql/001_initial.sql.
// Anything else can be entered as a custom ISO 639 code, provided it has been
// added to the database.
// English is added by backend/sql/003_add_english.sql; apply it before choosing English.
export const SEEDED_LANGUAGES = [
  { code: 'yo', name: 'Yoruba', native: 'Yorùbá' },
  { code: 'ha', name: 'Hausa', native: 'Hausa' },
  { code: 'ig', name: 'Igbo', native: 'Igbo' },
  { code: 'en', name: 'English', native: 'English' },
] as const

// The speech-to-text model (Whisper on Groq) was not trained on these languages.
// Transcripts still work, but the model has to guess the language, so expect a
// rough draft that needs heavy correction.
const LIMITED_SPEECH_RECOGNITION = new Set(['ig'])

// The backend only accepts these as automatic translation targets
// (schemas/translation.py). Any other language code must be translated by hand.
const AUTO_TRANSLATE_LANGUAGES = new Set(['en', 'yo', 'ha', 'ig'])

export function canTranslateAutomatically(code: string): boolean {
  return AUTO_TRANSLATE_LANGUAGES.has(code.trim().toLowerCase())
}

export function hasLimitedSpeechRecognition(code: string): boolean {
  return LIMITED_SPEECH_RECOGNITION.has(code.trim().toLowerCase())
}

export const LANGUAGE_CODE_PATTERN = /^[a-z]{2,3}$/

export function languageName(code: string): string {
  const known = SEEDED_LANGUAGES.find((l) => l.code === code)
  return known ? known.name : code.toUpperCase()
}
