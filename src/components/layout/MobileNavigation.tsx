import { Link, usePathname } from '../../lib/router'
import { Icon } from '../ui/Icon'
import { NAV_ITEMS } from './Sidebar'

export function MobileNavigation() {
  const pathname = usePathname()
  return (
    <nav className="mobile-nav" aria-label="Primary">
      {NAV_ITEMS.map((item) => {
        const active = item.match(pathname)
        return (
          <Link key={item.to} to={item.to} className={`mobile-nav__item${active ? ' mobile-nav__item--active' : ''}`} aria-current={active ? 'page' : undefined}>
            <Icon name={item.icon} size={22} />
            <span>{item.label}</span>
          </Link>
        )
      })}
    </nav>
  )
}
