// Decorative cover art, derived deterministically from the story id so each
// card looks distinct. It carries no data.
const PALETTES = [
  ['#E8DDBF', '#C6A66B', '#183D32'],
  ['#CFE0D3', '#A8B9A0', '#183D32'],
  ['#EFD9C8', '#D49A7A', '#5B2E22'],
  ['#D9DFE6', '#8FA3B5', '#1F3A4D'],
] as const

function hash(input: string): number {
  let h = 2166136261
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

export function StoryArt({ seed }: { seed: string }) {
  const h = hash(seed)
  const [light, mid, dark] = PALETTES[h % PALETTES.length]
  const cx = 30 + (h % 40)
  const cy = 70 + ((h >> 4) % 25)
  const gid = `g${h}`
  const rings = [18, 30, 42, 54, 66, 78]
  return (
    <svg className="story-art" viewBox="0 0 200 110" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={light} />
          <stop offset="1" stopColor={mid} />
        </linearGradient>
      </defs>
      <rect width="200" height="110" fill={`url(#${gid})`} />
      <g fill="none" stroke={dark} strokeOpacity="0.28" strokeWidth="0.9">
        {rings.map((r, i) => (
          <ellipse key={r} cx={cx * 2} cy={cy} rx={r * 1.4 + (h % 5) * i * 0.4} ry={r} />
        ))}
      </g>
      <path
        d={`M${cx * 2} 112 C ${cx * 2 + 4} 88, ${cx * 2 - 10} 74, ${cx * 2 + 6} 58 M${cx * 2 + 2} 92 C ${cx * 2 + 20} 84, ${cx * 2 + 30} 70, ${cx * 2 + 44} 66 M${cx * 2 - 2} 84 C ${cx * 2 - 20} 80, ${cx * 2 - 30} 66, ${cx * 2 - 46} 64`}
        fill="none"
        stroke={dark}
        strokeOpacity="0.55"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}
