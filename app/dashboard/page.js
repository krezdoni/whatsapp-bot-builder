'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'

// ─── Formatters ───────────────────────────────────────────────────────────────

function fmt(n) {
  if (n == null) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

function pct(n) {
  return n != null ? (n * 100).toFixed(1) + '%' : '—'
}

function relativeDate(dateStr) {
  if (!dateStr) return '—'
  const days = Math.floor((Date.now() - new Date(dateStr)) / 86_400_000)
  if (days === 0) return 'today'
  if (days === 1) return 'yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return `${Math.floor(days / 30)}mo ago`
}

function isoToday() {
  return new Date().toISOString().slice(0, 10)
}

function isoFrom(days) {
  return new Date(Date.now() - days * 86_400_000).toISOString().slice(0, 10)
}

// ─── Pull LinkedIn-specific analytics from a post object ──────────────────────

function liAnalytics(post) {
  const li = post.platformAnalytics?.find(p => p.platform === 'linkedin')
  return li?.analytics ?? post.analytics ?? {}
}

// ─── Stat Card ────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, highlight }) {
  return (
    <div className={`rounded-xl p-5 border ${highlight ? 'bg-slate-800 border-blue-500/40' : 'bg-slate-800 border-slate-700'}`}>
      <p className="text-slate-400 text-xs font-semibold uppercase tracking-widest mb-1">{label}</p>
      <p className="text-3xl font-bold text-white mb-1">{value}</p>
      {sub && <p className="text-slate-500 text-sm">{sub}</p>}
    </div>
  )
}

// ─── Post table row ───────────────────────────────────────────────────────────

function PostRow({ post, rank }) {
  const a = liAnalytics(post)
  const li = post.platformAnalytics?.find(p => p.platform === 'linkedin')
  const preview = (post.content ?? '').slice(0, 90)
  const er = a.engagementRate
  const erClass = er > 0.05 ? 'text-emerald-400' : er > 0.02 ? 'text-yellow-400' : 'text-slate-500'

  return (
    <tr className="border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors">
      <td className="py-3 px-4 text-slate-500 text-sm tabular-nums">{rank}</td>
      <td className="py-3 px-4 max-w-[280px]">
        <p className="text-white text-sm leading-snug">
          {preview}{(post.content?.length ?? 0) > 90 ? '…' : ''}
        </p>
        <p className="text-slate-500 text-xs mt-0.5">{relativeDate(post.publishedAt)}</p>
      </td>
      <td className="py-3 px-4 text-right font-mono text-sm text-white tabular-nums">{fmt(a.impressions)}</td>
      <td className="py-3 px-4 text-right font-mono text-sm text-white tabular-nums">{fmt(a.reach)}</td>
      <td className="py-3 px-4 text-right font-mono text-sm text-white tabular-nums">{fmt(a.likes)}</td>
      <td className="py-3 px-4 text-right font-mono text-sm text-white tabular-nums">{fmt(a.comments)}</td>
      <td className="py-3 px-4 text-right font-mono text-sm text-white tabular-nums">{fmt(a.shares)}</td>
      <td className="py-3 px-4 text-right font-mono text-sm text-white tabular-nums">{fmt(a.clicks)}</td>
      <td className="py-3 px-4 text-right">
        <span className={`text-sm font-semibold ${erClass}`}>{pct(er)}</span>
      </td>
      <td className="py-3 px-4 text-center">
        {li?.platformPostUrl ? (
          <a
            href={li.platformPostUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block px-2 py-0.5 rounded bg-slate-700 hover:bg-slate-600 text-blue-400 text-xs transition"
          >
            View
          </a>
        ) : '—'}
      </td>
    </tr>
  )
}

// ─── Skeleton loader ──────────────────────────────────────────────────────────

function Skeleton({ rows = 5 }) {
  return Array.from({ length: rows }, (_, i) => (
    <tr key={i} className="border-b border-slate-700/50">
      <td colSpan={10} className="py-3.5 px-4">
        <div
          className="h-3.5 rounded bg-slate-700 animate-pulse"
          style={{ width: `${45 + ((i * 17) % 40)}%` }}
        />
      </td>
    </tr>
  ))
}

// ─── Best-time heatmap ────────────────────────────────────────────────────────

const DAYS_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function BestTimeHeatmap({ data }) {
  if (!data?.length) {
    return (
      <p className="text-slate-600 text-sm py-4">
        No best-time data yet — more posts needed to generate insights.
      </p>
    )
  }

  const grid = Array.from({ length: 7 }, () => Array(24).fill(0))
  let max = 0
  data.forEach(({ dayOfWeek, hour, engagementScore }) => {
    const d = DAYS_SHORT.indexOf(dayOfWeek)
    if (d >= 0 && hour >= 0 && hour < 24) {
      grid[d][hour] = engagementScore ?? 0
      if ((engagementScore ?? 0) > max) max = engagementScore
    }
  })

  const cellColor = (score) => {
    const t = max > 0 ? score / max : 0
    if (t > 0.8) return 'bg-blue-500'
    if (t > 0.6) return 'bg-blue-600'
    if (t > 0.4) return 'bg-blue-800'
    if (t > 0.15) return 'bg-blue-950'
    return 'bg-slate-700/40'
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[580px]">
        <div className="flex mb-1 ml-12">
          {Array.from({ length: 24 }, (_, h) => (
            <div key={h} className="flex-1 text-center text-slate-600 text-[9px]">
              {h % 6 === 0 ? `${h}h` : ''}
            </div>
          ))}
        </div>
        {DAYS_SHORT.map((day, di) => (
          <div key={day} className="flex items-center mb-1">
            <span className="w-12 text-slate-500 text-xs pr-2 text-right shrink-0">{day}</span>
            {Array.from({ length: 24 }, (_, h) => (
              <div
                key={h}
                title={`${day} ${h}:00 — score: ${grid[di][h].toFixed(2)}`}
                className={`flex-1 h-5 mx-px rounded-sm ${cellColor(grid[di][h])} cursor-default transition-colors`}
              />
            ))}
          </div>
        ))}
        <div className="flex items-center gap-1.5 mt-4 ml-12">
          <span className="text-slate-600 text-xs mr-1">Less</span>
          {['bg-slate-700/40', 'bg-blue-950', 'bg-blue-800', 'bg-blue-600', 'bg-blue-500'].map((c, i) => (
            <div key={i} className={`w-4 h-4 rounded-sm ${c}`} />
          ))}
          <span className="text-slate-600 text-xs ml-1">More</span>
        </div>
      </div>
    </div>
  )
}

// ─── Custom chart tooltip ─────────────────────────────────────────────────────

const ChartTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-slate-800 border border-slate-600 rounded-xl px-4 py-3 shadow-2xl text-xs">
      <p className="text-slate-400 mb-2">{label}</p>
      {payload.map(({ name, value, color }) => (
        <p key={name} style={{ color }} className="flex justify-between gap-4">
          <span>{name}</span>
          <span className="font-semibold tabular-nums">{fmt(value)}</span>
        </p>
      ))}
    </div>
  )
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

