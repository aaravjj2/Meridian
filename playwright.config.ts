import { defineConfig } from '@playwright/test'

export default defineConfig({
  retries: 0,
  workers: 1,
  testDir: 'tests/e2e',
  reporter: 'list',
  webServer: {
    command:
      'MERIDIAN_MODE=demo PLAYWRIGHT=true concurrently "python -m uvicorn apps.api.main:app --port 8100" "MERIDIAN_API_BASE_URL=http://localhost:8100 npm run -w @meridian/web dev -- -p 3100"',
    url: 'http://localhost:3100',
    reuseExistingServer: false,
    timeout: 180000,
  },
  use: {
    video: 'on',
    trace: 'on',
    screenshot: 'on',
    baseURL: 'http://localhost:3100',
  },
})
