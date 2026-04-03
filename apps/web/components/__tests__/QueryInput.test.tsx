import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import QueryInput from '../Terminal/QueryInput'

describe('QueryInput', () => {
  it('renders input field with correct attributes', () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input') as HTMLInputElement
    expect(input).toBeInTheDocument()
    expect(input.disabled).toBe(false)
    expect(input.placeholder).toBe('Ask a macro research question...')
  })

  it('submits non-empty query on Enter key', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).toHaveBeenCalledWith('test question')
    expect(input).toHaveValue('')
  })

  it('does not submit empty query', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.click(input)
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('does not submit whitespace-only query', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, '   ')
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('does not submit when disabled', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={true} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input') as HTMLInputElement
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Enter}')

    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('clears input after successful submit', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Enter}')

    expect(input).toHaveValue('')
  })

  it('shows enter hint when typing', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test')

    const hint = screen.getByText('↵ Enter')
    expect(hint).toBeInTheDocument()
  })

  it('shows submit button when typing', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test')

    const button = screen.getByTestId('query-submit')
    expect(button).toBeInTheDocument()
  })

  it('submits when submit button is clicked', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')

    const button = screen.getByTestId('query-submit')
    await userEvent.click(button)

    expect(onSubmit).toHaveBeenCalledWith('test question')
  })

  it('clears input on Escape key', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'test question')
    await userEvent.keyboard('{Escape}')

    expect(input).toHaveValue('')
  })

  it('restores last query on ArrowUp when input is empty', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="previous query" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.keyboard('{ArrowUp}')

    expect(input).toHaveValue('previous query')
  })

  it('does not restore last query when input has content', async () => {
    const onSubmit = vi.fn()
    render(<QueryInput disabled={false} lastQuery="previous query" onSubmit={onSubmit} />)

    const input = screen.getByTestId('query-input')
    await userEvent.type(input, 'current ')
    await userEvent.keyboard('{ArrowUp}')

    expect(input).toHaveValue('current ')
  })
})
