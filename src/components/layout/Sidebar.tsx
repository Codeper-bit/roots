import { Link, usePathname } from '../../lib/router'
import { Icon, Wordmark, type IconName } from '../ui/Icon'

export const NAV_ITEMS: Array<{ to: string; label: string; icon: IconName; match: (p: string) => boolean }> = [
  { to: '/dashboard', label: 'Stories', icon: 'library', match: (p) => p === '/dashboard' || (p.startsWith('/stories/') && p !== '/stories/new') },
  { to: '/stories/new', label: 'Record a story', icon: 'mic', match: (p) => p === '/stories/new' },
  { to: '/reviews', label: 'Review', icon: 'checkCircle', match: (p) => p === '/reviews' },
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="sidebar">
      <Link to="/" className="sidebar__brand" aria-label="Roots home">
        <Wordmark light />
      </Link>
      <nav aria-label="Primary" className="sidebar__nav">
        {NAV_ITEMS.map((item) => {
          const active = item.match(pathname)
          return (
            <Link key={item.to} to={item.to} className={`nav-link${active ? ' nav-link--active' : ''}`} aria-current={active ? 'page' : undefined}>
              <Icon name={item.icon} size={20} />
              {item.label}
            </Link>
          )
        })}
      </nav>
      <p className="sidebar__foot">
        <Icon name="shield" size={16} />
        <span>AI helps preserve the story. The storyteller decides what is true.</span>
      </p>
    </aside>
  )
}
