import type { SVGProps } from 'react'

// Small stroke-icon set (24x24). Kept local so no icon dependency is needed.
const PATHS = {
  home: 'M3 11l9-8 9 8M5 10v10h14V10M10 20v-6h4v6',
  library: 'M4 4h4v16H4zM10 4h4v16h-4zM16.5 5.5l3.8 1-3.4 13.2-3.8-1z',
  mic: 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  checkCircle: 'M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0zM8 12.5l3 3 5-6',
  x: 'M6 6l12 12M18 6L6 18',
  play: 'M7 4.5v15l12-7.5z',
  pause: 'M8 5v14M16 5v14',
  stop: 'M6 6h12v12H6z',
  upload: 'M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3',
  plus: 'M12 5v14M5 12h14',
  arrowRight: 'M5 12h14M13 6l6 6-6 6',
  arrowLeft: 'M19 12H5M11 6l-6 6 6 6',
  alert: 'M12 4l9 16H3zM12 10v4M12 17.5v.01',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8v.01',
  clock: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2',
  globe: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM3 12h18M12 3c2.5 2.5 3.5 5.5 3.5 9S14.5 18.5 12 21M12 3C9.5 5.5 8.5 8.5 8.5 12s1 6.5 3.5 9',
  edit: 'M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16zM13.5 6.5l4 4',
  shield: 'M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z',
  users: 'M9 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM2.5 20a6.5 6.5 0 0 1 13 0M16 4.3a3.5 3.5 0 0 1 0 6.4M18 14.5a6.5 6.5 0 0 1 3.5 5.5',
  menu: 'M4 7h16M4 12h16M4 17h16',
  refresh: 'M20 11a8 8 0 0 0-14-4L4 9M4 4v5h5M4 13a8 8 0 0 0 14 4l2-2M20 20v-5h-5',
  fileAudio: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M10 15v-3l4-1v4M10 15a1.2 1.2 0 1 1-2.4 0 1.2 1.2 0 0 1 2.4 0zM14 15a1.2 1.2 0 1 1-2.4 0 1.2 1.2 0 0 1 2.4 0z',
  message: 'M4 5h16v11H9l-5 4z',
  languages: 'M4 5h8M8 3v2M5.5 5c.5 3 2.5 5.5 5.5 7M11 5c-.5 3-3 6-6.5 8M13 20l4-9 4 9M14.3 17h5.4',
  history: 'M3 12a9 9 0 1 0 3-6.7L3 8M3 3v5h5M12 8v4l3 2',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',
  lock: 'M6 11h12v9H6zM8.5 11V8a3.5 3.5 0 0 1 7 0v3',
  rotate: 'M4 12a8 8 0 1 0 2.6-5.9M4 4v5h5',
  list: 'M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
  share:
    'M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM8.6 13.5l6.8 4M15.4 6.5l-6.8 4',
  copy: 'M9 9h11v11H9zM5 15V4h11',
  mail: 'M3 6h18v12H3zM3 7l9 7 9-7',
  sparkles: 'M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8zM19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z',
  heart: 'M12 20s-8-5-8-11a4.5 4.5 0 0 1 8-2.7A4.5 4.5 0 0 1 20 9c0 6-8 11-8 11z',
} as const

export type IconName = keyof typeof PATHS

interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName
  size?: number
}

export function Icon({ name, size = 20, ...rest }: IconProps) {
  const filled = name === 'play' || name === 'stop'
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      <path d={PATHS[name]} />
    </svg>
  )
}

export function Wordmark({ light = false, size = 22 }: { light?: boolean; size?: number }) {
  return (
    <span className={`wordmark${light ? ' wordmark--light' : ''}`} style={{ fontSize: size }}>
      <svg width={size * 1.15} height={size * 1.15} viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="9" fill={light ? '#F7F5F0' : '#183D32'} />
        <path
          d="M16 26V14M16 14c0-4 3-6 7-6M16 14c0-4-3-6-7-6M16 20c0-2 2-3.5 5-3.5M16 20c0-2-2-3.5-5-3.5"
          stroke={light ? '#183D32' : '#C6A66B'}
          strokeWidth="2"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <span>Roots</span>
    </span>
  )
}
