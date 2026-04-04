'use client'

import { useEffect, useRef, useState } from 'react'

import type { ResearchTemplateDefinition, ResearchTemplateId } from './types'

type QueryInputProps = {
  disabled: boolean
  lastQuery: string
  sessionId: string | null
  followUpHint: string | null
  templates: ResearchTemplateDefinition[]
  selectedTemplateId: ResearchTemplateId
  templateState: 'loading' | 'ready' | 'error'
  templateError: string
  onTemplateChange: (templateId: ResearchTemplateId) => void
  onSubmit: (query: string) => void
}

export default function QueryInput({
  disabled,
  lastQuery,
  sessionId,
  followUpHint,
  templates,
  selectedTemplateId,
  templateState,
  templateError,
  onTemplateChange,
  onSubmit,
}: QueryInputProps) {
  const [value, setValue] = useState('')
  const ref = useRef<HTMLInputElement>(null)
  const activeTemplate = templates.find((item) => item.id === selectedTemplateId) ?? templates[0] ?? null

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
      <select
        className="query-template-select"
        data-testid="query-template-select"
        value={selectedTemplateId}
        disabled={disabled || templateState === 'loading'}
        onChange={(event) => onTemplateChange(event.target.value as ResearchTemplateId)}
      >
        {templates.map((template) => (
          <option key={template.id} value={template.id}>
            {template.title}
          </option>
        ))}
      </select>
      {activeTemplate ? (
        <span className="query-template-hint" data-testid="query-template-hint" title={activeTemplate.framing}>
          {activeTemplate.query_class_default.toUpperCase()}
        </span>
      ) : null}
      {templateState === 'error' && templateError ? (
        <span className="query-template-error" data-testid="query-template-error" title={templateError}>
          Template fallback
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
