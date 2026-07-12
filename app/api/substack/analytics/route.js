import { NextResponse } from 'next/server'

// Accepts either a custom domain ("letters.niccokrezdorn.com")
// or a bare subdomain ("nicco" → nicco.substack.com)
const RAW = process.env.SUBSTACK_PUBLICATION
const HOST = RAW
  ? RAW.includes('.') ? RAW : `${RAW}.substack.com`
  : null

const COOKIE = process.env.SUBSTACK_SESSION_COOKIE

function normalize(post, stats) {
  return {
    id: String(post.id ?? ''),
    platform: 'substack',
    content: post.title ?? post.subtitle ?? '',
    publishedAt: post.post_date ?? post.updated_at ?? '',
    url: post.canonical_url ?? (HOST ? `https://${HOST}/p/${post.slug}` : ''),
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
  if (!HOST) return NextResponse.json({ posts: [] })

  const { searchParams } = new URL(request.url)
  const limit = searchParams.get('limit') ?? '50'

  const authHeaders = COOKIE ? { Cookie: `connect.sid=${COOKIE}` } : {}

  try {
    const postsRes = await fetch(
      `https://${HOST}/api/v1/posts?sort=new&limit=${limit}&type=newsletter`,
      { headers: authHeaders, next: { revalidate: 3600 } }
    )
    if (!postsRes.ok) return NextResponse.json({ posts: [], error: `Substack ${postsRes.status}` })
    const rawPosts = await postsRes.json()
    const postList = Array.isArray(rawPosts) ? rawPosts : (rawPosts.posts ?? [])

    let statsById = {}
    if (COOKIE) {
      const statsRes = await fetch(
        `https://${HOST}/api/v1/post_stats`,
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
