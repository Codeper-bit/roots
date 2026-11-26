// The backend validates language codes as ^[a-z]{2,3}$ and the database
// requires them to exist in the `languages` table. There is no endpoint that
// lists that table, so these are the codes seeded by backend/sql/001_initial.sql.
// Anything else can be entered as a custom ISO 639 code, provided it has been
// added to the database.
export const SEEDED_LANGUAGES = [
  { code: 'yo', name: 'Yoruba', native: 'Yorùbá' },
  { code: 'ha', name: 'Hausa', native: 'Hausa' },
  { code: 'ig', name: 'Igbo', native: 'Igbo' },
] as const

export const LANGUAGE_CODE_PATTERN = /^[a-z]{2,3}$/

export function languageName(code: string): string {
  const known = SEEDED_LANGUAGES.find((l) => l.code === code)
  return known ? known.name : code.toUpperCase()
}
