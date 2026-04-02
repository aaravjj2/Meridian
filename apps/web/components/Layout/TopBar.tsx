'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV_ITEMS = [
  { href: '/', label: 'Research', testId: 'nav-research' },
  { href: '/screener', label: 'Screener', testId: 'nav-screener' },
  { href: '/methodology', label: 'Methodology', testId: 'nav-methodology' },
]

export default function TopBar() {
  const pathname = usePathname()
  const mode = (process.env.NEXT_PUBLIC_MERIDIAN_MODE ?? 'DEMO').toUpperCase()
  const isDemo = mode !== 'LIVE'

  return (
    <header className="topbar" data-testid="topbar">
      <div className="topbar-left">
        <div className="wordmark-wrap">
          <span className="wordmark" data-testid="wordmark">
            MERIDIAN
          </span>
          <span className="version-tag">v0.1</span>
        </div>
      </div>

      <nav className="topbar-nav" aria-label="Primary">
        {NAV_ITEMS.map((item) => {
          const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              className={active ? 'nav-link nav-link-active' : 'nav-link'}
              data-testid={item.testId}
            >
              {item.label}
            </Link>
          )
        })}
      </nav>

      <div
        className={isDemo ? 'mode-badge mode-badge-demo' : 'mode-badge mode-badge-live'}
        data-testid="mode-badge"
      >
        {isDemo ? 'DEMO' : 'LIVE'}
      </div>
    </header>
  )
}
