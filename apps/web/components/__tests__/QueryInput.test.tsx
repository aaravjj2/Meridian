import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import QueryInput from '../Terminal/QueryInput'

const templates = [
  {
    id: 'macro_outlook',
    title: 'Macro outlook',
    description: 'Macro baseline',
    framing: 'Macro first',
    query_class_default: 'macro_outlook',
    emphasis: ['cycle'],
    evaluation_expectations: ['conflicts'],
  },
  {
    id: 'event_probability_interpretation',
    title: 'Event probability interpretation',
    description: 'Event odds',
    framing: 'Odds first',
    query_class_default: 'event_probability',
    emphasis: ['pricing'],
    evaluation_expectations: ['timing risk'],
  },
] as const

type RenderOverrides = Partial<{
  disabled: boolean
  lastQuery: string
  sessionId: string | null
  followUpHint: string | null
  selectedTemplateId: 'macro_outlook' | 'event_probability_interpretation'
  templateState: 'loading' | 'ready' | 'error'
  templateError: string
  onTemplateChange: ReturnType<typeof vi.fn>
  onSubmit: ReturnType<typeof vi.fn>
}>

function renderQueryInput(overrides: RenderOverrides = {}) {
  const onTemplateChange = overrides.onTemplateChange ?? vi.fn()
  const onSubmit = overrides.onSubmit ?? vi.fn()

  render(
    <QueryInput
      disabled={overrides.disabled ?? false}
      lastQuery={overrides.lastQuery ?? ''}
      sessionId={overrides.sessionId ?? null}
      followUpHint={overrides.followUpHint ?? null}
      templates={[...templates]}
      selectedTemplateId={overrides.selectedTemplateId ?? 'macro_outlook'}
      templateState={overrides.templateState ?? 'ready'}
      templateError={overrides.templateError ?? ''}
      onTemplateChange={onTemplateChange}
      onSubmit={onSubmit}
    />
  )

  return { onTemplateChange, onSubmit }
}

describe('QueryInput', () => {
  it('renders input field with correct attributes', () => {
    renderQueryInput()

    const input = screen.getByTestId('query-input') as HTMLInputElement
    expect(input).toBeInTheDocument()
    expect(input.disabled).toBe(false)
    expect(input.placeholder).toBe('Ask a macro research question...')
    expect(screen.getByTestId('query-template-select')).toHaveValue('macro_outlook')
  })

  it('submits non-empty query on Enter key', async () => {
    const { onSubmit } = renderQueryInput()

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).toHaveBeenCalledWith('test question')
    expect(input).toHaveValue('')
  })

  it('does not submit empty query', async () => {
    const { onSubmit } = renderQueryInput()

    const input = screen.getByTestId('query-input')
    await userEvent.click(input)
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('does not submit whitespace-only query', async () => {
    const { onSubmit } = renderQueryInput()

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, '   ')
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('does not submit when disabled', async () => {
    const { onSubmit } = renderQueryInput({ disabled: true })

    const input = screen.getByTestId('query-input') as HTMLInputElement
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('shows enter hint and submit button when typing', async () => {
    renderQueryInput()

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test')

    expect(screen.getByText('↵ Enter')).toBeInTheDocument()
    expect(screen.getByTestId('query-submit')).toBeInTheDocument()
  })

  it('submits when submit button is clicked', async () => {
    const { onSubmit } = renderQueryInput()

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')

    await userEvent.click(screen.getByTestId('query-submit'))
    expect(onSubmit).toHaveBeenCalledWith('test question')
  })

  it('clears input on Escape key', async () => {
    renderQueryInput()

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Escape}')

    expect(input).toHaveValue('')
  })

  it('restores last query on ArrowUp when input is empty', async () => {
    renderQueryInput({ lastQuery: 'previous query' })

    const input = screen.getByTestId('query-input')
    await userEvent.keyboard('{ArrowUp}')

    expect(input).toHaveValue('previous query')
  })

  it('changes selected template from dropdown', async () => {
    const { onTemplateChange } = renderQueryInput()

    await userEvent.selectOptions(screen.getByTestId('query-template-select'), 'event_probability_interpretation')
    expect(onTemplateChange).toHaveBeenCalledWith('event_probability_interpretation')
  })
})