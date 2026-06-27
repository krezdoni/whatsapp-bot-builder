import './globals.css'

export const metadata = {
  title: 'EU Health AI Companion',
  description: 'Your personal health AI assistant — private, EU-based, GDPR-compliant.',
  manifest: '/manifest.json',
  themeColor: '#1a6b4a',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
      </head>
      <body>{children}</body>
    </html>
  )
}
