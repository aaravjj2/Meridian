import { expect, test } from '@playwright/test'

test('smoke: homepage chrome renders', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByTestId('topbar')).toBeVisible()
  await expect(page.getByTestId('mode-badge')).toContainText('DEMO')
  await expect(page.getByTestId('regime-strip')).toBeVisible()
  await expect(page.getByTestId('query-input')).toBeVisible()

  await expect(page.getByTestId('regime-growth')).toBeVisible()
  await expect(page.getByTestId('regime-inflation')).toBeVisible()
  await expect(page.getByTestId('regime-monetary')).toBeVisible()
  await expect(page.getByTestId('regime-credit')).toBeVisible()
  await expect(page.getByTestId('regime-labor')).toBeVisible()
})
