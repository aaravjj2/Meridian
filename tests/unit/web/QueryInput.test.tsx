import React from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import QueryInput from '../../../apps/web/components/Terminal/QueryInput'

describe('QueryInput', () => {
  it('renders session follow-up hints and submits query on Enter', () => {
    const onSubmit = vi.fn()

    render(
      <QueryInput
        disabled={false}
        lastQuery="What changed in the macro outlook?"
        sessionId="sess-abc12345"
        followUpHint="Follow-up to prior question: What changed in the macro outlook?"
        onSubmit={onSubmit}
      />
    )

    expect(screen.getByTestId('query-session-hint')).toHaveTextContent('Session sess-abc')
    expect(screen.getByTestId('query-followup-hint')).toHaveTextContent('Follow-up to prior question')

    const input = screen.getByTestId('query-input')
    fireEvent.change(input, { target: { value: 'How does this affect tech?' } })
    fireEvent.keyDown(input, { key: 'Enter' })

    expect(onSubmit).toHaveBeenCalledWith('How does this affect tech?')
  })

  it('recalls last query when ArrowUp is pressed on empty input', () => {
    const onSubmit = vi.fn()

    render(
      <QueryInput
        disabled={false}
        lastQuery="Repeat prior query"
        sessionId={null}
        followUpHint={null}
        onSubmit={onSubmit}
      />
    )

    const input = screen.getByTestId('query-input') as HTMLInputElement
    fireEvent.keyDown(input, { key: 'ArrowUp' })
    expect(input.value).toBe('Repeat prior query')
  })
})
