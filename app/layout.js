import './globals.css'

export const metadata = {
  title: 'WhatsApp Reply Bot Builder',
  description: 'Create custom WhatsApp bots in 60 seconds',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
