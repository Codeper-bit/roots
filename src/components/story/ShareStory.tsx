import { useMemo, useState } from 'react'
import { Link } from '../../lib/router'
import type { ConsentState } from '../../lib/consent'
import {
  MAX_LINK_TEXT_LENGTH,
  buildShareText,
  copyText,
  mailtoUrl,
  shareableVersions,
  whatsAppUrl,
} from '../../lib/share'
import type { ContentVersion, Story } from '../../types'
import { Button } from '../ui/Button'
import { Select } from '../ui/Field'
import { Icon } from '../ui/Icon'
import { Modal } from '../ui/Modal'
import { Notice } from '../ui/States'
import { useToast } from '../ui/Toast'

/**
 * Share a story that is not private, through WhatsApp, e-mail, any app the
 * device offers, or by copying the text. Recipients do not need a Roots account:
 * what is sent is plain text.
 *
 * Guard rails, because this is the one place a story leaves Roots:
 *   - the story must not be private;
 *   - the storyteller must have granted "family sharing";
 *   - only APPROVED text can be sent, never an unreviewed AI draft.
 * Audio is never shared; recordings stay private.
 */
export function ShareStory({
  story,
  versions,
  storyteller,
  sharingConsent,
  consentHref,
  reviewHref,
}: {
  story: Story
  versions: ContentVersion[]
  storyteller: string | null
  sharingConsent: ConsentState | 'unknown'
  consentHref: string
  reviewHref: string
}) {
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [choice, setChoice] = useState<string | null>(null)

  const options = useMemo(() => shareableVersions(versions), [versions])
  const selected = options.find((o) => o.key === choice) ?? options[0] ?? null

  const text = useMemo(
    () =>
      selected
        ? buildShareText({
            title: story.title,
            storyteller,
            sourceLanguage: story.source_language,
            version: selected.version,
          })
        : '',
    [selected, story.title, story.source_language, storyteller],
  )

  // Private stories have no share button at all.
  if (story.visibility === 'private') return null

  const consentOk = sharingConsent === 'granted'
  const canShare = consentOk && selected !== null
  const tooLongForLinks = text.length > MAX_LINK_TEXT_LENGTH
  const nativeShare = typeof navigator !== 'undefined' && typeof navigator.share === 'function'

  async function share() {
    try {
      await navigator.share({ title: story.title, text })
    } catch (err) {
      // Closing the share sheet is not an error.
      if (!(err instanceof DOMException && err.name === 'AbortError')) {
        toast.error('Couldn’t open the share menu. Try copying the text instead.')
      }
    }
  }

  async function copy() {
    if (await copyText(text)) toast.success('Copied. You can paste it anywhere.')
    else toast.error('Couldn’t copy automatically. Select the text and copy it by hand.')
  }

  return (
    <>
      <Button variant="secondary" icon="share" onClick={() => setOpen(true)}>
        Share
      </Button>
      <Modal open={open} title="Share this story" onClose={() => setOpen(false)}>
        <div className="stack">
          {sharingConsent === 'unknown' ? (
            <p className="muted">Checking permission…</p>
          ) : !consentOk ? (
            <Notice tone="warning" title="Sharing permission needed">
              The storyteller hasn’t agreed to share this story with family yet.{' '}
              <Link className="link" to={consentHref}>
                Review consent
              </Link>
            </Notice>
          ) : options.length === 0 ? (
            <Notice tone="info" title="Nothing approved to share yet">
              Only text that a person has reviewed and approved can be shared.{' '}
              <Link className="link" to={reviewHref}>
                Review the transcript
              </Link>
            </Notice>
          ) : (
            <>
              <p className="muted small">
                Anyone you send this to can read it, even without a Roots account. Only the approved
                text is shared. The recording stays private.
              </p>
              {options.length > 1 && (
                <Select label="What to share" value={selected?.key ?? ''} onChange={(e) => setChoice(e.target.value)}>
                  {options.map((o) => (
                    <option key={o.key} value={o.key}>
                      {o.label}
                    </option>
                  ))}
                </Select>
              )}
              <pre className="share__preview" lang={selected?.version.language_code}>
                {text}
              </pre>
              {tooLongForLinks && (
                <p className="muted small">
                  This story is too long for a WhatsApp or e-mail link. Use “Share…” or “Copy text”
                  to send all of it.
                </p>
              )}
              <div className="share__actions">
                {nativeShare && (
                  <Button icon="share" onClick={share} disabled={!canShare}>
                    Share…
                  </Button>
                )}
                {tooLongForLinks ? (
                  <>
                    <Button variant="secondary" icon="message" disabled>
                      WhatsApp
                    </Button>
                    <Button variant="secondary" icon="mail" disabled>
                      Email
                    </Button>
                  </>
                ) : (
                  <>
                    <a
                      className="btn btn--secondary btn--md"
                      href={whatsAppUrl(text)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <Icon name="message" size={18} />
                      WhatsApp
                    </a>
                    <a className="btn btn--secondary btn--md" href={mailtoUrl(story.title, text)}>
                      <Icon name="mail" size={18} />
                      Email
                    </a>
                  </>
                )}
                <Button variant={nativeShare ? 'secondary' : 'primary'} icon="copy" onClick={copy} disabled={!canShare}>
                  Copy text
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </>
  )
}
