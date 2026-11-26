import { useCallback, useEffect, useRef, useState } from 'react'

export type RecorderState =
  | 'idle'
  | 'requesting'
  | 'recording'
  | 'paused'
  | 'stopped'
  | 'denied'
  | 'unsupported'
  | 'error'

export interface RecordedAudio {
  blob: Blob
  /** MIME type without codec parameters, e.g. audio/webm (the backend rejects ";codecs=..."). */
  mimeType: string
  extension: string
  durationMs: number
}

const CANDIDATES: Array<{ type: string; ext: string }> = [
  { type: 'audio/webm;codecs=opus', ext: 'webm' },
  { type: 'audio/webm', ext: 'webm' },
  { type: 'audio/ogg;codecs=opus', ext: 'ogg' },
  { type: 'audio/mp4', ext: 'm4a' },
]

function pickMimeType(): { type: string; ext: string } | null {
  if (typeof MediaRecorder === 'undefined') return null
  for (const c of CANDIDATES) {
    if (MediaRecorder.isTypeSupported(c.type)) return c
  }
  return { type: '', ext: 'webm' } // let the browser choose
}

export function useAudioRecorder() {
  const [state, setState] = useState<RecorderState>(() =>
    typeof MediaRecorder === 'undefined' || !navigator.mediaDevices?.getUserMedia
      ? 'unsupported'
      : 'idle',
  )
  const [error, setError] = useState<string | null>(null)
  const [elapsedMs, setElapsedMs] = useState(0)
  const [result, setResult] = useState<RecordedAudio | null>(null)
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null)

  const recorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const formatRef = useRef<{ type: string; ext: string }>({ type: '', ext: 'webm' })
  const accumulatedRef = useRef(0)
  const segmentStartRef = useRef<number | null>(null)
  const timerRef = useRef<number | null>(null)

  const canPause =
    typeof MediaRecorder !== 'undefined' && typeof MediaRecorder.prototype?.pause === 'function'

  const stopTimer = () => {
    if (timerRef.current != null) window.clearInterval(timerRef.current)
    timerRef.current = null
  }

  const currentElapsed = () =>
    accumulatedRef.current +
    (segmentStartRef.current != null ? performance.now() - segmentStartRef.current : 0)

  const startTimer = () => {
    segmentStartRef.current = performance.now()
    stopTimer()
    timerRef.current = window.setInterval(() => setElapsedMs(currentElapsed()), 200)
  }

  const releaseStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    void audioCtxRef.current?.close().catch(() => undefined)
    audioCtxRef.current = null
    setAnalyser(null)
  }, [])

  useEffect(
    () => () => {
      stopTimer()
      if (recorderRef.current && recorderRef.current.state !== 'inactive') {
        recorderRef.current.onstop = null
        recorderRef.current.stop()
      }
      releaseStream()
    },
    [releaseStream],
  )

  const start = useCallback(async () => {
    setError(null)
    setResult(null)
    const format = pickMimeType()
    if (!format || !navigator.mediaDevices?.getUserMedia) {
      setState('unsupported')
      return
    }
    formatRef.current = format
    setState('requesting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const AudioCtx: typeof AudioContext =
        window.AudioContext ??
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext
      const ctx = new AudioCtx()
      const source = ctx.createMediaStreamSource(stream)
      const node = ctx.createAnalyser()
      node.fftSize = 1024
      source.connect(node)
      audioCtxRef.current = ctx
      setAnalyser(node)

      const recorder = new MediaRecorder(stream, format.type ? { mimeType: format.type } : undefined)
      chunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstop = () => {
        stopTimer()
        const durationMs = currentElapsed()
        segmentStartRef.current = null
        const rawType = recorder.mimeType || format.type || 'audio/webm'
        const baseType = rawType.split(';')[0].trim() || 'audio/webm'
        const blob = new Blob(chunksRef.current, { type: baseType })
        releaseStream()
        setElapsedMs(durationMs)
        if (blob.size === 0) {
          setError('Nothing was recorded. Please try again.')
          setState('error')
          return
        }
        setResult({ blob, mimeType: baseType, extension: format.ext, durationMs })
        setState('stopped')
      }
      recorder.onerror = () => {
        stopTimer()
        releaseStream()
        setError('The recording stopped unexpectedly.')
        setState('error')
      }
      recorderRef.current = recorder
      accumulatedRef.current = 0
      setElapsedMs(0)
      recorder.start(1000)
      startTimer()
      setState('recording')
    } catch (err) {
      releaseStream()
      const name = err instanceof DOMException ? err.name : ''
      if (name === 'NotAllowedError' || name === 'SecurityError') {
        setState('denied')
      } else if (name === 'NotFoundError' || name === 'OverconstrainedError') {
        setError('No microphone was found on this device.')
        setState('error')
      } else {
        setError('The microphone could not be started.')
        setState('error')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [releaseStream])

  const pause = useCallback(() => {
    const r = recorderRef.current
    if (!r || r.state !== 'recording') return
    r.pause()
    accumulatedRef.current = currentElapsed()
    segmentStartRef.current = null
    stopTimer()
    setElapsedMs(accumulatedRef.current)
    setState('paused')
  }, [])

  const resume = useCallback(() => {
    const r = recorderRef.current
    if (!r || r.state !== 'paused') return
    r.resume()
    startTimer()
    setState('recording')
  }, [])

  const stop = useCallback(() => {
    const r = recorderRef.current
    if (!r || r.state === 'inactive') return
    // Fold any running segment into the total before onstop reads it.
    r.stop()
  }, [])

  const reset = useCallback(() => {
    stopTimer()
    accumulatedRef.current = 0
    segmentStartRef.current = null
    chunksRef.current = []
    setElapsedMs(0)
    setResult(null)
    setError(null)
    setState(typeof MediaRecorder === 'undefined' ? 'unsupported' : 'idle')
  }, [])

  return { state, error, elapsedMs, result, analyser, canPause, start, pause, resume, stop, reset }
}
