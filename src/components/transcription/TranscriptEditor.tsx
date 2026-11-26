import type { Segment } from '../../utils/segments'
import { TranscriptSegment } from './TranscriptSegment'

export function TranscriptEditor({
  segments,
  original,
  readOnly,
  lang,
  onChange,
}: {
  segments: Segment[]
  original: Segment[]
  readOnly: boolean
  lang: string
  onChange: (index: number, text: string) => void
}) {
  return (
    <div className="transcript" aria-label="Transcript">
      {segments.map((segment, i) => (
        <TranscriptSegment
          key={i}
          index={i}
          text={segment.text}
          originalText={original[i]?.text ?? ''}
          readOnly={readOnly}
          lang={lang}
          onChange={(text) => onChange(i, text)}
        />
      ))}
    </div>
  )
}
