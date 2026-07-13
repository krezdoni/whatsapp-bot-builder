import { NextResponse } from 'next/server'

// Zernio / Getlate — covers LinkedIn posts published through Zernio
// Note: LinkedIn's API only exposes analytics for posts authored via the connected app.
// For posts published natively on LinkedIn, use the CSV import feature instead.
const BASE = process.env.ZERNIO_API_BASE ?? 'https://zernio.com/api'

function normalize(post) {
  const li = post.platformAnalytics?.find((p) => p.platform === 'linkedin')
  const a = li?.analytics ?? post.analytics ?? {}
  return {
    id: String(post.postId ?? post.latePostId ?? post.id ?? ''),
    platform: 'linkedin',
    content: post.content ?? post.text ?? '',
    publishedAt: post.publishedAt ?? post.createdAt ?? '',
    url: li?.platformPostUrl ?? post.url ?? '',
    views: a.impressions ?? a.views ?? 0,
    likes: a.reactions ?? a.likes ?? 0,
    comments: a.comments ?? 0,
    shares: a.reposts ?? a.shares ?? 0,
    saves: a.saves ?? 0,
    engagementRate: a.engagementRate ?? 0,
  }
}

export async function GET(request) {
  if (!process.env.ZERNIO_API_KEY) return NextResponse.json({ posts: [] })

  const { searchParams } = new URL(request.url)
  const params = new URLSearchParams({ platform: 'linkedin' })
  for (const [k, v] of searchParams.entries()) params.set(k, v)

  try {
    const res = await fetch(`${BASE}/v1/analytics?${params}`, {
      headers: { Authorization: `Bearer ${process.env.ZERNIO_API_KEY}` },
      next: { revalidate: 300 },
    })
    if (!res.ok) return NextResponse.json({ posts: [] })
    const data = await res.json()
    const posts = (data.data ?? data.posts ?? []).map(normalize)
    return NextResponse.json({ posts })
  } catch {
    return NextResponse.json({ posts: [] })
  }
}
