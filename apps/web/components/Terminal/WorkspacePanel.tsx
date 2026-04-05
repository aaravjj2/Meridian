'use client'

import { useEffect, useMemo, useState } from 'react'

import type {
  ResearchBrief,
  ResearchCollection,
  ResearchCollectionSummary,
  ResearchReviewChecklist,
  ResearchThreadTimelineDetail,
  ResearchThesisDelta,
  SavedResearchSessionSummary,
  SessionRecaptureLineage,
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
  recaptureBusy: boolean
  comparisonBusy: boolean
  integrityBusy: boolean
  reviewBusy: boolean
  searchValue: string
  includeArchived: boolean
  queryClassFilter: ResearchBrief['query_class'] | 'all'
  comparisonResult: SessionComparison | null
  recaptureLineage: SessionRecaptureLineage | null
  integrityReport: SessionIntegrityReport | null
  reviewChecklist: ResearchReviewChecklist | null
  integrityOverview: { count: number; issueCount: number } | null
  statusMessage: string | null
  collectionState: 'loading' | 'ready' | 'error'
  collectionError: string
  collections: ResearchCollectionSummary[]
  activeCollection: ResearchCollection | null
  collectionBusy: boolean
  threadTimelineState: 'idle' | 'loading' | 'ready' | 'error'
  threadTimelineError: string
  threadTimeline: ResearchThreadTimelineDetail | null
  onSearchChange: (value: string) => void
  onToggleIncludeArchived: (value: boolean) => void
  onQueryClassFilterChange: (value: ResearchBrief['query_class'] | 'all') => void
  onRefresh: () => void
  onCollectionRefresh: () => void
  onCollectionCreate: (payload: { title: string; summary?: string | null; notes?: string | null }) => void
  onCollectionOpen: (collectionId: string) => void
  onCollectionUpdate: (
    collectionId: string,
    payload: { title?: string; summary?: string | null; notes?: string | null }
  ) => void
  onCollectionAddActiveSession: () => void
  onCollectionExportBundle: () => void
  onCollectionRemoveSession: (sessionId: string) => void
  onCollectionReorderSession: (sessionId: string, direction: 'up' | 'down') => void
  onThreadTimelineRefresh: () => void
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
  onRecapture: (savedId: string) => void
  onReview: (savedId: string) => void
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

function optionalTimestampLabel(value: string | null | undefined): string {
  if (!value) return 'n/a'
  return value.replace('T', ' ').replace('Z', ' UTC')
}

function compactText(value: string, limit = 140): string {
  const normalized = value.trim()
  if (normalized.length <= limit) {
    return normalized
  }
  return `${normalized.slice(0, limit - 1)}...`
}

function templateLabel(templateTitle: string | null | undefined, templateId: string | null | undefined): string {
  if (templateTitle && templateTitle.trim()) {
    return templateTitle
  }
  if (templateId && templateId.trim()) {
    return templateId.replace(/_/g, ' ')
  }
  return 'default template'
}

function thesisDeltaLabel(delta: ResearchThesisDelta | null | undefined): string {
  if (!delta) {
    return 'Delta unavailable.'
  }
  if (!delta.previous_session_id) {
    return `Baseline save | sig ${delta.delta_signature}`
  }

  return [
    `vs ${delta.previous_session_id}`,
    `thesis ${delta.thesis_changed ? 'changed' : 'same'}`,
    `confidence ${delta.confidence_changed ? 'changed' : 'same'}`,
    `claims +${delta.claim_ids_added.length}/-${delta.claim_ids_removed.length}`,
    `freshness dV/W ${delta.freshness_policy_violation_delta}/${delta.freshness_policy_warning_delta}`,
    `conflicts +${delta.conflict_ids_added.length}/-${delta.conflict_ids_removed.length}`,
    `evaluation ${delta.evaluation_changed ? 'changed' : 'same'}`,
  ].join(' | ')
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
  recaptureBusy,
  comparisonBusy,
  integrityBusy,
  reviewBusy,
  searchValue,
  includeArchived,
  queryClassFilter,
  comparisonResult,
  recaptureLineage,
  integrityReport,
  reviewChecklist,
  integrityOverview,
  statusMessage,
  collectionState,
  collectionError,
  collections,
  activeCollection,
  collectionBusy,
  threadTimelineState,
  threadTimelineError,
  threadTimeline,
  onSearchChange,
  onToggleIncludeArchived,
  onQueryClassFilterChange,
  onRefresh,
  onCollectionRefresh,
  onCollectionCreate,
  onCollectionOpen,
  onCollectionUpdate,
  onCollectionAddActiveSession,
  onCollectionExportBundle,
  onCollectionRemoveSession,
  onCollectionReorderSession,
  onThreadTimelineRefresh,
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
  onRecapture,
  onReview,
  onCompare,
  onVerifyIntegrity,
  onVerifyWorkspaceIntegrity,
}: WorkspacePanelProps) {
  const [compareLeftId, setCompareLeftId] = useState('')
  const [compareRightId, setCompareRightId] = useState('')
  const [newCollectionTitle, setNewCollectionTitle] = useState('')
  const [newCollectionSummary, setNewCollectionSummary] = useState('')
  const [newCollectionNotes, setNewCollectionNotes] = useState('')
  const [editCollectionTitle, setEditCollectionTitle] = useState('')
  const [editCollectionSummary, setEditCollectionSummary] = useState('')
  const [editCollectionNotes, setEditCollectionNotes] = useState('')

  const compareOptions = useMemo(
    () => sessions.map((session) => ({ id: session.id, label: session.label || session.question })),
    [sessions]
  )

  useEffect(() => {
    setEditCollectionTitle(activeCollection?.title ?? '')
    setEditCollectionSummary(activeCollection?.summary ?? '')
    setEditCollectionNotes(activeCollection?.notes ?? '')
  }, [activeCollection])

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

  function createCollectionFromForm(): void {
    const title = newCollectionTitle.trim()
    if (!title || collectionBusy) {
      return
    }
    onCollectionCreate({
      title,
      summary: newCollectionSummary.trim() || null,
      notes: newCollectionNotes.trim() || null,
    })
    setNewCollectionTitle('')
    setNewCollectionSummary('')
    setNewCollectionNotes('')
  }

  function saveCollectionDetails(): void {
    if (!activeCollection || collectionBusy) {
      return
    }
    const title = editCollectionTitle.trim()
    if (!title) {
      return
    }
    onCollectionUpdate(activeCollection.id, {
      title,
      summary: editCollectionSummary.trim() || null,
      notes: editCollectionNotes.trim() || null,
    })
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
          <button
            type="button"
            data-testid="workspace-review-active"
            onClick={() => {
              if (activeSavedSessionId) {
                onReview(activeSavedSessionId)
              }
            }}
            disabled={reviewBusy || !activeSavedSessionId}
          >
            {reviewBusy ? 'Reviewing...' : 'Review Active'}
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

      <div className="workspace-collections" data-testid="workspace-collections-panel">
        <div className="workspace-collections-header">
          <span className="block-label">COLLECTIONS</span>
          <button
            type="button"
            data-testid="workspace-collections-refresh"
            onClick={onCollectionRefresh}
            disabled={collectionBusy}
          >
            Refresh
          </button>
        </div>

        <div className="workspace-collections-create" data-testid="workspace-collections-create">
          <input
            type="text"
            value={newCollectionTitle}
            placeholder="Collection title"
            data-testid="workspace-collection-create-title"
            onChange={(event) => setNewCollectionTitle(event.target.value)}
          />
          <input
            type="text"
            value={newCollectionSummary}
            placeholder="Summary (optional)"
            data-testid="workspace-collection-create-summary"
            onChange={(event) => setNewCollectionSummary(event.target.value)}
          />
          <textarea
            value={newCollectionNotes}
            placeholder="Notes (optional)"
            data-testid="workspace-collection-create-notes"
            onChange={(event) => setNewCollectionNotes(event.target.value)}
          />
          <button
            type="button"
            data-testid="workspace-collection-create-submit"
            disabled={collectionBusy || !newCollectionTitle.trim()}
            onClick={createCollectionFromForm}
          >
            {collectionBusy ? 'Working...' : 'Create Collection'}
          </button>
        </div>

        {collectionState === 'loading' ? (
          <div className="workspace-state" data-testid="workspace-collections-loading">
            Loading collections...
          </div>
        ) : null}

        {collectionState === 'error' ? (
          <div className="workspace-state workspace-state-error" data-testid="workspace-collections-error">
            {collectionError || 'Failed to load collections.'}
          </div>
        ) : null}

        {collectionState === 'ready' && collections.length === 0 ? (
          <div className="workspace-state" data-testid="workspace-collections-empty">
            No collections yet.
          </div>
        ) : null}

        {collectionState === 'ready' && collections.length > 0 ? (
          <div className="workspace-collections-list" data-testid="workspace-collections-list">
            {collections.map((collection, idx) => {
              const isActive = activeCollection?.id === collection.id
              return (
                <button
                  key={collection.id}
                  type="button"
                  className={isActive ? 'workspace-collection-item workspace-collection-item-active' : 'workspace-collection-item'}
                  data-testid={`workspace-collection-open-${idx}`}
                  onClick={() => onCollectionOpen(collection.id)}
                >
                  <span>{collection.title}</span>
                  <span>{collection.session_count} session(s)</span>
                </button>
              )
            })}
          </div>
        ) : null}

        {activeCollection ? (
          <div className="workspace-collection-detail" data-testid="workspace-collection-detail">
            <p className="workspace-status" data-testid="workspace-collection-signature">
              Signature: {activeCollection.collection_signature}
            </p>
            <p className="workspace-status" data-testid="workspace-collection-timeline-signature">
              Timeline signature: {activeCollection.timeline_signature || 'n/a'}
            </p>
            <div className="workspace-collections-edit-grid">
              <input
                type="text"
                value={editCollectionTitle}
                placeholder="Collection title"
                data-testid="workspace-collection-edit-title"
                onChange={(event) => setEditCollectionTitle(event.target.value)}
              />
              <input
                type="text"
                value={editCollectionSummary}
                placeholder="Collection summary"
                data-testid="workspace-collection-edit-summary"
                onChange={(event) => setEditCollectionSummary(event.target.value)}
              />
              <textarea
                value={editCollectionNotes}
                placeholder="Collection notes"
                data-testid="workspace-collection-edit-notes"
                onChange={(event) => setEditCollectionNotes(event.target.value)}
              />
            </div>
            <div className="workspace-collections-detail-actions">
              <button
                type="button"
                data-testid="workspace-collection-save"
                disabled={collectionBusy || !editCollectionTitle.trim()}
                onClick={saveCollectionDetails}
              >
                Save Collection
              </button>
              <button
                type="button"
                data-testid="workspace-collection-add-active-session"
                disabled={collectionBusy || !activeSavedSessionId}
                onClick={onCollectionAddActiveSession}
              >
                Add Active Session
              </button>
              <button
                type="button"
                data-testid="workspace-collection-export-bundle"
                disabled={collectionBusy || exportBusy}
                onClick={onCollectionExportBundle}
              >
                Export Collection Bundle
              </button>
            </div>
            <p className="workspace-status" data-testid="workspace-collection-missing-count">
              Missing sessions: {activeCollection.missing_session_count}
            </p>

            {activeCollection.timeline.length === 0 ? (
              <div className="workspace-state" data-testid="workspace-collection-timeline-empty">
                Collection timeline is empty.
              </div>
            ) : (
              <div className="workspace-collection-timeline" data-testid="workspace-collection-timeline">
                {activeCollection.timeline.map((item, idx) => {
                  const label = item.label || item.question || item.session_id
                  const thesisState = item.thesis_state
                  return (
                    <article
                      key={`${item.session_id}-${idx}`}
                      className="workspace-collection-timeline-item"
                      data-testid={`workspace-collection-timeline-item-${idx}`}
                    >
                      <header className="workspace-collection-timeline-header">
                        <strong>{label}</strong>
                        <span>{savedAtLabel(item.saved_at || '')}</span>
                      </header>
                      <p className="workspace-item-meta">
                        {queryClassLabel(item.query_class)} | {templateLabel(item.template_title, item.template_id)} |{' '}
                        {item.evaluation_passed ? 'Eval PASS' : 'Eval n/a'}
                      </p>
                      {thesisState ? (
                        <p className="workspace-item-meta" data-testid={`workspace-collection-thesis-${idx}`}>
                          Thesis: {compactText(thesisState.thesis, 120)} | conf {thesisState.confidence}/5 | claims{' '}
                          {thesisState.claim_count} | freshness v/w {thesisState.freshness_policy_violation_count}/
                          {thesisState.freshness_policy_warning_count} | conflicts {thesisState.conflict_count}
                        </p>
                      ) : null}
                      {item.thesis_delta ? (
                        <p
                          className="workspace-item-snapshot-signature"
                          data-testid={`workspace-collection-delta-${idx}`}
                        >
                          {thesisDeltaLabel(item.thesis_delta)}
                        </p>
                      ) : null}
                      <p className="workspace-item-snapshot-signature">
                        Snapshot sig: {item.snapshot_signature ?? 'n/a'}
                      </p>
                      {!item.exists ? <p className="workspace-item-archived">Missing saved session</p> : null}
                      <div className="workspace-item-actions">
                        <button
                          type="button"
                          data-testid={`workspace-collection-reopen-${idx}`}
                          disabled={!item.exists || collectionBusy}
                          onClick={() => onReopen(item.session_id)}
                        >
                          Reopen
                        </button>
                        <button
                          type="button"
                          data-testid={`workspace-collection-move-up-${idx}`}
                          disabled={idx === 0 || collectionBusy}
                          onClick={() => onCollectionReorderSession(item.session_id, 'up')}
                        >
                          Move Up
                        </button>
                        <button
                          type="button"
                          data-testid={`workspace-collection-move-down-${idx}`}
                          disabled={idx === activeCollection.timeline.length - 1 || collectionBusy}
                          onClick={() => onCollectionReorderSession(item.session_id, 'down')}
                        >
                          Move Down
                        </button>
                        <button
                          type="button"
                          data-testid={`workspace-collection-remove-${idx}`}
                          disabled={collectionBusy}
                          onClick={() => onCollectionRemoveSession(item.session_id)}
                        >
                          Remove
                        </button>
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </div>
        ) : null}
      </div>

      <div className="workspace-thread-timeline" data-testid="workspace-thread-timeline-panel">
        <div className="workspace-collections-header">
          <span className="block-label">THREAD TIMELINE</span>
          <button
            type="button"
            data-testid="workspace-thread-timeline-refresh"
            onClick={onThreadTimelineRefresh}
            disabled={threadTimelineState === 'loading'}
          >
            {threadTimelineState === 'loading' ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {threadTimelineState === 'idle' ? (
          <div className="workspace-state" data-testid="workspace-thread-timeline-idle">
            Reopen or select a saved session to inspect thread evolution.
          </div>
        ) : null}

        {threadTimelineState === 'loading' ? (
          <div className="workspace-state" data-testid="workspace-thread-timeline-loading">
            Loading thread timeline...
          </div>
        ) : null}

        {threadTimelineState === 'error' ? (
          <div className="workspace-state workspace-state-error" data-testid="workspace-thread-timeline-error">
            {threadTimelineError || 'Failed to load thread timeline.'}
          </div>
        ) : null}

        {threadTimelineState === 'ready' && threadTimeline ? (
          <>
            <p className="workspace-status" data-testid="workspace-thread-signature">
              Thread {threadTimeline.thread_session_id} | timeline sig {threadTimeline.timeline_signature}
            </p>
            {threadTimeline.timeline.length === 0 ? (
              <div className="workspace-state" data-testid="workspace-thread-timeline-empty">
                No saved sessions in this thread yet.
              </div>
            ) : (
              <div className="workspace-collection-timeline" data-testid="workspace-thread-timeline-list">
                {threadTimeline.timeline.map((item, idx) => {
                  const label = item.label || item.question || item.session_id
                  const thesisState = item.thesis_state
                  return (
                    <article
                      key={`thread-${item.session_id}-${idx}`}
                      className="workspace-collection-timeline-item"
                      data-testid={`workspace-thread-timeline-item-${idx}`}
                    >
                      <header className="workspace-collection-timeline-header">
                        <strong>{label}</strong>
                        <span>{savedAtLabel(item.saved_at || '')}</span>
                      </header>
                      <p className="workspace-item-meta">
                        {queryClassLabel(item.query_class)} | {templateLabel(item.template_title, item.template_id)} |{' '}
                        {item.evaluation_passed ? 'Eval PASS' : 'Eval n/a'}
                      </p>
                      {thesisState ? (
                        <p className="workspace-item-meta" data-testid={`workspace-thread-thesis-${idx}`}>
                          Thesis: {compactText(thesisState.thesis, 120)} | conf {thesisState.confidence}/5 | claims{' '}
                          {thesisState.claim_count} | freshness v/w {thesisState.freshness_policy_violation_count}/
                          {thesisState.freshness_policy_warning_count} | conflicts {thesisState.conflict_count}
                        </p>
                      ) : null}
                      {item.thesis_delta ? (
                        <p className="workspace-item-snapshot-signature" data-testid={`workspace-thread-delta-${idx}`}>
                          {thesisDeltaLabel(item.thesis_delta)}
                        </p>
                      ) : null}
                      <p className="workspace-item-snapshot-signature">
                        Snapshot sig: {item.snapshot_signature ?? 'n/a'}
                      </p>
                      <div className="workspace-item-actions">
                        <button
                          type="button"
                          data-testid={`workspace-thread-reopen-${idx}`}
                          disabled={!item.exists}
                          onClick={() => onReopen(item.session_id)}
                        >
                          Reopen
                        </button>
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
          </>
        ) : null}
      </div>

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
            <div className="workspace-compare-drift" data-testid="workspace-compare-drift-panel">
              <p data-testid="workspace-compare-drift-signature">
                Drift signature: {comparisonResult.snapshot_drift.drift_signature}
              </p>
              <p data-testid="workspace-compare-drift-snapshot-id-count">
                Snapshot IDs changed: {comparisonResult.snapshot_drift.snapshot_ids_changed.length}
              </p>
              <p data-testid="workspace-compare-drift-freshness-count">
                Freshness changed: {comparisonResult.snapshot_drift.freshness_changed.length}
              </p>
              <p data-testid="workspace-compare-drift-source-set">
                Source set changed: {comparisonResult.snapshot_drift.source_set_changed ? 'yes' : 'no'}
              </p>
              <p data-testid="workspace-compare-drift-evaluation-signature">
                Evaluation signature changed: {comparisonResult.snapshot_drift.evaluation_signature_changed ? 'yes' : 'no'}
              </p>
              {comparisonResult.snapshot_drift.snapshot_ids_changed.length > 0 ? (
                <ul className="workspace-compare-drift-list" data-testid="workspace-compare-drift-snapshot-id-list">
                  {comparisonResult.snapshot_drift.snapshot_ids_changed.slice(0, 4).map((item, idx) => (
                    <li key={`${item.source_ref}-snapshot-${idx}`} data-testid={`workspace-compare-snapshot-id-change-${idx}`}>
                      {item.source_ref}: {item.left_snapshot_id ?? 'none'} {'->'} {item.right_snapshot_id ?? 'none'}
                    </li>
                  ))}
                </ul>
              ) : (
                <p data-testid="workspace-compare-snapshot-id-change-none">No snapshot id drift.</p>
              )}
              {comparisonResult.snapshot_drift.freshness_changed.length > 0 ? (
                <ul className="workspace-compare-drift-list" data-testid="workspace-compare-drift-freshness-list">
                  {comparisonResult.snapshot_drift.freshness_changed.slice(0, 4).map((item, idx) => (
                    <li key={`${item.source_ref}-freshness-${idx}`} data-testid={`workspace-compare-freshness-change-${idx}`}>
                      {item.source_ref}: {item.left_freshness ?? 'unknown'} {'->'} {item.right_freshness ?? 'unknown'}
                    </li>
                  ))}
                </ul>
              ) : (
                <p data-testid="workspace-compare-freshness-change-none">No freshness drift.</p>
              )}
            </div>
            <div className="workspace-compare-drift" data-testid="workspace-compare-conflict-panel">
              <p data-testid="workspace-compare-conflict-signature">
                Conflict drift signature: {comparisonResult.conflict_diffs.drift_signature}
              </p>
              <p data-testid="workspace-compare-conflict-resolved-count">
                Resolved conflicts: {comparisonResult.conflict_diffs.resolved.length}
              </p>
              <p data-testid="workspace-compare-conflict-unchanged-count">
                Unchanged conflicts: {comparisonResult.conflict_diffs.unchanged.length}
              </p>
              <p data-testid="workspace-compare-conflict-worsened-count">
                Worsened conflicts: {comparisonResult.conflict_diffs.worsened.length}
              </p>
              {[
                ...comparisonResult.conflict_diffs.worsened,
                ...comparisonResult.conflict_diffs.resolved,
                ...comparisonResult.conflict_diffs.unchanged,
              ].length > 0 ? (
                <ul className="workspace-compare-drift-list" data-testid="workspace-compare-conflict-list">
                  {[
                    ...comparisonResult.conflict_diffs.worsened,
                    ...comparisonResult.conflict_diffs.resolved,
                    ...comparisonResult.conflict_diffs.unchanged,
                  ]
                    .slice(0, 6)
                    .map((conflict, idx) => (
                      <li key={`${conflict.conflict_id}-${idx}`} data-testid={`workspace-compare-conflict-item-${idx}`}>
                        {conflict.state.toUpperCase()} {conflict.conflict_id}: claims 
                        {conflict.claim_delta ? 'changed' : 'stable'}, sources 
                        {conflict.source_delta ? 'changed' : 'stable'}, snapshots 
                        {conflict.snapshot_delta ? 'changed' : 'stable'}
                      </li>
                    ))}
                </ul>
              ) : (
                <p data-testid="workspace-compare-conflict-item-none">No conflict drift.</p>
              )}
            </div>
          </div>
        ) : null}
      </div>

      {recaptureLineage ? (
        <div className="workspace-recapture" data-testid="workspace-recapture-panel">
          <span className="block-label">RECAPTURE LINEAGE</span>
          <div className="workspace-recapture-result" data-testid="workspace-recapture-lineage">
            <p data-testid="workspace-recapture-source">Source session: {recaptureLineage.source_session_id}</p>
            <p data-testid="workspace-recapture-target">Recaptured session: {recaptureLineage.recaptured_session_id}</p>
            <p data-testid="workspace-recapture-mode">Mode: {recaptureLineage.recapture_mode}</p>
            <p data-testid="workspace-recapture-before-signature">
              Before snapshot signature: {recaptureLineage.before_snapshot_signature}
            </p>
            <p data-testid="workspace-recapture-after-signature">
              After snapshot signature: {recaptureLineage.after_snapshot_signature}
            </p>
            <p data-testid="workspace-recapture-snapshot-id-changes">
              Snapshot id changes: {recaptureLineage.snapshot_id_changes}
            </p>
            <p data-testid="workspace-recapture-source-set-changes">
              Source set changes: {recaptureLineage.source_set_changes}
            </p>
            {recaptureLineage.transitions.length > 0 ? (
              <ul className="workspace-recapture-transitions" data-testid="workspace-recapture-transition-list">
                {recaptureLineage.transitions.slice(0, 4).map((transition, idx) => (
                  <li key={`${transition.source_ref}-${idx}`} data-testid={`workspace-recapture-transition-${idx}`}>
                    {transition.source_ref}: {transition.before_snapshot_id ?? 'none'} {'->'}{' '}
                    {transition.after_snapshot_id ?? 'none'}
                  </li>
                ))}
              </ul>
            ) : (
              <p data-testid="workspace-recapture-transition-none">No snapshot id transitions.</p>
            )}
          </div>
        </div>
      ) : null}

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
            <p data-testid="workspace-integrity-freshness-policy">
              Freshness policy:{' '}
              {integrityReport.freshness_policy_valid
                ? 'compliant'
                : `${integrityReport.freshness_policy_violation_count} violation(s)`}
            </p>
            <p data-testid="workspace-integrity-snapshot">
              Snapshot provenance:{' '}
              {integrityReport.snapshot_complete
                ? integrityReport.snapshot_consistent
                  ? 'complete + consistent'
                  : 'complete but inconsistent'
                : 'missing metadata'}
            </p>
            <p data-testid="workspace-integrity-snapshot-summary">
              Snapshot summary: {integrityReport.snapshot_summary_present ? 'present' : 'missing'}
            </p>
            <p data-testid="workspace-integrity-snapshot-checksum">
              Snapshot checksum: {integrityReport.snapshot_checksum_complete ? 'complete' : 'incomplete'}
            </p>
            <p data-testid="workspace-integrity-evaluation">
              Evaluation:{' '}
              {integrityReport.evaluation_present
                ? integrityReport.evaluation_valid
                  ? 'valid'
                  : 'signature mismatch'
                : 'missing'}
            </p>
            {integrityReport.bundle_snapshot_signature ? (
              <p data-testid="workspace-integrity-snapshot-signature">
                Snapshot signature: {integrityReport.bundle_snapshot_signature}
              </p>
            ) : null}
            <p>Issues: {integrityReport.issues.length === 0 ? 'none' : integrityReport.issues.join('; ')}</p>
          </div>
        ) : null}
      </div>

      <div className="workspace-integrity" data-testid="workspace-review-panel">
        <span className="block-label">GUIDED REVIEW</span>
        {reviewChecklist ? (
          <div className="workspace-integrity-result" data-testid="workspace-review-result">
            <p data-testid="workspace-review-status">
              Status: {reviewChecklist.status.toUpperCase()} | passed {reviewChecklist.passed_count}/
              {reviewChecklist.total_count}
            </p>
            <p data-testid="workspace-review-summary">{reviewChecklist.summary}</p>
            <p className="workspace-item-snapshot-signature" data-testid="workspace-review-signature">
              Signature: {reviewChecklist.deterministic_signature}
            </p>
            <div className="evaluation-checks" data-testid="workspace-review-items">
              {reviewChecklist.items.map((item, idx) => (
                <div
                  key={`${item.check_id}-${idx}`}
                  className={item.passed ? 'evaluation-check evaluation-check-pass' : 'evaluation-check evaluation-check-fail'}
                  data-testid={`workspace-review-item-${idx}`}
                >
                  <strong>{item.title}</strong>
                  <span>{item.detail}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="workspace-status" data-testid="workspace-review-empty">
            Run Review on any saved session to audit claim linkage, freshness, provenance, evaluation, template metadata, and snapshot completeness.
          </p>
        )}
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
                <p className="workspace-item-meta">
                  Thread {session.session_id} | {templateLabel(session.template_title, session.template_id)}
                </p>
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
                {session.snapshot_kind_counts ? (
                  <p className="workspace-item-snapshot" data-testid={`workspace-snapshot-${idx}`}>
                    Snapshots f/c/l/d/u: {session.snapshot_kind_counts.fixture ?? 0}/
                    {session.snapshot_kind_counts.cache ?? 0}/
                    {session.snapshot_kind_counts.live_capture ?? 0}/
                    {session.snapshot_kind_counts.derived ?? 0}/
                    {session.snapshot_kind_counts.unknown ?? 0}
                  </p>
                ) : null}
                {session.state_label_counts ? (
                  <p className="workspace-item-snapshot" data-testid={`workspace-state-labels-${idx}`}>
                    States fixture/cached/live/derived/unknown: {session.state_label_counts.fixture ?? 0}/
                    {session.state_label_counts.cached ?? 0}/{session.state_label_counts.live ?? 0}/
                    {session.state_label_counts.derived ?? 0}/{session.state_label_counts.unknown ?? 0}
                  </p>
                ) : null}
                {session.latest_fetched_at || session.latest_cached_at || session.latest_generated_at ? (
                  <p className="workspace-item-meta" data-testid={`workspace-live-metadata-${idx}`}>
                    fetched {optionalTimestampLabel(session.latest_fetched_at)} | cached{' '}
                    {optionalTimestampLabel(session.latest_cached_at)} | generated{' '}
                    {optionalTimestampLabel(session.latest_generated_at)}
                  </p>
                ) : null}
                {session.snapshot_signature ? (
                  <p className="workspace-item-snapshot-signature" data-testid={`workspace-snapshot-signature-${idx}`}>
                    Snapshot sig: {session.snapshot_signature}
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
                    data-testid={`workspace-recapture-${idx}`}
                    onClick={() => onRecapture(session.id)}
                    disabled={recaptureBusy}
                  >
                    {recaptureBusy ? 'Recapturing...' : 'Recapture'}
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
                    data-testid={`workspace-review-${idx}`}
                    onClick={() => onReview(session.id)}
                    disabled={reviewBusy}
                  >
                    Review
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
