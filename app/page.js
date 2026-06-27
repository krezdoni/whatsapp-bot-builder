'use client'

import { useState } from 'react'

const CHANNEL_LABELS = {
  threema: { name: 'Threema', desc: 'EU-native, no metadata exposure', badge: 'Most private' },
  whatsapp: { name: 'WhatsApp', desc: 'Convenient, metadata visible to Meta', badge: null },
}

export default function Home() {
  const [step, setStep] = useState('landing') // landing | channel | register | done
  const [channel, setChannel] = useState(null)
  const [identifier, setIdentifier] = useState('')
  const [consents, setConsents] = useState({
    profile_storage: false,
    messaging_channel: false,
    whatsapp_meta_exposure: false,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  const handleRegister = async () => {
    if (!identifier.trim()) { setError('Please enter your identifier.'); return }
    if (!consents.profile_storage || !consents.messaging_channel) {
      setError('Required consents must be accepted to continue.'); return
    }
    if (channel === 'whatsapp' && !consents.whatsapp_meta_exposure) {
      setError('WhatsApp metadata consent must be accepted.'); return
    }
    setLoading(true)
    setError('')
    try {
      const body = { messaging_channel: channel }
      if (channel === 'threema') body.threema_id = identifier
      else body.phone_number = identifier

      const res = await fetch(`${apiBase}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Registration failed') }
      const { access_token } = await res.json()
      localStorage.setItem('health_token', access_token)

      // Record consents
      const consentTypes = ['profile_storage', 'messaging_channel']
      if (channel === 'whatsapp') consentTypes.push('whatsapp_meta_exposure')
      for (const type of consentTypes) {
        await fetch(`${apiBase}/auth/consent`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access_token}` },
          body: JSON.stringify({ consent_type: type, granted: true }),
        })
      }
      setStep('done')
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  if (step === 'done') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-900 to-teal-900 text-white p-6">
        <div className="max-w-md text-center space-y-6">
          <div className="text-6xl">✓</div>
          <h1 className="text-3xl font-bold">You're set up</h1>
          <p className="text-green-200 text-lg">
            Your EU Health Companion is ready. Send your first message via {CHANNEL_LABELS[channel]?.name}.
          </p>
          {channel === 'threema' && (
            <p className="text-sm text-green-300 bg-green-900 bg-opacity-50 rounded-lg p-4">
              Add our Threema Gateway ID to your contacts to start chatting.
            </p>
          )}
          <p className="text-xs text-green-400">
            All your health data is encrypted and stored in Germany. You can export or delete it at any time from settings.
          </p>
        </div>
      </div>
    )
  }

  if (step === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 to-teal-900 text-white flex items-center justify-center p-6">
        <div className="max-w-md w-full space-y-6">
          <div>
            <button onClick={() => setStep('channel')} className="text-green-300 text-sm mb-4 hover:underline">← Back</button>
            <h2 className="text-2xl font-bold">Register with {CHANNEL_LABELS[channel]?.name}</h2>
            <p className="text-green-200 text-sm mt-1">Your data stays in the EU.</p>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              {channel === 'threema' ? 'Threema ID (e.g. *ABC123)' : 'Phone number (e.g. +4512345678)'}
            </label>
            <input
              type={channel === 'whatsapp' ? 'tel' : 'text'}
              value={identifier}
              onChange={e => setIdentifier(e.target.value)}
              placeholder={channel === 'threema' ? '*XXXXXXX' : '+4500000000'}
              className="w-full bg-white bg-opacity-10 border border-white border-opacity-20 rounded-lg px-4 py-3 text-white placeholder-green-400 focus:outline-none focus:ring-2 focus:ring-green-400"
            />
          </div>

          <div className="space-y-3 bg-white bg-opacity-5 rounded-lg p-4">
            <h3 className="font-semibold text-sm">Consent (required)</h3>

            <ConsentItem
              checked={consents.profile_storage}
              onChange={v => setConsents(c => ({ ...c, profile_storage: v }))}
              label="Health profile storage"
              desc="I consent to my health information being stored on EU servers (Hetzner Frankfurt, Germany), encrypted at rest."
            />
            <ConsentItem
              checked={consents.messaging_channel}
              onChange={v => setConsents(c => ({ ...c, messaging_channel: v }))}
              label="Messaging channel"
              desc={`I consent to receiving personalised health information via ${CHANNEL_LABELS[channel]?.name}.`}
            />
            {channel === 'whatsapp' && (
              <ConsentItem
                checked={consents.whatsapp_meta_exposure}
                onChange={v => setConsents(c => ({ ...c, whatsapp_meta_exposure: v }))}
                label="WhatsApp metadata acknowledgment"
                desc="I acknowledge that message metadata (sender, timestamp, length) is accessible to Meta Platforms Inc. (US). Health content is end-to-end encrypted and not shared with Meta."
                highlight
              />
            )}
          </div>

          {error && <p className="text-red-400 text-sm">{error}</p>}

          <button
            onClick={handleRegister}
            disabled={loading}
            className="w-full bg-green-500 hover:bg-green-400 text-white font-bold py-3 rounded-lg transition disabled:opacity-50"
          >
            {loading ? 'Setting up...' : 'Create my account'}
          </button>
        </div>
      </div>
    )
  }

  if (step === 'channel') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-900 to-teal-900 text-white flex items-center justify-center p-6">
        <div className="max-w-md w-full space-y-6">
          <div>
            <button onClick={() => setStep('landing')} className="text-green-300 text-sm mb-4 hover:underline">← Back</button>
            <h2 className="text-2xl font-bold">Choose your messaging channel</h2>
            <p className="text-green-200 text-sm mt-1">You can change this later.</p>
          </div>

          {Object.entries(CHANNEL_LABELS).map(([key, info]) => (
            <button
              key={key}
              onClick={() => { setChannel(key); setStep('register') }}
              className="w-full text-left bg-white bg-opacity-10 hover:bg-opacity-20 border border-white border-opacity-20 rounded-lg p-5 transition"
            >
              <div className="flex justify-between items-start">
                <span className="font-bold text-lg">{info.name}</span>
                {info.badge && (
                  <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded-full">{info.badge}</span>
                )}
              </div>
              <p className="text-green-200 text-sm mt-1">{info.desc}</p>
            </button>
          ))}
        </div>
      </div>
    )
  }

  // Landing
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 to-teal-900 text-white">
      <header className="max-w-5xl mx-auto px-6 py-5 flex justify-between items-center">
        <div className="font-bold text-xl tracking-tight">EU Health Companion</div>
        <div className="text-xs text-green-300 border border-green-700 px-3 py-1 rounded-full">GDPR-native</div>
      </header>

      <section className="max-w-3xl mx-auto px-6 py-20 text-center">
        <p className="text-green-300 text-sm font-medium mb-4 tracking-wide uppercase">Denmark & Germany</p>
        <h1 className="text-5xl md:text-6xl font-bold mb-6 leading-tight">
          Your health records.<br />
          <span className="text-green-300">In your language.</span><br />
          On your side.
        </h1>
        <p className="text-xl text-green-100 mb-10 max-w-2xl mx-auto">
          A personal health AI that understands your records, helps you prepare for doctor visits, and explains your lab results — all via the messaging app you already use.
        </p>
        <button
          onClick={() => setStep('channel')}
          className="bg-green-500 hover:bg-green-400 text-white font-bold px-10 py-4 rounded-lg text-lg transition"
        >
          Get started
        </button>
        <p className="mt-4 text-green-400 text-sm">No app download required · Works via Threema or WhatsApp</p>
      </section>

      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            icon="🔒"
            title="EU-native privacy"
            desc="All health data encrypted and stored in Hetzner Frankfurt, Germany. No US cloud."
          />
          <FeatureCard
            icon="🏥"
            title="Connects to your records"
            desc="Links to Sundhedsjournalen (DK) and ePA (DE) so your profile stays current."
          />
          <FeatureCard
            icon="💬"
            title="Works via messaging"
            desc="Ask questions, upload lab PDFs, prepare for appointments — all via Threema or WhatsApp."
          />
        </div>
      </section>

      <section className="max-w-3xl mx-auto px-6 py-12">
        <div className="bg-white bg-opacity-5 border border-white border-opacity-10 rounded-xl p-8">
          <h2 className="text-xl font-bold mb-4">What it can help with</h2>
          <ul className="space-y-3 text-green-100">
            {[
              '"What does my HbA1c of 6.8 mean?"',
              '"Can you prepare questions for my cardiology appointment?"',
              '"I got a letter from the hospital — can you explain it?"',
              '"What are the common side effects of Metformin?"',
              '"Show me my vaccination history."',
            ].map(q => (
              <li key={q} className="flex gap-3">
                <span className="text-green-400">→</span>
                <span className="italic text-sm">{q}</span>
              </li>
            ))}
          </ul>
          <p className="mt-6 text-xs text-green-400">
            This service provides health information, not medical advice. Always consult your doctor for clinical decisions.
          </p>
        </div>
      </section>

      <footer className="border-t border-white border-opacity-10 py-8 text-center text-green-500 text-xs mt-12">
        <p>EU Health Companion · All data stored in EU · Built for Denmark & Germany</p>
        <p className="mt-1">For urgent medical concerns, call 112 (EU) · 1813 (DK) · 116 117 (DE)</p>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-white bg-opacity-5 border border-white border-opacity-10 rounded-xl p-6">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="font-bold mb-2">{title}</h3>
      <p className="text-green-200 text-sm">{desc}</p>
    </div>
  )
}

function ConsentItem({ checked, onChange, label, desc, highlight = false }) {
  return (
    <label className={`flex gap-3 cursor-pointer ${highlight ? 'bg-yellow-900 bg-opacity-30 p-3 rounded-lg' : ''}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        className="mt-0.5 h-4 w-4 rounded accent-green-400 shrink-0"
      />
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-green-300 mt-0.5">{desc}</p>
      </div>
    </label>
  )
}
