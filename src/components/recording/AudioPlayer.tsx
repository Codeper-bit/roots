import { useEffect, useRef, useState } from 'react'
import { formatDuration } from '../../utils/formatDuration'
import { Icon } from '../ui/Icon'

/** Accessible audio player: play/pause, seek, elapsed/total time, speed. */
export function AudioPlayer({
  src,
  durationHintMs,
  label = 'Recording',
}: {
  src: string
  /** Used when the browser cannot read a duration (MediaRecorder WebM files). */
  durationHintMs?: number | null
  label?: string
}) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [duration, setDuration] = useState(0)
  const [speed, setSpeed] = useState(1)

  useEffect(() => {
    setPlaying(false)
    setCurrent(0)
  }, [src])

  const total = Number.isFinite(duration) && duration > 0 ? duration : (durationHintMs ?? 0) / 1000

  function toggle() {
    const a = audioRef.current
    if (!a) return
    if (a.paused) void a.play()
    else a.pause()
  }

  return (
    <div className="player" role="group" aria-label={label}>
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onTimeUpdate={(e) => setCurrent(e.currentTarget.currentTime)}
        onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
        onDurationChange={(e) => setDuration(e.currentTarget.duration)}
      />
      <button
        type="button"
        className="player__play"
        onClick={toggle}
        aria-label={playing ? 'Pause' : 'Play'}
      >
        <Icon name={playing ? 'pause' : 'play'} size={20} />
      </button>
      <span className="player__time" aria-hidden="true">
        {formatDuration(current * 1000)}
      </span>
      <input
        type="range"
        className="player__seek"
        min={0}
        max={total > 0 ? total : 0}
        step={0.1}
        value={Math.min(current, total || 0)}
        onChange={(e) => {
          const t = Number(e.target.value)
          if (audioRef.current) audioRef.current.currentTime = t
          setCurrent(t)
        }}
        disabled={!(total > 0)}
        aria-label="Seek"
        aria-valuetext={`${formatDuration(current * 1000)} of ${formatDuration(total * 1000)}`}
      />
      <span className="player__time" aria-hidden="true">
        {formatDuration(total * 1000)}
      </span>
      <label className="player__speed">
        <span className="sr-only">Playback speed</span>
        <select
          value={speed}
          onChange={(e) => {
            const s = Number(e.target.value)
            setSpeed(s)
            if (audioRef.current) audioRef.current.playbackRate = s
          }}
        >
          {[0.75, 1, 1.25, 1.5].map((s) => (
            <option key={s} value={s}>
              {s}×
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
