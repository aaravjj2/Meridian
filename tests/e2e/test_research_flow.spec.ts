import { expect, test } from '@playwright/test'

test('research flow: query to complete brief', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByTestId('mode-badge')).toContainText('DEMO')
  await expect(page.getByTestId('query-input')).toBeVisible()

  await page.getByTestId('query-input').fill('What does the current yield curve shape imply for equities over the next 6 months?')
  await page.getByTestId('query-input').press('Enter')

  await expect(page.getByTestId('brief-loading')).toBeVisible({ timeout: 1000 })

  await expect(page.getByTestId('trace-step-0')).toBeVisible({ timeout: 5000 })
  await expect(page.getByTestId('trace-step-4')).toBeVisible({ timeout: 15000 })

  await expect(page.getByTestId('brief-complete')).toBeVisible({ timeout: 30000 })
  await expect(page.getByTestId('brief-query-class')).toContainText('MACRO OUTLOOK')

  await expect(page.getByTestId('thesis-summary')).not.toBeEmpty()
  await expect(page.getByTestId('bull-case')).toBeVisible()
  await expect(page.getByTestId('bear-case')).toBeVisible()
  await expect(page.getByTestId('confidence-meter')).toBeVisible()
  await expect(page.getByTestId('source-list')).toBeVisible()
  await expect(page.getByTestId('trace-group-evidence-0')).toBeVisible()
  await expect(page.getByTestId('trace-group-analysis-2')).toBeVisible()

  const sources = page.locator('[data-testid^="source-item-"]')
  const sourceCount = await sources.count()
  expect(sourceCount).toBeGreaterThanOrEqual(3)

  await page.getByTestId('source-item-0').click()
  await expect(page.getByTestId('source-preview-0')).toBeVisible()
  await expect(page.getByTestId('source-claims-0')).toBeVisible()

  await page.getByTestId('query-input').fill('How should I interpret the event probability if inflation re-accelerates?')
  await page.getByTestId('query-input').press('Enter')

  await expect(page.getByTestId('brief-complete')).toBeVisible({ timeout: 30000 })
  await expect(page.getByTestId('query-session-hint')).toBeVisible()
  await expect(page.getByTestId('query-followup-hint')).toBeVisible()
  await expect(page.getByTestId('brief-followup-context')).toBeVisible()
  await expect(page.getByTestId('brief-query-class')).toContainText('EVENT PROBABILITY')
})
