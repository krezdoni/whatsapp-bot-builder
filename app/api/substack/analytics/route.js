import { NextResponse } from 'next/server'

const PUB = process.env.SUBSTACK_PUBLICATION // e.g. "nicco" from nicco.substack.com
const COOKIE = process.env.SUBSTACK_SESSION_COOKIE // substack.sid value (optional — enables open/click stats)

function normalize(post, stats) {
  return {
    id: String(post.id ?? ''),
    platform: 'substack',
    content: post.title ?? post.subtitle ?? '',
    publishedAt: post.post_date ?? post.updated_at ?? '',
    url: post.canonical_url ?? (PUB ? `https://${PUB}.substack.com/p/${post.slug}` : ''),
    // With cookie: opens = email opens; without: fall back to page views or 0
    views: stats?.views ?? stats?.opens ?? post.views ?? 0,
    likes: stats?.reactions ?? post.reaction_count ?? 0,
    comments: stats?.comments ?? post.comment_count ?? 0,
    shares: 0,
    saves: stats?.clicks ?? 0,
    engagementRate: stats?.email_open_rate ?? 0,
    _substackOnly: {
      openRate: stats?.email_open_rate ?? null,
      paidOpens: stats?.paid_opens ?? null,
      freeOpens: stats?.free_opens ?? null,
    },
  }
}

export async function GET(request) {
  if (!PUB) return NextResponse.json({ posts: [] })

  const { searchParams } = new URL(request.url)
  const limit = searchParams.get('limit') ?? '50'

  const authHeaders = COOKIE ? { Cookie: `connect.sid=${COOKIE}` } : {}

  try {
    // Public post list (no auth needed for public newsletters)
    const postsRes = await fetch(
      `https://${PUB}.substack.com/api/v1/posts?sort=new&limit=${limit}&type=newsletter`,
      { headers: authHeaders, next: { revalidate: 3600 } }
    )
    if (!postsRes.ok) return NextResponse.json({ posts: [], error: `Substack ${postsRes.status}` })
    const rawPosts = await postsRes.json()
    const postList = Array.isArray(rawPosts) ? rawPosts : (rawPosts.posts ?? [])

    // Try to pull detailed stats if session cookie is available
    let statsById = {}
    if (COOKIE) {
      const statsRes = await fetch(
        `https://${PUB}.substack.com/api/v1/post_stats`,
        { headers: authHeaders, next: { revalidate: 300 } }
      ).catch(() => null)
      if (statsRes?.ok) {
        const statsData = await statsRes.json()
        ;(statsData.posts ?? statsData ?? []).forEach((s) => {
          if (s.id) statsById[s.id] = s
        })
      }
    }

    const posts = postList.map((p) => normalize(p, statsById[p.id] ?? null))
    return NextResponse.json({ posts, hasStats: COOKIE != null })
  } catch (e) {
    return NextResponse.json({ error: e.message, posts: [] }, { status: 500 })
  }
}
