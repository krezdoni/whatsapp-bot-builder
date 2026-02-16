'use client'

export default function StripeButton({ price }) {
  return (
    <button
      onClick={() => console.log('Stripe button clicked')}
      className="px-8 py-4 bg-white text-black font-bold rounded-lg hover:bg-gray-100 transition"
    >
      Buy Now
    </button>
  )
}
