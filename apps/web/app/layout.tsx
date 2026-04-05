import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'

import StatusBar from '@/components/Layout/StatusBar'
import TopBar from '@/components/Layout/TopBar'

import '../styles/globals.css'

export const metadata: Metadata = {
  title: 'Meridian',
  description: 'Meridian GLM-5.1 research terminal',
  icons: {
    icon: '/favicon.svg',
  },
}

const inter = Inter({ subsets: ['latin'], variable: '--font-ui', display: 'swap' })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono', display: 'swap' })

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const isE2E = process.env.PLAYWRIGHT === 'true'

  return (
    <html lang="en">
      <body className={`${inter.variable} ${mono.variable}`} data-e2e={isE2E ? 'true' : 'false'}>
        <TopBar />
        <div className="app-root">{children}</div>
        <StatusBar />
      </body>
    </html>
  )
}
