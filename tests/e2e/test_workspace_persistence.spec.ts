import { expect, test } from '@playwright/test'

test('workspace persistence: manage, compare, integrity, export, and continue', async ({ page }) => {
  await page.goto('/')

  await page.getByTestId('query-input').fill('What does the current yield curve shape imply for equities over the next 6 months?')
  await page.getByTestId('query-input').press('Enter')

  await expect(page.getByTestId('brief-complete')).toBeVisible({ timeout: 30000 })
  await page.getByTestId('claim-link-bull-1-inversion-easing').click()
  await expect(page.getByTestId('evidence-drilldown')).toBeVisible()

  await page.getByTestId('save-session-button').click()
  await expect(page.getByTestId('workspace-status')).toContainText('Saved session', { timeout: 15000 })
  await expect(page.getByTestId('workspace-item-0')).toBeVisible()
  await expect(page.getByTestId('workspace-evaluation-0')).toBeVisible()

  await page.getByTestId('query-input').fill('Continue from this session with an event-probability perspective.')
  await page.getByTestId('query-input').press('Enter')

  await expect(page.getByTestId('brief-complete')).toBeVisible({ timeout: 30000 })
  await page.getByTestId('save-session-button').click()
  await expect(page.getByTestId('workspace-item-1')).toBeVisible({ timeout: 15000 })

  const sessionIds = await page
    .locator('[data-testid^="workspace-item-"]')
    .evaluateAll((nodes) => nodes.map((node) => node.getAttribute('data-session-id')).filter(Boolean) as string[])
  expect(sessionIds.length).toBeGreaterThanOrEqual(2)

  await page.getByTestId('workspace-compare-left').selectOption(sessionIds[0])
  await page.getByTestId('workspace-compare-right').selectOption(sessionIds[1])
  await page.getByTestId('workspace-compare-run').click()
  await expect(page.getByTestId('workspace-compare-result')).toBeVisible({ timeout: 10000 })

  await page.getByTestId('workspace-verify-0').click()
  await expect(page.getByTestId('workspace-integrity-report')).toBeVisible({ timeout: 10000 })
  await expect(page.getByTestId('workspace-integrity-provenance')).toBeVisible()
  await expect(page.getByTestId('workspace-integrity-evaluation')).toBeVisible()
  await page.getByTestId('workspace-integrity-run-all').click()
  await expect(page.getByTestId('workspace-integrity-overview')).toBeVisible({ timeout: 10000 })

  await page.getByTestId('workspace-reopen-0').click()
  await expect(page.getByTestId('brief-complete')).toBeVisible({ timeout: 10000 })
  await expect(page.getByTestId('trace-step-0')).toBeVisible()
  await page.locator('[data-testid^="claim-link-"]').first().click()
  await expect(page.getByTestId('active-claim-id')).toBeVisible()
  await expect(page.getByTestId('source-preview-0')).toBeVisible()

  await page.getByTestId('workspace-export-current-json').click()
  await expect(page.getByTestId('workspace-status')).toContainText('Exported', { timeout: 10000 })
  await page.getByTestId('workspace-export-current-markdown').click()
  await expect(page.getByTestId('workspace-status')).toContainText('Exported', { timeout: 10000 })
  await page.getByTestId('workspace-export-current-bundle').click()
  await expect(page.getByTestId('workspace-status')).toContainText('bundle', { timeout: 10000 })

  await page.getByTestId('query-input').fill('Continue from this saved thread with a risk-off interpretation.')
  await page.getByTestId('query-input').press('Enter')

  await expect(page.getByTestId('brief-complete')).toBeVisible({ timeout: 30000 })
  await expect(page.getByTestId('query-session-hint')).toBeVisible()
  await expect(page.getByTestId('brief-followup-context')).toBeVisible()
})
