'use client'

import { useEffect, useRef, useState } from 'react'

type QueryInputProps = {
  disabled: boolean
  lastQuery: string
  sessionId: string | null
  followUpHint: string | null
  onSubmit: (query: string) => void
}

export default function QueryInput({ disabled, lastQuery, sessionId, followUpHint, onSubmit }: QueryInputProps) {
  const [value, setValue] = useState('')
  const ref = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!disabled) {
      ref.current?.focus()
    }
  }, [disabled])

  function submit() {
    const question = value.trim()
    if (!question || disabled) return
    onSubmit(question)
    setValue('')
  }

  return (
    <div className="query-container" data-testid="query-container">
      <span className="query-prompt">&gt;</span>
      {sessionId ? (
        <span className="query-session-hint" data-testid="query-session-hint">
          Session {sessionId.slice(0, 8)}
        </span>
      ) : null}
      {followUpHint ? (
        <span className="query-followup-hint" data-testid="query-followup-hint">
          {followUpHint}
        </span>
      ) : null}
      <input
        ref={ref}
        className="query-input"
        data-testid="query-input"
        value={value}
        disabled={disabled}
        placeholder="Ask a macro research question..."
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault()
            submit()
          }
          if (event.key === 'Escape') {
            setValue('')
          }
          if (event.key === 'ArrowUp' && !value && lastQuery) {
            event.preventDefault()
            setValue(lastQuery)
          }
        }}
      />
      {value ? <span className="enter-hint">↵ Enter</span> : null}
      {value ? (
        <button
          type="button"
          className="query-submit"
          data-testid="query-submit"
          aria-label="Submit query"
          onClick={submit}
        >
          ›
        </button>
      ) : null}
    </div>
  )
}
