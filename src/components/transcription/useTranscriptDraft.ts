import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ContentVersion } from '../../types'
import { joinSegments, segmentTranscript, type Segment } from '../../utils/segments'

/** Editable working copy of a transcript version, split into segments. */
export function useTranscriptDraft(version: ContentVersion | null) {
  const original = useMemo(() => (version ? segmentTranscript(version.content) : []), [version])
  const [segments, setSegments] = useState<Segment[]>(original)

  useEffect(() => setSegments(original), [original])

  const setText = useCallback((index: number, text: string) => {
    setSegments((all) => all.map((s, i) => (i === index ? { ...s, text } : s)))
  }, [])

  const reset = useCallback(() => setSegments(original), [original])

  const joined = useMemo(() => joinSegments(segments), [segments])
  const dirty = !!version && joined.trim() !== version.content.trim()

  return { segments, original, setText, reset, joined, dirty }
}
