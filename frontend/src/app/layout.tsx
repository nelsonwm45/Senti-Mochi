import type { Metadata } from 'next'
import Navbar from './components/Navbar'
import './globals.css'
import { Providers } from '@/components/providers'

export const metadata: Metadata = {
  title: 'Secure Finance RAG',
  description: 'AI-powered financial document analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <Navbar />
          <main className="main-content">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  )
}
