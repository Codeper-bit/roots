import { useEffect, useRef } from 'react'

/**
 * Live waveform drawn from the microphone's AnalyserNode. Every bar is the
 * measured loudness (RMS) of a ~45 ms slice of real input. Nothing is
 * simulated: with no input the line is flat.
 */
export function Waveform({
  analyser,
  active,
  clear,
  height = 140,
}: {
  analyser: AnalyserNode | null
  /** true only while audio is actually being captured */
  active: boolean
  /** when true, forget previously drawn bars */
  clear: boolean
  height?: number
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const barsRef = useRef<number[]>([])

  useEffect(() => {
    if (clear) barsRef.current = []
  }, [clear])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    const buffer = analyser ? new Uint8Array(analyser.fftSize) : null
    const barWidth = 3
    const gap = 3
    let raf = 0
    let lastSample = 0

    const color =
      getComputedStyle(document.documentElement).getPropertyValue('--forest').trim() || '#183D32'
    const idle =
      getComputedStyle(document.documentElement).getPropertyValue('--sage').trim() || '#A8B9A0'

    function render(now: number) {
      const el = canvasRef.current
      if (!el || !ctx) return
      const dpr = window.devicePixelRatio || 1
      const w = el.clientWidth
      const h = el.clientHeight
      if (el.width !== Math.round(w * dpr) || el.height !== Math.round(h * dpr)) {
        el.width = Math.round(w * dpr)
        el.height = Math.round(h * dpr)
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      if (active && analyser && buffer && now - lastSample > 45) {
        analyser.getByteTimeDomainData(buffer)
        let sum = 0
        for (let i = 0; i < buffer.length; i++) {
          const v = (buffer[i] - 128) / 128
          sum += v * v
        }
        const rms = Math.sqrt(sum / buffer.length)
        barsRef.current.push(Math.min(1, rms * 3.5))
        if (barsRef.current.length > 2000) barsRef.current.splice(0, 1000)
        lastSample = now
      }

      const slot = barWidth + gap
      const maxBars = Math.max(1, Math.floor(w / slot))
      const bars = barsRef.current.slice(-maxBars)
      const mid = h / 2
      for (let i = 0; i < maxBars; i++) {
        const dataIndex = i - (maxBars - bars.length)
        const x = i * slot
        if (dataIndex < 0) {
          ctx.fillStyle = idle
          ctx.fillRect(x, mid - 1, barWidth, 2)
        } else {
          const amp = Math.max(2, bars[dataIndex] * (h - 8))
          ctx.fillStyle = color
          ctx.fillRect(x, mid - amp / 2, barWidth, amp)
        }
      }
      if (active) raf = requestAnimationFrame(render)
    }

    render(performance.now())
    const observer = new ResizeObserver(() => render(performance.now()))
    observer.observe(canvas)
    return () => {
      cancelAnimationFrame(raf)
      observer.disconnect()
    }
  }, [analyser, active, clear])

  return (
    <canvas
      ref={canvasRef}
      className="waveform"
      style={{ height }}
      role="img"
      aria-label={active ? 'Live microphone level' : 'Microphone level, not recording'}
    />
  )
}
