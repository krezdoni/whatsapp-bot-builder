import { NextResponse } from 'next/server'

const BASE = process.env.AUTHOREDUP_API_BASE ?? 'https://api.authoredup.com'

function normalize(post) {
  const s = post.stats ?? post.analytics ?? {}
  return {
    id: String(post.id ?? post.postId ?? ''),
    platform: 'linkedin',
    content: post.text ?? post.content ?? post.body ?? '',
    publishedAt: post.publishedAt ?? post.createdAt ?? post.date ?? '',
    url: post.postUrl ?? post.url ?? '',
    views: s.impressions ?? s.views ?? 0,
    likes: s.reactions ?? s.likes ?? 0,
    comments: s.comments ?? 0,
    shares: s.reposts ?? s.shares ?? 0,
    saves: s.saves ?? s.bookmarks ?? 0,
    engagementRate: s.engagementRate ?? 0,
  }
}

export async function GET(request) {
  const { searchParams } = new URL(request.url)
  const params = new URLSearchParams()
  for (const [k, v] of searchParams.entries()) params.set(k, v)

  try {
    const res = await fetch(`${BASE}/api/v1/posts?${params}`, {
      headers: { Authorization: `Bearer ${process.env.AUTHOREDUP_API_KEY}` },
      next: { revalidate: 300 },
    })
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text, posts: [] }, { status: res.status })
    }
    const data = await res.json()
    const posts = (data.posts ?? data.data ?? (Array.isArray(data) ? data : [])).map(normalize)
    return NextResponse.json({ posts })
  } catch (e) {
    return NextResponse.json({ error: e.message, posts: [] }, { status: 500 })
  }
}
