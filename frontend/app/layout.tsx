import './globals.css'

export const metadata = {
  title: 'Feltabout',
  description: 'AI-guided communication preparation for difficult conversations',
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon.png', type: 'image/png', sizes: '32x32' },
      { url: '/favicon-64.png', type: 'image/png', sizes: '64x64' },
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
    shortcut: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
