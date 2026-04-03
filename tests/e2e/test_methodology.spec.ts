import { expect, test } from '@playwright/test'

test('methodology page renders', async ({ page }) => {
  await page.goto('/methodology')

  await expect(page.getByTestId('methodology-page')).toBeVisible()
  await expect(page.getByTestId('methodology-heading-how')).toBeVisible()
  await expect(page.getByTestId('methodology-heading-data-sources')).toBeVisible()
})
