import { NextResponse } from 'next/server'

// Which platforms are configured
const CONFIG = {
  linkedin: !!process.env.AUTHOREDUP_API_KEY,
  instagram: !!process.env.ZERNIO_API_KEY,
  twitter: !!process.env.ZERNIO_API_KEY,
  substack: !!process.env.SUBSTACK_PUBLICATION,
}

async function safeFetch(url) {
  try {
    const res = await fetch(url, { next: { revalidate: 60 } })
    const json = await res.json()
    return json.posts ?? []
  } catch {
    return []
  }
}

export async function GET(request) {
  const { searchParams, origin } = new URL(request.url)
  const from = searchParams.get('from') ?? ''
  const to = searchParams.get('to') ?? ''
  const qs = `from=${from}&to=${to}&limit=100`

  const [li, ig, tw, sub] = await Promise.all([
    CONFIG.linkedin ? safeFetch(`${origin}/api/linkedin/analytics?${qs}`) : [],
    CONFIG.instagram ? safeFetch(`${origin}/api/instagram/analytics?${qs}`) : [],
    CONFIG.twitter ? safeFetch(`${origin}/api/twitter/analytics?${qs}`) : [],
    CONFIG.substack ? safeFetch(`${origin}/api/substack/analytics?limit=50`) : [],
  ])

  const posts = [...li, ...ig, ...tw, ...sub].sort(
    (a, b) => new Date(b.publishedAt) - new Date(a.publishedAt)
  )

  return NextResponse.json({ posts, config: CONFIG })
}
