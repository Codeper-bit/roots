import { useMemo, useState } from 'react'
import { createContentVersion } from '../../api/content'
import { translateTranscript } from '../../api/translation'
import { Link } from '../../lib/router'
import type { ConsentState } from '../../lib/consent'
import type { ContentVersion } from '../../types'
import { describeError } from '../../utils/errors'
import { formatDate } from '../../utils/formatDate'
import {
  LANGUAGE_CODE_PATTERN,
  SEEDED_LANGUAGES,
  canTranslateAutomatically,
  languageName,
} from '../../utils/languages'
import { Badge, OriginBadge, ReviewBadge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Input, Select, Textarea } from '../ui/Field'
import { Notice } from '../ui/States'
import { useToast } from '../ui/Toast'

/**
 * Original and translation side by side.
 *
 * A translation can be created two ways, and both end up as a normal content
 * version that goes through human review like any other text:
 *   - "Translate with AI" asks the backend (POST /translations). The result is
 *     marked AI-generated and unreviewed.
 *   - "Write a translation" lets a person type or correct one by hand.
 */
export function TranslationPanel({
  storyId,
  sourceLanguage,
  original,
  versions,
  translationConsent,
  consentHref,
  userId,
  participantId,
  onSaved,
  readOnly = false,
}: {
  storyId: string
  sourceLanguage: string
  original: ContentVersion | null
  versions: ContentVersion[]
  translationConsent: ConsentState | 'unknown'
  consentHref: string
  userId: string
  /** The storyteller whose consent covers translation. Needed for AI translation. */
  participantId?: string | null
  onSaved: () => void
  readOnly?: boolean
}) {
  const toast = useToast()
  const translationVersions = useMemo(() => versions.filter((v) => v.content_type === 'translation'), [versions])
  const existingLanguages = useMemo(
    () => [...new Set(translationVersions.map((v) => v.language_code))],
    [translationVersions],
  )
  const defaultTarget =
    existingLanguages[0] ?? SEEDED_LANGUAGES.find((l) => l.code !== sourceLanguage)?.code ?? 'yo'
  const [target, setTarget] = useState<string>(defaultTarget)
  const [custom, setCustom] = useState('')
  const [customMode, setCustomMode] = useState(false)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')
  const [saving, setSaving] = useState(false)
  const [translating, setTranslating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const targetCode = customMode ? custom.trim().toLowerCase() : target
  const validTarget = LANGUAGE_CODE_PATTERN.test(targetCode)
  const latest = useMemo(
    () =>
      translationVersions
        .filter((v) => v.language_code === targetCode)
        .sort((a, b) => b.version_number - a.version_number)[0] ?? null,
    [translationVersions, targetCode],
  )
  const consentOk = translationConsent === 'granted'
  const canAutoTranslate =
    !!participantId && !!original && canTranslateAutomatically(targetCode) && targetCode !== sourceLanguage

  async function translateWithAi() {
    if (translating || !participantId || !original || !canAutoTranslate) return
    setTranslating(true)
    setError(null)
    try {
      await translateTranscript({
        story_id: storyId,
        participant_id: participantId,
        source_version_id: original.id,
        target_language_code: targetCode,
      })
      toast.success('Translation created. It is an AI draft, so please have a person review it.')
      onSaved()
    } catch (err) {
      setError(describeError(err))
    } finally {
      setTranslating(false)
    }
  }

  function beginEdit() {
    setDraft(latest?.content ?? '')
    setError(null)
    setEditing(true)
  }

  async function save() {
    if (saving) return
    if (!draft.trim()) {
      setError('Write the translation first.')
      return
    }
    if (!validTarget) {
      setError('Enter a language code with 2–3 lowercase letters.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await createContentVersion(
        latest
          ? {
              story_id: storyId,
              content_type: 'translation',
              language_code: targetCode,
              content: draft,
              origin: 'human_edited',
              based_on_version_id: latest.id,
              created_by: userId,
            }
          : {
              story_id: storyId,
              content_type: 'translation',
              language_code: targetCode,
              content: draft,
              origin: 'human_created',
              created_by: userId,
            },
      )
      toast.success('Translation saved for review.')
      setEditing(false)
      onSaved()
    } catch (err) {
      setError(describeError(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="stack" aria-label="Translation">
      <div className="translation__controls">
        {customMode ? (
          <Input
            label="Translation language code"
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            maxLength={3}
            hint="2–3 letter ISO code that exists in the database’s languages table."
          />
        ) : (
          <Select label="Translate into" value={target} onChange={(e) => setTarget(e.target.value)}>
            {SEEDED_LANGUAGES.filter((l) => l.code !== sourceLanguage || existingLanguages.includes(l.code)).map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
                {existingLanguages.includes(l.code) ? ' (has translation)' : ''}
              </option>
            ))}
          </Select>
        )}
        <Button variant="ghost" size="sm" onClick={() => setCustomMode((v) => !v)}>
          {customMode ? 'Pick from list' : 'Use another language code'}
        </Button>
      </div>

      <div className="translation">
        <div className="translation__col">
          <p className="translation__label">
            <Badge tone="neutral">Original · {languageName(sourceLanguage)}</Badge>
          </p>
          {original ? (
            <p className="translation__text" lang={sourceLanguage}>
              {original.content}
            </p>
          ) : (
            <p className="muted">There is no original transcript yet.</p>
          )}
        </div>
        <div className="translation__col translation__col--target">
          <p className="translation__label">
            <Badge tone="gold">Translation · {validTarget ? languageName(targetCode) : '—'}</Badge>
            {latest && <ReviewBadge status={latest.review_status} />}
          </p>
          {editing ? (
            <div className="stack">
              <Textarea
                label="Translation"
                value={draft}
                rows={10}
                lang={targetCode}
                onChange={(e) => setDraft(e.target.value)}
              />
              {error && (
                <Notice tone="error" title="Couldn’t save the translation">
                  {error}
                </Notice>
              )}
              <div className="row">
                <Button onClick={save} loading={saving}>
                  Save translation
                </Button>
                <Button variant="ghost" onClick={() => setEditing(false)} disabled={saving}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : latest ? (
            <>
              <p className="translation__text" lang={targetCode}>
                {latest.content}
              </p>
              <p className="muted small row row--wrap">
                <OriginBadge origin={latest.origin} /> version {latest.version_number} · {formatDate(latest.created_at)}
              </p>
            </>
          ) : (
            <Notice tone="info" title="No translation yet">
              {canAutoTranslate
                ? `Use “Translate with AI” to create a ${languageName(targetCode)} draft, or write one yourself. AI translations are always marked as drafts until a person reviews them.`
                : 'Write the translation yourself. Automatic translation is only available for English, Yoruba, Hausa and Igbo.'}
            </Notice>
          )}
          {!editing && error && (
            <Notice tone="error" title="Couldn’t translate">
              {error}
            </Notice>
          )}
          {!editing && !readOnly && validTarget && original && (
            <>
              {consentOk ? (
                <div className="row row--wrap">
                  {canAutoTranslate && (
                    <Button icon="sparkles" onClick={translateWithAi} loading={translating}>
                      {latest ? 'Translate again with AI' : 'Translate with AI'}
                    </Button>
                  )}
                  <Button variant="secondary" icon="edit" onClick={beginEdit} disabled={translating}>
                    {latest ? 'Edit translation' : 'Write a translation'}
                  </Button>
                </div>
              ) : (
                <Notice tone="warning" title="Translation permission needed">
                  {translationConsent === 'unknown'
                    ? 'Checking permission…'
                    : 'The storyteller has not granted permission for translation.'}{' '}
                  {translationConsent !== 'unknown' && <Link className="link" to={consentHref}>Review consent</Link>}
                </Notice>
              )}
            </>
          )}
        </div>
      </div>
    </section>
  )
}
