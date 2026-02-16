# WhatsApp Reply Bot Builder

Create custom WhatsApp bots in 60 seconds. No coding required.

## Features

✅ No-code bot builder  
✅ Instant OpenClaw integration  
✅ Customer support, lead qualification, applicant screening, appointment booking  
✅ $9 one-time payment  

## Local Setup

```bash
npm install
npm run dev
```

Visit `http://localhost:3000`

## Deployment to Vercel

```bash
vercel --prod
```

## Environment Variables

Create `.env.local`:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_ID=price_...
NEXT_PUBLIC_URL=https://your-domain.vercel.app
```

## Stripe Setup

1. Create Stripe account
2. Create a new product ($9 one-time)
3. Copy `price_` ID to `.env.local`
4. Set webhook endpoint to `/api/webhooks/stripe`

## License

MIT
