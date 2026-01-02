import type { Metadata } from 'next'
import Navbar from './components/Navbar'
import './globals.css'

export const metadata: Metadata = {
  title: 'Finance AI Platform',
  description: 'AI-powered financial advice',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main className="main-content">
          {children}
        </main>
      </body>
    </html>
  )
}
