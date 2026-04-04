import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import QueryInput from '../../../apps/web/components/Terminal/QueryInput'

const templates = [
  {
    id: 'macro_outlook',
    title: 'Macro outlook',
    description: 'Baseline macro framing',
    framing: 'Macro first',
    query_class_default: 'macro_outlook',
    emphasis: ['cycle'],
    evaluation_expectations: ['conflicts'],
  },
  {
    id: 'event_probability_interpretation',
    title: 'Event probability interpretation',
    description: 'Event odds framing',
    framing: 'Odds first',
    query_class_default: 'event_probability',
    emphasis: ['pricing'],
    evaluation_expectations: ['timing risk'],
  },
] as const

describe('QueryInput', () => {
  it('renders session follow-up hints and submits query on Enter', () => {
    const onSubmit = vi.fn()
    const onTemplateChange = vi.fn()

    render(
      <QueryInput
        disabled={false}
        lastQuery="What changed in the macro outlook?"
        sessionId="sess-abc12345"
        followUpHint="Follow-up to prior question: What changed in the macro outlook?"
        templates={[...templates]}
        selectedTemplateId="macro_outlook"
        templateState="ready"
        templateError=""
        onTemplateChange={onTemplateChange}
        onSubmit={onSubmit}
      />
    )

    expect(screen.getByTestId('query-session-hint')).toHaveTextContent('Session sess-abc')
    expect(screen.getByTestId('query-followup-hint')).toHaveTextContent('Follow-up to prior question')
    expect(screen.getByTestId('query-template-select')).toHaveValue('macro_outlook')

    const input = screen.getByTestId('query-input')
    fireEvent.change(input, { target: { value: 'How does this affect tech?' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onSubmit).toHaveBeenCalledWith('How does this affect tech?')

    fireEvent.change(screen.getByTestId('query-template-select'), {
      target: { value: 'event_probability_interpretation' },
    })
    expect(onTemplateChange).toHaveBeenCalledWith('event_probability_interpretation')
  })

  it('recalls last query when ArrowUp is pressed on empty input', () => {
    const onSubmit = vi.fn()
    const onTemplateChange = vi.fn()

    render(
      <QueryInput
        disabled={false}
        lastQuery="Repeat prior query"
        sessionId={null}
        followUpHint={null}
        templates={[...templates]}
        selectedTemplateId="macro_outlook"
        templateState="ready"
        templateError=""
        onTemplateChange={onTemplateChange}
        onSubmit={onSubmit}
      />
    )

    const input = screen.getByTestId('query-input') as HTMLInputElement
    fireEvent.keyDown(input, { key: 'ArrowUp' })
    expect(input.value).toBe('Repeat prior query')
  })
})
