'use client'

import { useEffect, useMemo, useRef, useState } from 'react'

import type { TraceEvent } from './types'

type TracePanelProps = {
  steps: TraceEvent[]
}

export default function TracePanel({ steps }: TracePanelProps) {
  const [autoScroll, setAutoScroll] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (autoScroll) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [steps, autoScroll])

  const counter = useMemo(() => {
    if (steps.length === 0) return '[0/0]'
    const last = steps[steps.length - 1]?.step ?? 0
    return `[${last + 1}/${last + 1}]`
  }, [steps])

  return (
    <div
      ref={containerRef}
      className="trace-panel"
      onScroll={(event) => {
        const target = event.currentTarget
        const nearBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 16
        setAutoScroll(nearBottom)
      }}
    >
      <div className="trace-header">
        <span>REASONING TRACE</span>
        <span>{counter}</span>
      </div>

      {steps.length === 0 ? <div className="trace-empty">Awaiting query…</div> : null}

      {steps.map((step, idx) => {
        const base = `trace-step-${step.step}`
        const typeId =
          step.type === 'tool_call'
            ? `trace-tool-call-${step.step}`
            : step.type === 'tool_result'
              ? `trace-tool-result-${step.step}`
              : step.type === 'reasoning'
                ? `trace-reasoning-${step.step}`
                : step.type === 'reflection'
                  ? `trace-reflection-${step.step}`
                  : undefined

        const staggerClass = idx < 5 ? `stagger-${idx + 1}` : ''

        return (
          <div
            key={`${step.step}-${step.type}`}
            className={`trace-row trace-row-${step.type} ${staggerClass}`}
            data-testid={base}
          >
            <div className="trace-row-main" data-testid={typeId}>
              <span className="trace-icon">
                {step.type === 'tool_call' ? '→' : null}
                {step.type === 'tool_result' ? '←' : null}
                {step.type === 'reasoning' ? '◈' : null}
                {step.type === 'reflection' ? '◎' : null}
                {step.type === 'brief_delta' ? '✦' : null}
                {step.type === 'complete' ? '✓' : null}
                {step.type === 'error' ? '!' : null}
              </span>

              {step.type === 'tool_call' ? (
                <details>
                  <summary>
                    <strong>{step.tool}</strong>
                    <span className="trace-ts">{step.ts}</span>
                  </summary>
                  <pre>{JSON.stringify(step.args ?? {}, null, 2)}</pre>
                </details>
              ) : null}

              {step.type === 'tool_result' ? (
                <details>
                  <summary>
                    <strong>{step.tool}</strong>
                    <span className="trace-ts">{step.ts}</span>
                  </summary>
                  <pre>{JSON.stringify(step.preview ?? [], null, 2)}</pre>
                </details>
              ) : null}

              {step.type === 'reasoning' ? <p>{step.text}</p> : null}

              {step.type === 'reflection' ? (
                <div className="trace-reflection-content">
                  <div className="trace-reflection-header">
                    <span className="trace-reflection-badge">REFLECTION</span>
                    <span>Step {step.content?.step || idx}</span>
                  </div>
                  <p>{step.content?.message || 'Evaluating progress...'}</p>
                  {step.content?.tools_used && (
                    <div className="trace-reflection-tools">
                      Tools used: {Array.isArray(step.content.tools_used)
                        ? step.content.tools_used.join(', ')
                        : step.content.tools_used}
                    </div>
                  )}
                </div>
              ) : null}

              {step.type === 'brief_delta' ? <p>{`${step.section}: ${step.text}`}</p> : null}
              {step.type === 'complete' ? (
                <p className="trace-complete" data-testid="trace-complete">
                  RESEARCH COMPLETE
                </p>
              ) : null}
              {step.type === 'error' ? <p className="trace-error">{step.message}</p> : null}
            </div>
          </div>
        )
      })}

      {!autoScroll && steps.length > 0 ? (
        <button
          type="button"
          className="trace-resume"
          onClick={() => {
            setAutoScroll(true)
            bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
          }}
        >
          ↓ Resume
        </button>
      ) : null}
      <div ref={bottomRef} />
    </div>
  )
}
