// Presentation-only splitting of a transcript into readable chunks. The
// backend stores a transcript as one plain-text string: there are no
// timestamps, speakers or word confidences, so none are invented here.
// Splitting is lossless: joinSegments(segmentTranscript(t)) === t.

export interface Segment {
  text: string
  /** whitespace that followed this segment in the original text */
  sep: string
}

const SENTENCE = /(\s*\S[\s\S]*?(?:[.!?。？！]+["'”’)\]]*(?=\s|$)|(?=\n)|$))(\s*)/g

export function segmentTranscript(text: string, maxChars = 280): Segment[] {
  const sentences: Segment[] = []
  for (const m of text.matchAll(SENTENCE)) sentences.push({ text: m[1], sep: m[2] })
  if (sentences.length === 0) return text ? [{ text, sep: '' }] : []

  const segments: Segment[] = []
  let current: Segment | null = null
  for (const s of sentences) {
    if (!current) {
      current = { ...s }
      continue
    }
    const breakHere = current.sep.includes('\n') || current.text.length + current.sep.length + s.text.length > maxChars
    if (breakHere) {
      segments.push(current)
      current = { ...s }
    } else {
      current = { text: current.text + current.sep + s.text, sep: s.sep }
    }
  }
  if (current) segments.push(current)
  return segments
}

export function joinSegments(segments: Segment[]): string {
  return segments.map((s) => s.text + s.sep).join('')
}
