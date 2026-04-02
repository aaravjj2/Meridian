import { expect, test } from '@playwright/test'

test('methodology page renders', async ({ page }) => {
  await page.goto('/methodology')

  await expect(page.getByTestId('methodology-page')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'How Meridian Works' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Data Sources' })).toBeVisible()
})
