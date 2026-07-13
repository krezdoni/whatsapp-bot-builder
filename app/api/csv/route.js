import { NextResponse } from 'next/server'

// Parses a CSV string into an array of objects using the header row as keys
function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/)
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map((h) => h.replace(/^"|"$/g, '').trim().toLowerCase())
  return lines.slice(1).map((line) => {
    const vals = line.match(/(".*?"|[^,]+|(?<=,)(?=,)|(?<=,)$|^(?=,))/g) ?? []
    const obj = {}
    headers.forEach((h, i) => {
      obj[h] = (vals[i] ?? '').replace(/^"|"$/g, '').trim()
    })
    return obj
  })
}

function num(v) {
  const n = parseInt(String(v ?? '0').replace(/,/g, ''), 10)
  return isNaN(n) ? 0 : n
}

function parseFloat2(v) {
  const n = parseFloat(String(v ?? '0').replace(/%/g, ''))
  return isNaN(n) ? 0 : n
}

// ── X / Twitter Analytics CSV ─────────────────────────────────────────────────
// Export from: analytics.twitter.com/about → Export data → Tweet activity
// Columns: Tweet id, Tweet permalink, Tweet text, time, impressions, engagements,
//   engagement rate, retweets, replies, likes, user profile clicks, url clicks,
//   hashtag clicks, detail expands, media views, media engagements
function normalizeTwitterCsv(row) {
  const text = row['tweet text'] ?? row['text'] ?? ''
  const date = row['time'] ?? row['date'] ?? ''
  return {
    id: row['tweet id'] ?? row['id'] ?? String(Math.random()),
    platform: 'twitter',
    content: text,
    publishedAt: date ? new Date(date).toISOString() : '',
    url: row['tweet permalink'] ?? row['permalink'] ?? '',
    views: num(row['impressions']),
    likes: num(row['likes']),
    comments: num(row['replies']),
    shares: num(row['retweets']),
    saves: num(row['url clicks'] ?? row['bookmarks'] ?? 0),
    engagementRate: parseFloat2(row['engagement rate']) / 100,
  }
}

// ── LinkedIn Analytics CSV ────────────────────────────────────────────────────
// Export from: linkedin.com/analytics/creator/content → Export
// Columns: Post title, Published date, Content type, Impressions, Views,
//   Reactions, Comments, Reposts, Engagement rate, Clicks
function normalizeLinkedInCsv(row) {
  return {
    id: row['post url'] ?? String(Math.random()),
    platform: 'linkedin',
    content: row['post title'] ?? row['title'] ?? '',
    publishedAt: row['published date'] ?? row['date'] ?? '',
    url: row['post url'] ?? '',
    views: num(row['impressions'] ?? row['views']),
    likes: num(row['reactions'] ?? row['likes']),
    comments: num(row['comments']),
    shares: num(row['reposts'] ?? row['shares']),
    saves: 0,
    engagementRate: parseFloat2(row['engagement rate']) / 100,
  }
}

function detectPlatform(headers) {
  const h = headers.join(' ')
  if (h.includes('tweet') || h.includes('retweets') || h.includes('twitter')) return 'twitter'
  if (h.includes('reactions') || h.includes('reposts') || h.includes('linkedin')) return 'linkedin'
  return null
}

export async function POST(request) {
  try {
    const formData = await request.formData()
    const file = formData.get('file')
    if (!file) return NextResponse.json({ error: 'No file' }, { status: 400 })

    const text = await file.text()
    const rows = parseCsv(text)
    if (!rows.length) return NextResponse.json({ error: 'Empty CSV' }, { status: 400 })

    const headers = Object.keys(rows[0])
    const platform = detectPlatform(headers)
    if (!platform) return NextResponse.json({ error: 'Unrecognised CSV format. Export from X Analytics or LinkedIn Creator Analytics.' }, { status: 400 })

    const posts = rows
      .map((r) => platform === 'twitter' ? normalizeTwitterCsv(r) : normalizeLinkedInCsv(r))
      .filter((p) => p.content || p.views > 0)

    return NextResponse.json({ posts, platform, count: posts.length })
  } catch (e) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
