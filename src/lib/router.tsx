// A deliberately small History-API router: Roots has ~12 routes and no need
// for nested data routers, so this avoids an extra dependency. Swapping to
// react-router later only touches this file and the import sites.
import {
  createContext,
  useContext,
  useSyncExternalStore,
  type AnchorHTMLAttributes,
  type MouseEvent,
  type ReactNode,
} from 'react'

const NAV_EVENT = 'roots:navigate'

function subscribe(callback: () => void) {
  window.addEventListener('popstate', callback)
  window.addEventListener(NAV_EVENT, callback)
  return () => {
    window.removeEventListener('popstate', callback)
    window.removeEventListener(NAV_EVENT, callback)
  }
}

const getSnapshot = () => window.location.pathname + window.location.search

export function navigate(to: string, options: { replace?: boolean } = {}) {
  if (to === getSnapshot()) return
  if (options.replace) window.history.replaceState(null, '', to)
  else window.history.pushState(null, '', to)
  window.dispatchEvent(new Event(NAV_EVENT))
  window.scrollTo(0, 0)
}

export function useNavigate() {
  return navigate
}

export function usePathname(): string {
  const key = useSyncExternalStore(subscribe, getSnapshot)
  return key.split('?')[0]
}

export function useSearchParams(): URLSearchParams {
  const key = useSyncExternalStore(subscribe, getSnapshot)
  const index = key.indexOf('?')
  return new URLSearchParams(index === -1 ? '' : key.slice(index + 1))
}

const ParamsContext = createContext<Record<string, string>>({})
export function useParams(): Record<string, string> {
  return useContext(ParamsContext)
}

interface LinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> {
  to: string
  replace?: boolean
}

export function Link({ to, replace, onClick, children, ...rest }: LinkProps) {
  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    onClick?.(event)
    if (
      event.defaultPrevented ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey ||
      rest.target === '_blank'
    )
      return
    event.preventDefault()
    navigate(to, { replace })
  }
  return (
    <a href={to} onClick={handleClick} {...rest}>
      {children}
    </a>
  )
}

export interface RouteDef {
  path: string
  element: ReactNode
}

function matchPath(pattern: string, pathname: string): Record<string, string> | null {
  const patternParts = pattern.split('/').filter(Boolean)
  const pathParts = pathname.split('/').filter(Boolean)
  if (patternParts.length !== pathParts.length) return null
  const params: Record<string, string> = {}
  for (let i = 0; i < patternParts.length; i++) {
    const p = patternParts[i]
    if (p.startsWith(':')) params[p.slice(1)] = decodeURIComponent(pathParts[i])
    else if (p !== pathParts[i]) return null
  }
  return params
}

/** First match wins, so list static paths (e.g. /stories/new) before /stories/:storyId. */
export function Routes({ routes, fallback }: { routes: RouteDef[]; fallback: ReactNode }) {
  const pathname = usePathname()
  for (const route of routes) {
    const params = matchPath(route.path, pathname)
    if (params) return <ParamsContext.Provider value={params}>{route.element}</ParamsContext.Provider>
  }
  return <ParamsContext.Provider value={{}}>{fallback}</ParamsContext.Provider>
}
