'use client'

import { useSearchParams } from 'next/navigation'

export default function Success() {
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('session_id')

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white">
      <div className="text-center max-w-md">
        <div className="text-6xl mb-6">✅</div>
        <h1 className="text-4xl font-bold mb-4">Payment Successful!</h1>
        <p className="text-lg mb-8">
          Check your email for setup instructions and your bot builder dashboard.
        </p>
        <a
          href="/"
          className="inline-block px-8 py-3 bg-white text-blue-600 font-bold rounded-lg hover:bg-gray-100 transition"
        >
          Back Home
        </a>
      </div>
    </div>
  )
}
