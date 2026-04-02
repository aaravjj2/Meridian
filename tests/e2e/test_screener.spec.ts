import { expect, test } from '@playwright/test'

test('screener: loads, sorts, filters, opens drawer', async ({ page }) => {
  await page.goto('/screener')
  await expect(page.getByTestId('screener-table')).toBeVisible()

  const rows = page.locator('[data-testid^="screener-row-"]')
  await expect(rows.first()).toBeVisible({ timeout: 5000 })
  expect(await rows.count()).toBeGreaterThanOrEqual(5)

  const beforeSort = await rows.first().getAttribute('data-testid')
  await page.getByTestId('sort-confidence').click()
  await expect(async () => {
    const afterSort = await rows.first().getAttribute('data-testid')
    expect(afterSort).not.toEqual(beforeSort)
  }).toPass()

  await page.getByTestId('filter-platform').selectOption('kalshi')
  const polymarketRows = page.locator('[data-testid^="screener-row-pm-"]')
  await expect(polymarketRows).toHaveCount(0)

  const firstRowId = await rows.first().getAttribute('data-testid')
  const id = firstRowId?.replace('screener-row-', '')
  await rows.first().click()

  await expect(page.getByTestId(`screener-drawer-${id}`)).toBeVisible()
  await expect(page.getByTestId('screener-drawer-explanation')).not.toBeEmpty()
})
