'use client'

import { useEffect, useState } from 'react'

export default function StatusBar() {
  const [now, setNow] = useState('')

  useEffect(() => {
    setNow(new Date().toISOString())
  }, [])

  return (
    <footer className="status-bar" data-testid="status-bar">
      <span>GLM-5.1</span>
      <span>demo mode</span>
      <span>{now || 'initializing'}</span>
    </footer>
  )
}
