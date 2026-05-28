import { NextResponse } from 'next/server'

const BASE = process.env.ZERNIO_API_BASE ?? 'https://zernio.com/api'

export async function GET(request) {
  const { searchParams } = new URL(request.url)

  const params = new URLSearchParams({ platform: 'linkedin' })
  for (const [k, v] of searchParams.entries()) params.set(k, v)

  try {
    const res = await fetch(`${BASE}/v1/analytics/best-time?${params}`, {
      headers: { Authorization: `Bearer ${process.env.ZERNIO_API_KEY}` },
      next: { revalidate: 3600 },
    })
    if (!res.ok) {
      const text = await res.text()
      return NextResponse.json({ error: text }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (e) {
    return NextResponse.json({ error: e.message }, { status: 500 })
  }
}
