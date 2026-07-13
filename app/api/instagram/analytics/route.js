import { NextResponse } from 'next/server'

// Instagram Graph API — reads your own posts natively (no posting-through-Zernio needed)
// Requires: INSTAGRAM_ACCESS_TOKEN (long-lived user token from Meta Developer)
// Setup guide shown in the dashboard when token is missing.
const TOKEN = process.env.INSTAGRAM_ACCESS_TOKEN
const BASE = 'https://graph.instagram.com'

const FIELDS = [
  'id', 'caption', 'timestamp', 'media_type', 'permalink',
  'like_count', 'comments_count',
].join(',')

const INSIGHTS_METRICS = 'impressions,reach,saved'

function normalize(post, insights) {
  const m = {}
  insights?.data?.forEach((d) => { m[d.name] = d.values?.[0]?.value ?? d.value ?? 0 })
  return {
    id: String(post.id ?? ''),
    platform: 'instagram',
    content: post.caption ?? '',
    publishedAt: post.timestamp ?? '',
    url: post.permalink ?? '',
    views: m.impressions ?? 0,
    likes: post.like_count ?? 0,
    comments: post.comments_count ?? 0,
    shares: 0,
    saves: m.saved ?? 0,
    engagementRate: m.reach > 0
      ? ((post.like_count ?? 0) + (post.comments_count ?? 0) + (m.saved ?? 0)) / m.reach
      : 0,
  }
}

export async function GET() {
  if (!TOKEN) return NextResponse.json({ posts: [], missingToken: true })

  try {
    // 1. Fetch media list
    const mediaRes = await fetch(
      `${BASE}/me/media?fields=${FIELDS}&limit=50&access_token=${TOKEN}`,
      { next: { revalidate: 300 } }
    )
    if (!mediaRes.ok) {
      const err = await mediaRes.json()
      return NextResponse.json({ posts: [], error: err?.error?.message ?? mediaRes.status })
    }
    const mediaData = await mediaRes.json()
    const items = mediaData.data ?? []

    // 2. Fetch insights for each post (parallel, skip errors for non-image types)
    const withInsights = await Promise.all(
      items.map(async (post) => {
        try {
          const iRes = await fetch(
            `${BASE}/${post.id}/insights?metric=${INSIGHTS_METRICS}&access_token=${TOKEN}`,
            { next: { revalidate: 300 } }
          )
          const insights = iRes.ok ? await iRes.json() : null
          return normalize(post, insights)
        } catch {
          return normalize(post, null)
        }
      })
    )

    return NextResponse.json({ posts: withInsights })
  } catch (e) {
    return NextResponse.json({ posts: [], error: e.message })
  }
}
