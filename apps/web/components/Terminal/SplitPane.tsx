'use client'

import { useState } from 'react'

type SplitPaneProps = {
  left: React.ReactNode
  right: React.ReactNode
}

export default function SplitPane({ left, right }: SplitPaneProps) {
  const [leftWidth, setLeftWidth] = useState(55)

  function handleDrag(clientX: number) {
    const windowWidth = window.innerWidth
    const next = Math.min(75, Math.max(35, (clientX / windowWidth) * 100))
    setLeftWidth(next)
  }

  return (
    <div className="split-pane" data-testid="split-pane">
      <section className="split-left" style={{ width: `${leftWidth}%` }} data-testid="research-panel">
        {left}
      </section>
      <button
        type="button"
        className="split-divider"
        aria-label="Resize panels"
        onMouseDown={(event) => {
          event.preventDefault()
          const onMove = (moveEvent: MouseEvent) => handleDrag(moveEvent.clientX)
          const onUp = () => {
            window.removeEventListener('mousemove', onMove)
            window.removeEventListener('mouseup', onUp)
          }
          window.addEventListener('mousemove', onMove)
          window.addEventListener('mouseup', onUp)
        }}
      />
      <section className="split-right" style={{ width: `${100 - leftWidth}%` }} data-testid="trace-panel">
        {right}
      </section>
    </div>
  )
}
