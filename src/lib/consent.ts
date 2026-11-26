import type { Consent, ConsentPurpose } from '../types'

export interface ConsentPurposeInfo {
  purpose: ConsentPurpose
  title: string
  /** Plain-language statement shown to the participant. */
  description: string
  /** Needed for the core record → transcribe workflow. */
  required: boolean
}

export const CONSENT_PURPOSES: ConsentPurposeInfo[] = [
  {
    purpose: 'audio_storage',
    title: 'Keep my recording',
    description:
      'Roots may store the original audio of this story, privately, so it is preserved exactly as it was told.',
    required: true,
  },
  {
    purpose: 'transcription',
    title: 'Write down what I say',
    description:
      'Roots may send the recording to a speech-to-text service to produce a written draft. The draft is only a suggestion until the storyteller reviews it.',
    required: true,
  },
  {
    purpose: 'translation',
    title: 'Translate my story',
    description:
      'The story may be translated into other languages so more people in the family can read it. Translations are also reviewed by a person.',
    required: false,
  },
  {
    purpose: 'cultural_interpretation',
    title: 'Add cultural context',
    description:
      'Notes may be added to explain words, places or customs in the story, always marked as interpretation and not as the storyteller’s own words.',
    required: false,
  },
  {
    purpose: 'family_sharing',
    title: 'Share with my family',
    description: 'The story may be shared with family members. It stays private until this is granted.',
    required: false,
  },
]

export type ConsentState = 'granted' | 'declined' | 'withdrawn' | 'none'

export interface PurposeConsent {
  state: ConsentState
  /** The active grant when state is granted, otherwise the latest record (if any). */
  record: Consent | null
}

/**
 * The backend returns the full history (oldest first). A purpose is granted
 * when an active `granted` record exists (the database allows only one);
 * otherwise the most recent record decides declined / withdrawn.
 */
export function consentByPurpose(consents: Consent[]): Record<ConsentPurpose, PurposeConsent> {
  const result = {} as Record<ConsentPurpose, PurposeConsent>
  for (const info of CONSENT_PURPOSES) {
    const records = consents.filter((c) => c.purpose === info.purpose)
    const granted = records.find((c) => c.status === 'granted')
    if (granted) {
      result[info.purpose] = { state: 'granted', record: granted }
    } else {
      const latest = records[records.length - 1] ?? null
      result[info.purpose] = { state: latest ? latest.status : 'none', record: latest }
    }
  }
  return result
}
