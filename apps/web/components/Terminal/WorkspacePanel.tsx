'use client'

import type { SavedResearchSessionSummary } from './types'

type WorkspacePanelProps = {
  historyState: 'loading' | 'ready' | 'error'
  historyError: string
  sessions: SavedResearchSessionSummary[]
  activeSavedSessionId: string | null
  canSaveCurrent: boolean
  saveBusy: boolean
  exportBusy: boolean
  statusMessage: string | null
  onRefresh: () => void
  onSaveCurrent: () => void
  onExportCurrentJson: () => void
  onExportCurrentMarkdown: () => void
  onReopen: (savedId: string) => void
  onExportJson: (savedId: string) => void
  onExportMarkdown: (savedId: string) => void
}

function queryClassLabel(value: SavedResearchSessionSummary['query_class']): string {
  if (value === 'event_probability') return 'EVENT'
  if (value === 'ticker_macro') return 'TICKER'
  if (value === 'macro_outlook') return 'MACRO'
  return 'UNKNOWN'
}

function savedAtLabel(value: string): string {
  if (!value) return 'unknown'
  return value.replace('T', ' ').replace('Z', ' UTC')
}

export default function WorkspacePanel({
  historyState,
  historyError,
  sessions,
  activeSavedSessionId,
  canSaveCurrent,
  saveBusy,
  exportBusy,
  statusMessage,
  onRefresh,
  onSaveCurrent,
  onExportCurrentJson,
  onExportCurrentMarkdown,
  onReopen,
  onExportJson,
  onExportMarkdown,
}: WorkspacePanelProps) {
  return (
    <section className="workspace-panel" data-testid="workspace-panel">
      <div className="workspace-header">
        <span className="block-label">WORKSPACE</span>
        <div className="workspace-actions">
          <button type="button" data-testid="workspace-refresh-button" onClick={onRefresh}>
            Refresh
          </button>
          <button
            type="button"
            data-testid="save-session-button"
            onClick={onSaveCurrent}
            disabled={!canSaveCurrent || saveBusy}
          >
            {saveBusy ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            data-testid="workspace-export-current-json"
            onClick={onExportCurrentJson}
            disabled={!canSaveCurrent || exportBusy}
          >
            Export JSON
          </button>
          <button
            type="button"
            data-testid="workspace-export-current-markdown"
            onClick={onExportCurrentMarkdown}
            disabled={!canSaveCurrent || exportBusy}
          >
            Export MD
          </button>
        </div>
      </div>

      {statusMessage ? (
        <p className="workspace-status" data-testid="workspace-status">
          {statusMessage}
        </p>
      ) : null}

      {historyState === 'loading' ? (
        <div className="workspace-state" data-testid="workspace-loading">
          Loading saved sessions...
        </div>
      ) : null}

      {historyState === 'error' ? (
        <div className="workspace-state workspace-state-error" data-testid="workspace-error">
          {historyError || 'Failed to load saved sessions.'}
        </div>
      ) : null}

      {historyState === 'ready' && sessions.length === 0 ? (
        <div className="workspace-state" data-testid="workspace-empty">
          No saved sessions yet.
        </div>
      ) : null}

      {historyState === 'ready' && sessions.length > 0 ? (
        <div className="workspace-list" data-testid="workspace-list">
          {sessions.map((session, idx) => {
            const isActive = session.id === activeSavedSessionId
            return (
              <article
                key={session.id}
                className={isActive ? 'workspace-item workspace-item-active' : 'workspace-item'}
                data-testid={`workspace-item-${idx}`}
                data-session-id={session.id}
              >
                <header className="workspace-item-header">
                  <span>{queryClassLabel(session.query_class)}</span>
                  <span>{savedAtLabel(session.saved_at)}</span>
                </header>
                <p className="workspace-item-question">{session.question}</p>
                <p className="workspace-item-meta">Thread {session.session_id}</p>
                <div className="workspace-item-actions">
                  <button type="button" data-testid={`workspace-reopen-${idx}`} onClick={() => onReopen(session.id)}>
                    Reopen
                  </button>
                  <button
                    type="button"
                    data-testid={`workspace-export-json-${idx}`}
                    onClick={() => onExportJson(session.id)}
                    disabled={exportBusy}
                  >
                    JSON
                  </button>
                  <button
                    type="button"
                    data-testid={`workspace-export-markdown-${idx}`}
                    onClick={() => onExportMarkdown(session.id)}
                    disabled={exportBusy}
                  >
                    Markdown
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      ) : null}
    </section>
  )
}