const SORT_OPTIONS = [
  { label: 'Impressions', value: 'impressions' },
  { label: 'Engagement', value: 'engagement' },
  { label: 'Likes', value: 'likes' },
  { label: 'Comments', value: 'comments' },
  { label: 'Shares', value: 'shares' },
  { label: 'Clicks', value: 'clicks' },
  { label: 'Date', value: 'date' },
]

const PAGE_SIZE = 10

export default function LinkedInDashboard() {
  const [range, setRange] = useState('30')
  const [sortBy, setSortBy] = useState('impressions')
  const [page, setPage] = useState(1)

  const [posts, setPosts] = useState([])
  const [dailyMetrics, setDailyMetrics] = useState([])
  const [bestTime, setBestTime] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [error, setError] = useState(null)

  const fetchAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    const from = isoFrom(parseInt(range, 10))
    const to = isoToday()
    const qs = `from=${from}&to=${to}&platform=linkedin`

    try {
      const [analyticsRes, dailyRes, bestTimeRes] = await Promise.all([
        fetch(`/api/linkedin/analytics?${qs}&sort=${sortBy}&limit=200`),
        fetch(`/api/linkedin/daily-metrics?${qs}`),
        fetch(`/api/linkedin/best-time?platform=linkedin`),
      ])

      if (!analyticsRes.ok) {
        const err = await analyticsRes.json().catch(() => ({}))
        throw new Error(err.error ?? `Analytics ${analyticsRes.status}`)
      }

      const analytics = await analyticsRes.json()
      const daily = dailyRes.ok ? await dailyRes.json() : {}
      const bt = bestTimeRes.ok ? await bestTimeRes.json() : {}

      setPosts(analytics.data ?? analytics.posts ?? [])
      setDailyMetrics(daily.metrics ?? [])
      setBestTime(bt.bestTimes ?? [])
      setLastRefresh(new Date())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [range, sortBy])

  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  // ── Aggregate stats ────────────────────────────────────────────────────────
  const totals = posts.reduce(
    (acc, p) => {
      const a = liAnalytics(p)
      acc.impressions += a.impressions ?? 0
      acc.likes += a.likes ?? 0
      acc.comments += a.comments ?? 0
      acc.clicks += a.clicks ?? 0
      acc.engagementSum += a.engagementRate ?? 0
      return acc
    },
    { impressions: 0, likes: 0, comments: 0, clicks: 0, engagementSum: 0 }
  )
  const avgEngagement = posts.length ? totals.engagementSum / posts.length : 0

  const topPost = posts[0]
  const topPostImpressions = topPost ? (liAnalytics(topPost).impressions ?? 0) : 0

  // ── Post table pagination ──────────────────────────────────────────────────
  const pagedPosts = posts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const totalPages = Math.ceil(posts.length / PAGE_SIZE)

  // ── Reactions bar data (top 10 posts) ─────────────────────────────────────
  const reactionBarData = posts.slice(0, 10).map((p, i) => {
    const a = liAnalytics(p)
    return {
      name: `P${i + 1}`,
      Likes: a.likes ?? 0,
      Comments: a.comments ?? 0,
      Shares: a.shares ?? 0,
    }
  })

  return (
    <div className="min-h-screen bg-slate-900 text-white">

      {/* ── Nav ──────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-slate-900/90 backdrop-blur border-b border-slate-700/80">
        <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            {/* LinkedIn logo */}
            <svg className="w-6 h-6 shrink-0" viewBox="0 0 24 24" fill="#0A66C2">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
            </svg>
            <span className="font-bold text-base">LinkedIn Analytics</span>
            {lastRefresh && (
              <span className="hidden sm:block text-slate-600 text-xs ml-1">
                Updated {lastRefresh.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="flex bg-slate-800 border border-slate-700 rounded-lg p-0.5 gap-0.5">
              {[['7', '7d'], ['30', '30d'], ['90', '90d']].map(([v, label]) => (
                <button
                  key={v}
                  onClick={() => { setRange(v); setPage(1) }}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                    range === v
                      ? 'bg-blue-600 text-white shadow'
                      : 'text-slate-400 hover:text-white hover:bg-slate-700'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>

            <button
              onClick={fetchAll}
              title="Refresh data"
              className="p-2 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 transition"
            >
              <svg className={`w-4 h-4 text-slate-400 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-7">

        {/* ── Error banner ───────────────────────────────────────────────── */}
        {error && (
          <div className="bg-red-950/60 border border-red-500/40 rounded-xl p-4 text-red-300 text-sm flex gap-3 items-start">
            <svg className="w-4 h-4 mt-0.5 shrink-0 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <strong>API error:</strong> {error}
              <br />
              <span className="text-red-400/70 text-xs">
                Set <code className="bg-red-900/50 px-1 rounded">ZERNIO_API_KEY</code> in{' '}
                <code className="bg-red-900/50 px-1 rounded">.env.local</code> and restart the dev server.
              </span>
            </div>
          </div>
        )}

        {/* ── Stat cards ─────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Impressions"
            value={loading ? '…' : fmt(totals.impressions)}
            sub={`last ${range} days`}
            highlight
          />
          <StatCard
            label="Avg Engagement"
            value={loading ? '…' : pct(avgEngagement)}
            sub={`across ${posts.length} posts`}
          />
          <StatCard
            label="Total Reactions"
            value={loading ? '…' : fmt(totals.likes)}
            sub={`${fmt(totals.comments)} comments · ${fmt(totals.clicks)} clicks`}
          />
          <StatCard
            label="Top Post Reach"
            value={loading ? '…' : fmt(topPostImpressions)}
            sub={topPost ? relativeDate(topPost.publishedAt) : '—'}
          />
        </div>

        {/* ── Charts row ─────────────────────────────────────────────────── */}
        <div className="grid lg:grid-cols-3 gap-6">

          {/* Daily metrics line chart */}
          <div className="lg:col-span-2 bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">
              Impressions &amp; Reach — Daily
            </h2>
            {dailyMetrics.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={dailyMetrics} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="date"
                    tick={{ fill: '#475569', fontSize: 10 }}
                    tickFormatter={(d) => d?.slice(5) ?? ''}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#475569', fontSize: 10 }}
                    tickFormatter={fmt}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend
                    wrapperStyle={{ fontSize: 11, color: '#64748b', paddingTop: 12 }}
                    iconType="circle"
                    iconSize={8}
                  />
                  <Line
                    type="monotone"
                    dataKey="impressions"
                    name="Impressions"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: '#3b82f6' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="reach"
                    name="Reach"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, fill: '#8b5cf6' }}
                  />
                  <Line
                    type="monotone"
                    dataKey="likes"
                    name="Likes"
                    stroke="#06b6d4"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="4 2"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center text-slate-600 text-sm">
                {loading ? (
                  <div className="w-full h-full rounded-lg bg-slate-700/40 animate-pulse" />
                ) : (
                  'No daily data for this range'
                )}
              </div>
            )}
          </div>

          {/* Reactions stacked bar (top 10 posts) */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-5">
              Engagement Mix — Top 10
            </h2>
            {reactionBarData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={reactionBarData} margin={{ top: 4, right: 4, bottom: 0, left: -24 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 10 }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: '#475569', fontSize: 10 }} tickFormatter={fmt} tickLine={false} axisLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Legend wrapperStyle={{ fontSize: 11, color: '#64748b', paddingTop: 12 }} iconType="circle" iconSize={8} />
                  <Bar dataKey="Likes" stackId="a" fill="#3b82f6" />
                  <Bar dataKey="Comments" stackId="a" fill="#8b5cf6" />
                  <Bar dataKey="Shares" stackId="a" fill="#06b6d4" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center">
                {loading ? (
                  <div className="w-full h-full rounded-lg bg-slate-700/40 animate-pulse" />
                ) : (
                  <span className="text-slate-600 text-sm">No data</span>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Post performance table ──────────────────────────────────────── */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div className="px-6 py-4 flex items-center justify-between gap-4 border-b border-slate-700">
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
              Post Performance
            </h2>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-slate-600 text-xs hidden sm:block">Sort by</span>
              <select
                value={sortBy}
                onChange={(e) => { setSortBy(e.target.value); setPage(1) }}
                className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[900px]">
              <thead>
                <tr className="border-b border-slate-700 text-slate-500 text-xs uppercase tracking-wider">
                  <th className="py-3 px-4 text-left w-10">#</th>
                  <th className="py-3 px-4 text-left">Content</th>
                  <th className="py-3 px-4 text-right">Impressions</th>
                  <th className="py-3 px-4 text-right">Reach</th>
                  <th className="py-3 px-4 text-right">Likes</th>
                  <th className="py-3 px-4 text-right">Comments</th>
                  <th className="py-3 px-4 text-right">Shares</th>
                  <th className="py-3 px-4 text-right">Clicks</th>
                  <th className="py-3 px-4 text-right">Eng.%</th>
                  <th className="py-3 px-4 text-center">Link</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <Skeleton rows={6} />
                ) : pagedPosts.length > 0 ? (
                  pagedPosts.map((p, i) => (
                    <PostRow
                      key={p.postId ?? p.latePostId ?? i}
                      post={p}
                      rank={(page - 1) * PAGE_SIZE + i + 1}
                    />
                  ))
                ) : (
                  <tr>
                    <td colSpan={10} className="py-14 text-center text-slate-600">
                      No posts found for the selected range
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="px-6 py-3.5 flex items-center justify-between border-t border-slate-700 gap-4">
              <span className="text-slate-600 text-xs">{posts.length} posts total</span>
              <div className="flex items-center gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 text-sm disabled:opacity-30 hover:bg-slate-600 transition"
                >
                  ← Prev
                </button>
                <span className="text-slate-500 text-sm tabular-nums">{page} / {totalPages}</span>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 rounded-lg bg-slate-700 text-sm disabled:opacity-30 hover:bg-slate-600 transition"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* ── Best time heatmap ───────────────────────────────────────────── */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-1">
            Best Time to Post
          </h2>
          <p className="text-slate-600 text-xs mb-5">
            Based on historical engagement from your LinkedIn posts (via Zernio)
          </p>
          {loading ? (
            <div className="h-40 rounded-lg bg-slate-700/40 animate-pulse" />
          ) : (
            <BestTimeHeatmap data={bestTime} />
          )}
        </div>

      </main>

      <footer className="border-t border-slate-700/50 py-5 text-center text-slate-700 text-xs mt-4">
        Data via Zernio API &middot; Personal LinkedIn dashboard
      </footer>
    </div>
  )
}
