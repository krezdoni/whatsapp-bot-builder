'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell,
} from 'recharts'

// ─── Platform config ──────────────────────────────────────────────────────────

const P = {
  linkedin: {
    label: 'LinkedIn',
    color: '#0A66C2',
    dimColor: '#0A66C220',
    icon: (
      <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
  },
  instagram: {
    label: 'Instagram',
    color: '#E1306C',
    dimColor: '#E1306C20',
    icon: (
      <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
  },
  twitter: {
    label: 'X',
    color: '#e7e9ea',
    dimColor: '#e7e9ea20',
    icon: (
      <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.742l7.776-8.906L2.25 2.25h6.865l4.254 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  substack: {
    label: 'Substack',
    color: '#FF6719',
    dimColor: '#FF671920',
    icon: (
      <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor">
        <path d="M22.539 8.242H1.46V5.406h21.08v2.836zM1.46 10.812V24L12 18.11 22.54 24V10.812H1.46zM22.54 0H1.46v2.836h21.08V0z" />
      </svg>
    ),
  },
}

const METRICS = [
  { key: 'views', label: 'Views / Impressions', short: 'Views' },
  { key: 'likes', label: 'Likes / Reactions', short: 'Likes' },
  { key: 'shares', label: 'Shares / Reposts', short: 'Shares' },
  { key: 'saves', label: 'Saves / Bookmarks', short: 'Saves' },
  { key: 'comments', label: 'Comments', short: 'Comments' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmt(n) {
  if (n == null || isNaN(n)) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(Math.round(n))
}

function pct(n) {
  return n != null && n > 0 ? (n * 100).toFixed(1) + '%' : '—'
}

function isoToday() {
  return new Date().toISOString().slice(0, 10)
}
function isoFrom(days) {
  return new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10)
}

function relDate(str) {
  if (!str) return '—'
  const d = Math.floor((Date.now() - new Date(str)) / 86_400_000)
  if (d === 0) return 'today'
  if (d === 1) return 'yesterday'
  if (d < 7) return `${d}d ago`
  if (d < 30) return `${Math.floor(d / 7)}w ago`
  return `${Math.floor(d / 30)}mo ago`
}

function weekKey(dateStr) {
  if (!dateStr) return null
  const d = new Date(dateStr)
  const mon = new Date(d)
  mon.setDate(d.getDate() - ((d.getDay() + 6) % 7))
  return mon.toISOString().slice(0, 10)
}

// Group posts into weekly buckets and sum a metric per platform
function buildWeeklyChart(posts, metric) {
  const byWeek = {}
  posts.forEach((p) => {
    const wk = weekKey(p.publishedAt)
    if (!wk) return
    if (!byWeek[wk]) byWeek[wk] = { week: wk }
    byWeek[wk][p.platform] = (byWeek[wk][p.platform] ?? 0) + (p[metric] ?? 0)
  })
  return Object.values(byWeek).sort((a, b) => a.week.localeCompare(b.week))
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function PlatformBadge({ platform }) {
  const cfg = P[platform]
  if (!cfg) return null
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium"
      style={{ color: cfg.color, backgroundColor: cfg.dimColor }}
    >
      {cfg.icon} {cfg.label}
    </span>
  )
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      {color && <div className="w-1.5 h-1.5 rounded-full mb-3" style={{ backgroundColor: color }} />}
      <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-1">{label}</p>
      <p className="text-2xl font-bold text-white mb-0.5">{value}</p>
      {sub && <p className="text-slate-500 text-xs">{sub}</p>}
    </div>
  )
}

function PostRow({ post, rank, highlightMetric }) {
  const er = post.engagementRate
  const erClass = er > 0.05 ? 'text-emerald-400' : er > 0.02 ? 'text-yellow-400' : 'text-slate-500'
  const contentPreview = (post.content ?? '').slice(0, 80)

  return (
    <tr className="border-b border-slate-700/40 hover:bg-slate-700/25 transition-colors group">
      <td className="py-3 px-4 text-slate-600 text-xs tabular-nums">{rank}</td>
      <td className="py-3 px-4 w-[220px] max-w-[220px]">
        <p className="text-white text-sm leading-snug">
          {contentPreview}{(post.content?.length ?? 0) > 80 ? '…' : ''}
        </p>
        <p className="text-slate-600 text-xs mt-0.5">{relDate(post.publishedAt)}</p>
      </td>
      <td className="py-3 px-4">
        <PlatformBadge platform={post.platform} />
      </td>
      {METRICS.map(({ key }) => (
        <td
          key={key}
          className={`py-3 px-3 text-right font-mono text-sm tabular-nums ${
            key === highlightMetric ? 'text-white font-semibold' : 'text-slate-400'
          }`}
        >
          {fmt(post[key])}
        </td>
      ))}
      <td className="py-3 px-3 text-right">
        <span className={`text-xs font-semibold ${erClass}`}>{pct(er)}</span>
      </td>
      <td className="py-3 px-3 text-center">
        {post.url ? (
          <a
            href={post.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-600 hover:text-blue-400 transition text-xs opacity-0 group-hover:opacity-100"
          >
            ↗
          </a>
        ) : null}
      </td>
    </tr>
  )
}

function Skeleton({ rows = 6 }) {
  return Array.from({ length: rows }, (_, i) => (
    <tr key={i} className="border-b border-slate-700/40">
      <td colSpan={10} className="py-3.5 px-4">
        <div
          className="h-3.5 rounded bg-slate-700 animate-pulse"
          style={{ width: `${40 + ((i * 19) % 45)}%` }}
        />
      </td>
    </tr>
  ))
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 shadow-2xl text-xs">
      <p className="text-slate-400 mb-2 font-medium">{label}</p>
      {payload.map(({ name, value, color }) => (
        <p key={name} style={{ color }} className="flex justify-between gap-6">
          <span>{P[name]?.label ?? name}</span>
          <span className="font-semibold tabular-nums">{fmt(value)}</span>
        </p>
      ))}
    </div>
  )
}

// ─── Platform Totals Bar ──────────────────────────────────────────────────────

function PlatformSummaryBar({ posts, activePlatforms }) {
  const totals = {}
  activePlatforms.forEach((pl) => {
    const plPosts = posts.filter((p) => p.platform === pl)
    totals[pl] = {
      posts: plPosts.length,
      views: plPosts.reduce((s, p) => s + p.views, 0),
      likes: plPosts.reduce((s, p) => s + p.likes, 0),
      shares: plPosts.reduce((s, p) => s + p.shares, 0),
      saves: plPosts.reduce((s, p) => s + p.saves, 0),
    }
  })

  if (!activePlatforms.length) return null

  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${activePlatforms.length}, 1fr)` }}>
      {activePlatforms.map((pl) => {
        const cfg = P[pl]
        const t = totals[pl] ?? {}
        return (
          <div
            key={pl}
            className="bg-slate-800 rounded-xl p-4 border"
            style={{ borderColor: cfg.color + '40' }}
          >
            <div className="flex items-center gap-2 mb-3" style={{ color: cfg.color }}>
              {cfg.icon}
              <span className="text-sm font-semibold">{cfg.label}</span>
              <span className="ml-auto text-slate-500 text-xs">{t.posts} posts</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              {[['Views', t.views], ['Likes', t.likes], ['Shares', t.shares], ['Saves', t.saves]].map(([label, val]) => (
                <div key={label}>
                  <p className="text-slate-500">{label}</p>
                  <p className="text-white font-semibold tabular-nums">{fmt(val)}</p>
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ─── CSV Uploader ─────────────────────────────────────────────────────────────

function CsvUploader({ onImport }) {
  const [status, setStatus] = useState(null) // null | 'uploading' | 'ok' | 'error'
  const [message, setMessage] = useState('')

  async function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setStatus('uploading')
    setMessage('')
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/csv', { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok || data.error) {
        setStatus('error')
        setMessage(data.error ?? 'Upload failed')
      } else {
        setStatus('ok')
        setMessage(`Imported ${data.count} ${data.platform === 'twitter' ? 'X' : 'LinkedIn'} posts`)
        onImport(data.posts, data.platform)
      }
    } catch (err) {
      setStatus('error')
      setMessage(err.message)
    }
    e.target.value = ''
  }

  return (
    <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
      <label className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-lg text-xs font-medium cursor-pointer transition">
        <svg className="w-3.5 h-3.5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        Upload X / LinkedIn CSV
        <input type="file" accept=".csv" className="hidden" onChange={handleFile} />
      </label>
      {status === 'uploading' && <span className="text-slate-500 text-xs">Importing…</span>}
      {status === 'ok' && <span className="text-emerald-400 text-xs">{message}</span>}
      {status === 'error' && <span className="text-red-400 text-xs">{message}</span>}
    </div>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

const PAGE_SIZE = 15
const CSV_STORAGE_KEY = 'dashboard_csv_posts'

export default function Dashboard() {
  const [range, setRange] = useState('30')
  const [activePlatform, setActivePlatform] = useState('all')
  const [sortMetric, setSortMetric] = useState('views')
  const [page, setPage] = useState(1)

  const [apiPosts, setApiPosts] = useState([])
  const [csvPosts, setCsvPosts] = useState([])
  const [configuredPlatforms, setConfiguredPlatforms] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)

  // Persist CSV posts in localStorage so they survive page reload
  useEffect(() => {
    try {
      const stored = localStorage.getItem(CSV_STORAGE_KEY)
      if (stored) setCsvPosts(JSON.parse(stored))
    } catch {}
  }, [])

  function handleCsvImport(posts, platform) {
    setCsvPosts((prev) => {
      // Replace all posts for this platform, keep others
      const kept = prev.filter((p) => p.platform !== platform)
      const next = [...kept, ...posts]
      try { localStorage.setItem(CSV_STORAGE_KEY, JSON.stringify(next)) } catch {}
      return next
    })
  }

  const allPosts = useMemo(
    () => [...apiPosts, ...csvPosts].sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt)),
    [apiPosts, csvPosts]
  )

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    const from = isoFrom(parseInt(range, 10))
    const to = isoToday()
    try {
      const res = await fetch(`/api/posts?from=${from}&to=${to}`)
      if (!res.ok) throw new Error(`${res.status}`)
      const data = await res.json()
      setApiPosts(data.posts ?? [])
      setConfiguredPlatforms(
        Object.entries(data.config ?? {})
          .filter(([, v]) => v)
          .map(([k]) => k)
      )
      setLastRefresh(new Date())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [range])

  useEffect(() => { fetchAll() }, [fetchAll])
  useEffect(() => { setPage(1) }, [activePlatform, sortMetric])

  // Include CSV-sourced platforms in the tab list
  const allConfiguredPlatforms = useMemo(() => {
    const csv = [...new Set(csvPosts.map((p) => p.platform))]
    return [...new Set([...configuredPlatforms, ...csv])]
  }, [configuredPlatforms, csvPosts])

  // ── Filter + sort ──────────────────────────────────────────────────────────
  const visiblePosts = useMemo(() => {
    const filtered = activePlatform === 'all'
      ? allPosts
      : allPosts.filter((p) => p.platform === activePlatform)
    return [...filtered].sort((a, b) => (b[sortMetric] ?? 0) - (a[sortMetric] ?? 0))
  }, [allPosts, activePlatform, sortMetric])

  const pagedPosts = visiblePosts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const totalPages = Math.ceil(visiblePosts.length / PAGE_SIZE)

  // ── Totals for stat cards ──────────────────────────────────────────────────
  const totals = useMemo(() => {
    const base = { views: 0, likes: 0, shares: 0, saves: 0, comments: 0 }
    return visiblePosts.reduce((acc, p) => {
      METRICS.forEach(({ key }) => { acc[key] += p[key] ?? 0 })
      return acc
    }, base)
  }, [visiblePosts])

  // ── Weekly chart data ──────────────────────────────────────────────────────
  const chartData = useMemo(
    () => buildWeeklyChart(activePlatform === 'all' ? allPosts : allPosts.filter((p) => p.platform === activePlatform), sortMetric),
    [allPosts, activePlatform, sortMetric]
  )

  const activePlatformsForChart = activePlatform === 'all'
    ? allConfiguredPlatforms
    : [activePlatform]

  // ── Platform comparison bar data ───────────────────────────────────────────
  const comparisonData = useMemo(() => {
    return METRICS.map(({ key, short }) => {
      const row = { metric: short }
      allConfiguredPlatforms.forEach((pl) => {
        row[pl] = allPosts.filter((p) => p.platform === pl).reduce((s, p) => s + (p[key] ?? 0), 0)
      })
      return row
    })
  }, [allPosts, allConfiguredPlatforms])

  const tabPlatforms = ['all', ...allConfiguredPlatforms]

  return (
    <div className="min-h-screen bg-slate-900 text-white">

      {/* ── Nav ──────────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-slate-900/95 backdrop-blur border-b border-slate-700/70">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center gap-4 flex-wrap">
          <span className="font-bold text-base shrink-0">Content Analytics</span>

          {/* Platform tabs */}
          <div className="flex bg-slate-800 border border-slate-700 rounded-lg p-0.5 gap-0.5 flex-wrap">
            {tabPlatforms.map((pl) => {
              const cfg = pl === 'all' ? null : P[pl]
              const active = activePlatform === pl
              return (
                <button
                  key={pl}
                  onClick={() => setActivePlatform(pl)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                    active ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-slate-300'
                  }`}
                  style={active && cfg ? { color: cfg.color } : {}}
                >
                  {cfg?.icon}
                  {pl === 'all' ? 'All platforms' : cfg?.label}
                </button>
              )
            })}
          </div>

          <div className="flex items-center gap-2 ml-auto">
            {/* Range */}
            <div className="flex bg-slate-800 border border-slate-700 rounded-lg p-0.5 gap-0.5">
              {[['7', '7d'], ['30', '30d'], ['90', '90d']].map(([v, l]) => (
                <button
                  key={v}
                  onClick={() => setRange(v)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                    range === v ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-white'
                  }`}
                >
                  {l}
                </button>
              ))}
            </div>
            {/* Refresh */}
            <button
              onClick={fetchAll}
              title="Refresh"
              className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 transition"
            >
              <svg
                className={`w-3.5 h-3.5 text-slate-400 ${loading ? 'animate-spin' : ''}`}
                fill="none" stroke="currentColor" viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-7 space-y-6">

        {/* ── Setup panels ─────────────────────────────────────────────────── */}
        <div className="space-y-3">

          {/* Instagram setup (needs token) */}
          {!configuredPlatforms.includes('instagram') && (
            <div className="bg-pink-950/40 border border-pink-500/30 rounded-xl p-4 text-sm">
              <p className="font-semibold text-pink-300 mb-1">Connect Instagram (free)</p>
              <p className="text-pink-400/70 text-xs mb-2">Reads all your native posts — impressions, reach, likes, saves.</p>
              <ol className="text-pink-300/70 text-xs space-y-1 list-decimal ml-4 mb-3">
                <li>Go to <strong>developers.facebook.com</strong> → Create App → Consumer</li>
                <li>Add <strong>Instagram Graph API</strong> product to the app</li>
                <li>Connect your Instagram Business/Creator account</li>
                <li>Generate a User Access Token with <code className="bg-pink-900/40 px-1 rounded">instagram_basic, read_insights</code> scopes</li>
                <li>Exchange for a long-lived token (60 days) via the Token Debugger</li>
                <li>Add to <code className="bg-pink-900/40 px-1 rounded">.env.local</code>: <code className="bg-pink-900/40 px-1 rounded">INSTAGRAM_ACCESS_TOKEN=your_token</code></li>
              </ol>
              <p className="text-pink-400/50 text-xs">Your account must be a Business or Creator account (not personal).</p>
            </div>
          )}

          {/* CSV upload for X + LinkedIn native posts */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-4">
            <p className="font-semibold text-slate-300 text-sm mb-1">Import X &amp; LinkedIn posts via CSV</p>
            <p className="text-slate-500 text-xs mb-3">
              Since you post natively, export your analytics CSV and upload it here. Posts persist across reloads.
            </p>
            <div className="grid sm:grid-cols-2 gap-3 text-xs text-slate-500 mb-4">
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-white font-medium mb-1 flex items-center gap-1.5">
                  {P.twitter.icon} X Analytics
                </p>
                <p>analytics.twitter.com/about → <strong>Export data</strong> → Tweet activity → select date range → Export</p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <p className="text-white font-medium mb-1 flex items-center gap-1.5">
                  {P.linkedin.icon} LinkedIn Analytics
                </p>
                <p>linkedin.com/analytics/creator/content → <strong>Export</strong> button (top right)</p>
              </div>
            </div>
            <CsvUploader onImport={handleCsvImport} />
            {csvPosts.length > 0 && (
              <p className="text-slate-600 text-xs mt-2">
                {csvPosts.length} posts loaded from CSV
                <button
                  onClick={() => { setCsvPosts([]); localStorage.removeItem(CSV_STORAGE_KEY) }}
                  className="ml-3 text-red-500/60 hover:text-red-400 transition"
                >
                  Clear
                </button>
              </p>
            )}
          </div>
        </div>

        {/* ── Error banner ─────────────────────────────────────────────────── */}
        {error && (
          <div className="bg-red-950/60 border border-red-500/40 rounded-xl p-4 text-red-300 text-sm">
            <strong>Fetch error:</strong> {error}
          </div>
        )}

        {/* ── Stat cards ───────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {METRICS.map(({ key, short }) => (
            <StatCard
              key={key}
              label={short}
              value={loading ? '…' : fmt(totals[key])}
              sub={`${visiblePosts.length} posts`}
              color={activePlatform !== 'all' ? P[activePlatform]?.color : undefined}
            />
          ))}
        </div>

        {/* ── Per-platform breakdown ───────────────────────────────────────── */}
        {!loading && allConfiguredPlatforms.length > 1 && activePlatform === 'all' && (
          <PlatformSummaryBar
            posts={allPosts}
            activePlatforms={allConfiguredPlatforms}
          />
        )}

        {/* ── Charts row ───────────────────────────────────────────────────── */}
        <div className="grid lg:grid-cols-3 gap-5">

          {/* Weekly trend */}
          <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
                {P[sortMetric]?.label ?? sortMetric} — by week
              </h2>
              <select
                value={sortMetric}
                onChange={(e) => setSortMetric(e.target.value)}
                className="bg-slate-700 border border-slate-600 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none"
              >
                {METRICS.map((m) => <option key={m.key} value={m.key}>{m.short}</option>)}
              </select>
            </div>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="week"
                    tick={{ fill: '#475569', fontSize: 9 }}
                    tickFormatter={(d) => d?.slice(5)}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis tick={{ fill: '#475569', fontSize: 9 }} tickFormatter={fmt} tickLine={false} axisLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  {activePlatformsForChart.map((pl) => (
                    <Bar key={pl} dataKey={pl} stackId="a" fill={P[pl]?.color ?? '#64748b'} radius={pl === activePlatformsForChart.at(-1) ? [3, 3, 0, 0] : undefined} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[200px] flex items-center justify-center">
                {loading
                  ? <div className="w-full h-full rounded-lg bg-slate-700/40 animate-pulse" />
                  : <span className="text-slate-600 text-sm">No data for this range</span>}
              </div>
            )}
          </div>

          {/* Platform comparison */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
              Platform comparison
            </h2>
            {allConfiguredPlatforms.length > 0 && !loading ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={comparisonData}
                  layout="vertical"
                  margin={{ top: 0, right: 8, bottom: 0, left: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" tick={{ fill: '#475569', fontSize: 9 }} tickFormatter={fmt} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="metric" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} width={48} />
                  <Tooltip content={<ChartTooltip />} />
                  {allConfiguredPlatforms.map((pl) => (
                    <Bar key={pl} dataKey={pl} fill={P[pl]?.color ?? '#64748b'} radius={[0, 3, 3, 0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[200px] flex items-center justify-center">
                {loading
                  ? <div className="w-full h-full rounded-lg bg-slate-700/40 animate-pulse" />
                  : <span className="text-slate-600 text-sm">Connect platforms to compare</span>}
              </div>
            )}
          </div>
        </div>

        {/* ── Post table ───────────────────────────────────────────────────── */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div className="px-5 py-4 flex items-center justify-between gap-4 border-b border-slate-700">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              Posts {visiblePosts.length > 0 && <span className="text-slate-600 font-normal ml-1">({visiblePosts.length})</span>}
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-slate-600 text-xs hidden sm:block">Rank by</span>
              <select
                value={sortMetric}
                onChange={(e) => setSortMetric(e.target.value)}
                className="bg-slate-700 border border-slate-600 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {METRICS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[820px]">
              <thead>
                <tr className="border-b border-slate-700 text-slate-500 text-[10px] uppercase tracking-wider">
                  <th className="py-2.5 px-4 text-left w-8">#</th>
                  <th className="py-2.5 px-4 text-left">Content</th>
                  <th className="py-2.5 px-4 text-left">Platform</th>
                  {METRICS.map(({ key, short }) => (
                    <th
                      key={key}
                      className={`py-2.5 px-3 text-right cursor-pointer hover:text-slate-300 transition ${sortMetric === key ? 'text-white' : ''}`}
                      onClick={() => setSortMetric(key)}
                    >
                      {short} {sortMetric === key ? '↓' : ''}
                    </th>
                  ))}
                  <th className="py-2.5 px-3 text-right">Eng.%</th>
                  <th className="py-2.5 px-3 w-8" />
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <Skeleton rows={6} />
                ) : pagedPosts.length > 0 ? (
                  pagedPosts.map((p, i) => (
                    <PostRow
                      key={`${p.platform}-${p.id}-${i}`}
                      post={p}
                      rank={(page - 1) * PAGE_SIZE + i + 1}
                      highlightMetric={sortMetric}
                    />
                  ))
                ) : (
                  <tr>
                    <td colSpan={10} className="py-14 text-center text-slate-600">
                      {configuredPlatforms.length === 0
                        ? 'Add API keys above to start seeing your posts'
                        : 'No posts found for this range'}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="px-5 py-3 flex items-center justify-between border-t border-slate-700">
              <span className="text-slate-600 text-xs">{visiblePosts.length} posts</span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 text-xs disabled:opacity-30 hover:bg-slate-600 transition"
                >
                  ← Prev
                </button>
                <span className="text-slate-500 text-xs tabular-nums">{page} / {totalPages}</span>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 text-xs disabled:opacity-30 hover:bg-slate-600 transition"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Substack note ────────────────────────────────────────────────── */}
        {configuredPlatforms.includes('substack') && !process.env.SUBSTACK_SESSION_COOKIE && (
          <p className="text-slate-600 text-xs text-center">
            Substack shows reactions + comments only. Add <code className="bg-slate-800 px-1 rounded">SUBSTACK_SESSION_COOKIE</code> to unlock open rates and click stats.
          </p>
        )}

      </main>

      <footer className="border-t border-slate-700/40 py-5 text-center text-slate-700 text-xs mt-4">
        LinkedIn via AuthoredUp · Instagram + X via Zernio · Substack via unofficial API
      </footer>
    </div>
  )
}
