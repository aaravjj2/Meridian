'use client'

import { useMemo } from 'react'

export default function StatusBar() {
  const now = useMemo(() => new Date().toISOString(), [])

  return (
    <footer className="status-bar" data-testid="status-bar">
      <span>GLM-5.1</span>
      <span>demo mode</span>
      <span>{now}</span>
    </footer>
  )
}
