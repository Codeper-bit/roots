import { useEffect, useRef } from 'react'

export function TranscriptSegment({
  index,
  text,
  originalText,
  readOnly,
  lang,
  onChange,
}: {
  index: number
  text: string
  originalText: string
  readOnly: boolean
  lang: string
  onChange: (text: string) => void
}) {
  const ref = useRef<HTMLTextAreaElement>(null)
  const edited = text !== originalText

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight + 2}px`
  }, [text, readOnly])

  return (
    <div className={`segment${edited ? ' segment--edited' : ''}`}>
      <div className="segment__gutter">
        <span className="segment__num">{index + 1}</span>
        {edited && <span className="segment__tag">Edited</span>}
      </div>
      {readOnly ? (
        <p className="segment__text" lang={lang}>
          {text}
        </p>
      ) : (
        <textarea
          ref={ref}
          className="segment__input"
          value={text}
          lang={lang}
          rows={1}
          spellCheck={false}
          aria-label={`Transcript segment ${index + 1}`}
          onChange={(e) => onChange(e.target.value)}
        />
      )}
    </div>
  )
}
