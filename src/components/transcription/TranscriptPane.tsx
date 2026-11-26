import { useEffect, useState } from 'react'
import { createContentVersion } from '../../api/content'
import type { ContentVersion } from '../../types'
import { describeError } from '../../utils/errors'
import { languageName } from '../../utils/languages'
import { Button } from '../ui/Button'
import { Notice } from '../ui/States'
import { useToast } from '../ui/Toast'
import { TranscriptEditor } from './TranscriptEditor'
import { useTranscriptDraft } from './useTranscriptDraft'

/**
 * Shows a transcript version and lets a person correct it. Corrections are
 * saved as a NEW "human_edited" version based on the one on screen, so the
 * original AI draft is never overwritten.
 */
export function TranscriptPane({
  version,
  userId,
  onSaved,
  onDirtyChange,
}: {
  version: ContentVersion
  userId: string
  onSaved: (created: ContentVersion) => void
  onDirtyChange?: (dirty: boolean) => void
}) {
  const toast = useToast()
  const draft = useTranscriptDraft(version)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setEditing(false)
    setError(null)
  }, [version.id])

  useEffect(() => {
    onDirtyChange?.(draft.dirty)
  }, [draft.dirty, onDirtyChange])

  async function save() {
    if (saving) return
    if (!draft.joined.trim()) {
      setError('The transcript can’t be empty.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const created = await createContentVersion({
        story_id: version.story_id,
        content_type: 'transcript',
        language_code: version.language_code,
        content: draft.joined,
        origin: 'human_edited',
        based_on_version_id: version.id,
        created_by: userId,
      })
      toast.success(`Corrections saved as version ${created.version_number}. The earlier version is kept.`)
      setEditing(false)
      onSaved(created)
    } catch (err) {
      setError(describeError(err))
    } finally {
      setSaving(false)
    }
  }

  function cancel() {
    draft.reset()
    setEditing(false)
    setError(null)
  }

  return (
    <div className="stack">
      <div className="pane-toolbar">
        <p className="muted small">
          {languageName(version.language_code)} · {draft.segments.length} segment
          {draft.segments.length === 1 ? '' : 's'}
          {editing && draft.dirty ? ' · unsaved changes' : ''}
        </p>
        <div className="row">
          {editing ? (
            <>
              <Button variant="ghost" size="sm" onClick={cancel} disabled={saving}>
                Discard
              </Button>
              <Button size="sm" icon="check" onClick={save} loading={saving} disabled={!draft.dirty}>
                Save corrections
              </Button>
            </>
          ) : (
            <Button variant="secondary" size="sm" icon="edit" onClick={() => setEditing(true)}>
              Correct the text
            </Button>
          )}
        </div>
      </div>
      {error && (
        <Notice tone="error" title="Couldn’t save your corrections">
          {error}
        </Notice>
      )}
      <TranscriptEditor
        segments={draft.segments}
        original={draft.original}
        readOnly={!editing}
        lang={version.language_code}
        onChange={draft.setText}
      />
    </div>
  )
}
