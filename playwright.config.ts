import { defineConfig } from '@playwright/test'

export default defineConfig({
  retries: 0,
  workers: 1,
  testDir: 'tests/e2e',
  reporter: 'list',
  webServer: {
    command:
      'MERIDIAN_MODE=demo PLAYWRIGHT=true npx concurrently -k -s first "/home/aarav/Aarav/Meridian/.venv/bin/python -m uvicorn apps.api.main:app --port 8100" "MERIDIAN_API_BASE_URL=http://localhost:8100 PLAYWRIGHT=true npm run -w @meridian/web build && MERIDIAN_API_BASE_URL=http://localhost:8100 PLAYWRIGHT=true npm run -w @meridian/web start -- -p 3100"',
    url: 'http://localhost:3100',
    reuseExistingServer: false,
    timeout: 300000,
  },
  use: {
    video: 'on',
    trace: 'on',
    screenshot: 'on',
    baseURL: 'http://localhost:3100',
  },
})
