'use client'

import { useMemo, useState } from 'react'

import type {
  ResearchBrief,
  SavedResearchSessionSummary,
  SessionComparison,
  SessionIntegrityReport,
} from './types'

type WorkspacePanelProps = {
  historyState: 'loading' | 'ready' | 'error'
  historyError: string
  sessions: SavedResearchSessionSummary[]
  activeSavedSessionId: string | null
  canSaveCurrent: boolean
  canExportCurrent: boolean
  saveBusy: boolean
  exportBusy: boolean
  mutationBusy: boolean
  comparisonBusy: boolean
  integrityBusy: boolean
  searchValue: string
  includeArchived: boolean
  queryClassFilter: ResearchBrief['query_class'] | 'all'
  comparisonResult: SessionComparison | null
  integrityReport: SessionIntegrityReport | null
  integrityOverview: { count: number; issueCount: number } | null
  statusMessage: string | null
  onSearchChange: (value: string) => void
  onToggleIncludeArchived: (value: boolean) => void
  onQueryClassFilterChange: (value: ResearchBrief['query_class'] | 'all') => void
  onRefresh: () => void
  onSaveCurrent: () => void
  onExportCurrentJson: () => void
  onExportCurrentMarkdown: () => void
  onExportCurrentBundle: () => void
  onReopen: (savedId: string) => void
  onExportJson: (savedId: string) => void
  onExportMarkdown: (savedId: string) => void
  onExportBundle: (savedId: string) => void
  onRename: (savedId: string, label: string | null) => void
  onArchive: (savedId: string, archived: boolean) => void
  onDelete: (savedId: string) => void
  onCompare: (leftId: string, rightId: string) => void
  onVerifyIntegrity: (savedId: string) => void
  onVerifyWorkspaceIntegrity: () => void
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
  canExportCurrent,
  saveBusy,
  exportBusy,
  mutationBusy,
  comparisonBusy,
  integrityBusy,
  searchValue,
  includeArchived,
  queryClassFilter,
  comparisonResult,
  integrityReport,
  integrityOverview,
  statusMessage,
  onSearchChange,
  onToggleIncludeArchived,
  onQueryClassFilterChange,
  onRefresh,
  onSaveCurrent,
  onExportCurrentJson,
  onExportCurrentMarkdown,
  onExportCurrentBundle,
  onReopen,
  onExportJson,
  onExportMarkdown,
  onExportBundle,
  onRename,
  onArchive,
  onDelete,
  onCompare,
  onVerifyIntegrity,
  onVerifyWorkspaceIntegrity,
}: WorkspacePanelProps) {
  const [compareLeftId, setCompareLeftId] = useState('')
  const [compareRightId, setCompareRightId] = useState('')

  const compareOptions = useMemo(
    () => sessions.map((session) => ({ id: session.id, label: session.label || session.question })),
    [sessions]
  )

  function promptRename(session: SavedResearchSessionSummary): void {
    const promptValue = window.prompt('Rename saved session (optional label)', session.label ?? '')
    if (promptValue === null) {
      return
    }
    const trimmed = promptValue.trim()
    onRename(session.id, trimmed ? trimmed : null)
  }

  function confirmDelete(session: SavedResearchSessionSummary): void {
    const confirmed = window.confirm(`Delete saved session ${session.id}?`)
    if (!confirmed) {
      return
    }
    onDelete(session.id)
  }

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
            disabled={!canExportCurrent || exportBusy}
          >
            Export JSON
          </button>
          <button
            type="button"
            data-testid="workspace-export-current-markdown"
            onClick={onExportCurrentMarkdown}
            disabled={!canExportCurrent || exportBusy}
          >
            Export MD
          </button>
          <button
            type="button"
            data-testid="workspace-export-current-bundle"
            onClick={onExportCurrentBundle}
            disabled={!canExportCurrent || exportBusy}
          >
            Export Bundle
          </button>
          <button
            type="button"
            data-testid="workspace-integrity-run-all"
            onClick={onVerifyWorkspaceIntegrity}
            disabled={integrityBusy}
          >
            {integrityBusy ? 'Verifying...' : 'Verify All'}
          </button>
        </div>
      </div>

      <div className="workspace-filters" data-testid="workspace-filters">
        <input
          type="search"
          value={searchValue}
          placeholder="Search saved sessions"
          data-testid="workspace-search-input"
          onChange={(event) => onSearchChange(event.target.value)}
        />
        <select
          data-testid="workspace-query-class-filter"
          value={queryClassFilter}
          onChange={(event) => onQueryClassFilterChange(event.target.value as ResearchBrief['query_class'] | 'all')}
        >
          <option value="all">All classes</option>
          <option value="macro_outlook">Macro outlook</option>
          <option value="event_probability">Event probability</option>
          <option value="ticker_macro">Ticker + macro</option>
        </select>
        <label className="workspace-archived-toggle" htmlFor="workspace-include-archived">
          <input
            id="workspace-include-archived"
            type="checkbox"
            checked={includeArchived}
            data-testid="workspace-include-archived"
            onChange={(event) => onToggleIncludeArchived(event.target.checked)}
          />
          Include archived
        </label>
      </div>

      {statusMessage ? (
        <p className="workspace-status" data-testid="workspace-status">
          {statusMessage}
        </p>
      ) : null}

      <div className="workspace-compare" data-testid="workspace-compare-panel">
        <span className="block-label">COMPARE</span>
        <div className="workspace-compare-controls">
          <select
            data-testid="workspace-compare-left"
            value={compareLeftId}
            onChange={(event) => setCompareLeftId(event.target.value)}
          >
            <option value="">Left session</option>
            {compareOptions.map((option) => (
              <option key={`left-${option.id}`} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <select
            data-testid="workspace-compare-right"
            value={compareRightId}
            onChange={(event) => setCompareRightId(event.target.value)}
          >
            <option value="">Right session</option>
            {compareOptions.map((option) => (
              <option key={`right-${option.id}`} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            data-testid="workspace-compare-run"
            onClick={() => onCompare(compareLeftId, compareRightId)}
            disabled={comparisonBusy || sessions.length < 2}
          >
            {comparisonBusy ? 'Comparing...' : 'Run Compare'}
          </button>
        </div>
        {comparisonResult ? (
          <div className="workspace-compare-result" data-testid="workspace-compare-result">
            <p data-testid="workspace-compare-signature">
              Signature: {comparisonResult.signature_match ? 'match' : 'different'}
            </p>
            <p data-testid="workspace-compare-claims">Claim changes: {comparisonResult.summary.total_claim_changes}</p>
            <p data-testid="workspace-compare-sources">Source changes: {comparisonResult.summary.total_source_changes}</p>
            <p data-testid="workspace-compare-fields">
              Changed fields:{' '}
              {comparisonResult.summary.changed_fields.length > 0
                ? comparisonResult.summary.changed_fields.join(', ')
                : 'none'}
            </p>
          </div>
        ) : null}
      </div>

      <div className="workspace-integrity" data-testid="workspace-integrity-panel">
        <span className="block-label">INTEGRITY</span>
        {integrityOverview ? (
          <p className="workspace-status" data-testid="workspace-integrity-overview">
            Checked {integrityOverview.count} sessions, issues in {integrityOverview.issueCount}
          </p>
        ) : null}
        {integrityReport ? (
          <div className="workspace-integrity-result" data-testid="workspace-integrity-report">
            <p>
              {integrityReport.id}: {integrityReport.signature_valid ? 'signature ok' : 'signature mismatch'}
            </p>
            <p data-testid="workspace-integrity-provenance">
              Provenance: {integrityReport.provenance_complete ? 'complete' : 'missing metadata'}
            </p>
            <p data-testid="workspace-integrity-freshness">
              Freshness: {integrityReport.freshness_valid ? 'resolved' : 'unknown present'}
            </p>
            <p data-testid="workspace-integrity-evaluation">
              Evaluation:{' '}
              {integrityReport.evaluation_present
                ? integrityReport.evaluation_valid
                  ? 'valid'
                  : 'signature mismatch'
                : 'missing'}
            </p>
            <p>Issues: {integrityReport.issues.length === 0 ? 'none' : integrityReport.issues.join('; ')}</p>
          </div>
        ) : null}
      </div>

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
                {session.label ? <p className="workspace-item-label">{session.label}</p> : null}
                <p className="workspace-item-question">{session.question}</p>
                <p className="workspace-item-meta">Thread {session.session_id}</p>
                {session.evaluation_passed !== undefined && session.evaluation_passed !== null ? (
                  <p
                    className={
                      session.evaluation_passed
                        ? 'workspace-item-evaluation workspace-item-evaluation-pass'
                        : 'workspace-item-evaluation workspace-item-evaluation-fail'
                    }
                    data-testid={`workspace-evaluation-${idx}`}
                  >
                    Eval {session.evaluation_passed ? 'PASS' : 'FAIL'}
                  </p>
                ) : null}
                {session.archived ? (
                  <p className="workspace-item-archived" data-testid={`workspace-archived-${idx}`}>
                    Archived
                  </p>
                ) : null}
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
                  <button
                    type="button"
                    data-testid={`workspace-export-bundle-${idx}`}
                    onClick={() => onExportBundle(session.id)}
                    disabled={exportBusy}
                  >
                    Bundle
                  </button>
                  <button
                    type="button"
                    data-testid={`workspace-verify-${idx}`}
                    onClick={() => onVerifyIntegrity(session.id)}
                    disabled={integrityBusy}
                  >
                    Verify
                  </button>
                  <button
                    type="button"
                    data-testid={`workspace-rename-${idx}`}
                    onClick={() => promptRename(session)}
                    disabled={mutationBusy}
                  >
                    Rename
                  </button>
                  <button
                    type="button"
                    data-testid={`workspace-archive-${idx}`}
                    onClick={() => onArchive(session.id, !session.archived)}
                    disabled={mutationBusy}
                  >
                    {session.archived ? 'Unarchive' : 'Archive'}
                  </button>
                  <button
                    type="button"
                    data-testid={`workspace-delete-${idx}`}
                    onClick={() => confirmDelete(session)}
                    disabled={mutationBusy}
                  >
                    Delete
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
