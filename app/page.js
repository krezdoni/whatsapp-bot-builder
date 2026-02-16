'use client'

import { useState } from 'react'
import StripeButton from './components/StripeButton'

export default function Home() {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleCheckout = async () => {
    if (!email) {
      alert('Please enter your email')
      return
    }
    setIsLoading(true)
    try {
      const res = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      const data = await res.json()
      if (data.url) {
        window.location.href = data.url
      }
    } catch (err) {
      alert('Error: ' + err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen text-white">
      {/* Header */}
      <header className="bg-black bg-opacity-50 border-b border-white border-opacity-20 sticky top-0">
        <nav className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold">🤖 WhatsApp Bot Builder</div>
          <div className="text-sm text-gray-200">Powered by OpenClaw</div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          Build Custom WhatsApp Bots in <span className="text-yellow-300">60 Seconds</span>
        </h1>
        <p className="text-xl text-gray-100 mb-8 max-w-2xl mx-auto">
          No coding required. Connect to OpenClaw. Handle customer support, lead qualification, applicant screening, and more.
        </p>
      </section>

      {/* Features Section */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white bg-opacity-10 backdrop-blur p-8 rounded-lg border border-white border-opacity-20">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-bold mb-4">No Code Required</h3>
            <p className="text-gray-100">Drag, drop, and configure. Anyone can build a bot.</p>
          </div>
          <div className="bg-white bg-opacity-10 backdrop-blur p-8 rounded-lg border border-white border-opacity-20">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-bold mb-4">Instant Setup</h3>
            <p className="text-gray-100">60 seconds from signup to your first bot running live.</p>
          </div>
          <div className="bg-white bg-opacity-10 backdrop-blur p-8 rounded-lg border border-white border-opacity-20">
            <div className="text-4xl mb-4">🔗</div>
            <h3 className="text-xl font-bold mb-4">OpenClaw Ready</h3>
            <p className="text-gray-100">Seamless integration with your Hetzner + WhatsApp setup.</p>
          </div>
        </div>

        {/* Use Cases */}
        <div className="bg-white bg-opacity-10 backdrop-blur p-12 rounded-lg border border-white border-opacity-20 mb-16">
          <h2 className="text-3xl font-bold mb-8 text-center">Perfect For</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="flex items-start gap-4">
              <span className="text-2xl">✅</span>
              <div>
                <h4 className="font-bold mb-2">Customer Support</h4>
                <p className="text-gray-100 text-sm">Automate FAQs, ticket routing, and escalations</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <span className="text-2xl">✅</span>
              <div>
                <h4 className="font-bold mb-2">Lead Qualification</h4>
                <p className="text-gray-100 text-sm">Qualify inbound sales leads 24/7</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <span className="text-2xl">✅</span>
              <div>
                <h4 className="font-bold mb-2">Applicant Screening</h4>
                <p className="text-gray-100 text-sm">Filter job applications automatically</p>
              </div>
            </div>
            <div className="flex items-start gap-4">
              <span className="text-2xl">✅</span>
              <div>
                <h4 className="font-bold mb-2">Appointment Booking</h4>
                <p className="text-gray-100 text-sm">Schedule meetings without back-and-forth</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="max-w-2xl mx-auto px-6 py-16">
        <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-black p-12 rounded-lg text-center">
          <h2 className="text-4xl font-bold mb-4">$9 One-Time</h2>
          <p className="text-lg mb-8 font-semibold">Launch unlimited bots. No monthly fees.</p>
          
          <div className="mb-8">
            <input
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 rounded-lg mb-4 font-semibold"
            />
            <button
              onClick={handleCheckout}
              disabled={isLoading}
              className="w-full bg-black text-white font-bold py-3 rounded-lg hover:bg-gray-800 transition disabled:opacity-50"
            >
              {isLoading ? 'Processing...' : 'Get Started Now →'}
            </button>
          </div>
          
          <p className="text-sm font-semibold">✓ 30-day money-back guarantee</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black bg-opacity-50 border-t border-white border-opacity-20 py-8 text-center text-gray-300 text-sm mt-20">
        <p>Built by HustlerBot • Powered by OpenClaw & Stripe</p>
      </footer>
    </div>
  )
}
