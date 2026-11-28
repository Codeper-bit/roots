import type { ContentVersion } from '../types'
import { languageName } from '../utils/languages'

/** The longest message we put into a WhatsApp / mailto link. Longer text is copied or shared natively instead. */
export const MAX_LINK_TEXT_LENGTH = 3500

export interface ShareableVersion {
  key: string
  label: string
  version: ContentVersion
}

/**
 * What may leave the app: only the latest APPROVED transcript and translation
 * per language. An unreviewed AI draft is never offered, because the storyteller
 * has not confirmed that it is true.
 */
export function shareableVersions(versions: ContentVersion[]): ShareableVersion[] {
  const latest = new Map<string, ContentVersion>()
  for (const v of versions) {
    if (v.review_status !== 'approved') continue
    if (v.content_type !== 'transcript' && v.content_type !== 'translation') continue
    const key = `${v.content_type}:${v.language_code}`
    const current = latest.get(key)
    if (!current || v.version_number > current.version_number) latest.set(key, v)
  }
  return [...latest.entries()]
    .map(([key, version]) => ({
      key,
      version,
      label: `${version.content_type === 'translation' ? 'Translation' : 'Transcript'} · ${languageName(version.language_code)}`,
    }))
    .sort((a, b) => {
      // Transcripts first, then translations; alphabetical within each.
      if (a.version.content_type !== b.version.content_type) return a.version.content_type === 'transcript' ? -1 : 1
      return a.label.localeCompare(b.label)
    })
}

export function buildShareText({
  title,
  storyteller,
  sourceLanguage,
  version,
}: {
  title: string
  storyteller: string | null
  sourceLanguage: string
  version: ContentVersion
}): string {
  const by = storyteller ? ` told by ${storyteller}` : ''
  const intro =
    version.content_type === 'translation'
      ? `A family story${by} in ${languageName(sourceLanguage)}, translated into ${languageName(version.language_code)}.`
      : `A family story${by} in ${languageName(version.language_code)}.`
  return `${title}\n${intro}\n\n${version.content.trim()}\n\n— Shared from Roots`
}

export function whatsAppUrl(text: string): string {
  return `https://wa.me/?text=${encodeURIComponent(text)}`
}

export function mailtoUrl(subject: string, text: string): string {
  return `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(text)}`
}

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    // Older browsers / insecure origins: fall back to a hidden textarea.
    try {
      const area = document.createElement('textarea')
      area.value = text
      area.setAttribute('readonly', '')
      area.style.position = 'fixed'
      area.style.opacity = '0'
      document.body.appendChild(area)
      area.select()
      const ok = document.execCommand('copy')
      document.body.removeChild(area)
      return ok
    } catch {
      return false
    }
  }
}
