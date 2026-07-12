import { NextResponse } from 'next/server'

const BASE = process.env.ZERNIO_API_BASE ?? 'https://zernio.com/api'

function normalize(post) {
  const li = post.platformAnalytics?.find((p) => p.platform === 'instagram')
  const a = li?.analytics ?? post.analytics ?? {}
  return {
    id: String(post.postId ?? post.latePostId ?? ''),
    platform: 'instagram',
    content: post.content ?? '',
    publishedAt: post.publishedAt ?? '',
    url: li?.platformPostUrl ?? '',
    views: a.impressions ?? a.views ?? 0,
    likes: a.likes ?? 0,
    comments: a.comments ?? 0,
    shares: a.shares ?? 0,
    saves: a.saves ?? 0,
    engagementRate: a.engagementRate ?? 0,
  }
}

export async function GET(request) {
  const { searchParams } = new URL(request.url)
  const params = new URLSearchParams({ platform: 'instagram' })
  for (const [k, v] of searchParams.entries()) params.set(k, v)

  try {
    const res = await fetch(`${BASE}/v1/analytics?${params}`, {
      headers: { Authorization: `Bearer ${process.env.ZERNIO_API_KEY}` },
      next: { revalidate: 300 },
    })
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text, posts: [] }, { status: res.status })
    }
    const data = await res.json()
    const posts = (data.data ?? data.posts ?? []).map(normalize)
    return NextResponse.json({ posts })
  } catch (e) {
    return NextResponse.json({ error: e.message, posts: [] }, { status: 500 })
  }
}
