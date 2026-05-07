import './globals.css'

export const metadata = {
  title: 'RelateFX',
  description: 'AI relationship facilitation platform',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
