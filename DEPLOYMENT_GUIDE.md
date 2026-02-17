# WhatsApp Bot Builder — Deployment Checklist

## Step 1: Set Up Stripe Account (5 minutes)

1. Go to [stripe.com](https://stripe.com) → Sign up (if not already)
2. Dashboard → Products → Create product:
   - **Name:** WhatsApp Reply Bot Builder
   - **Price:** $9.00 USD
   - **Billing:** One-time payment
3. Copy the **Price ID** (starts with `price_`)
4. Go to API keys → Copy **Secret Key** (starts with `sk_`)

## Step 2: Create Vercel Account & Connect GitHub (2 minutes)

1. Go to [vercel.com](https://vercel.com) → Sign up
2. Import project:
   - Click "Add New" → Import Git Repository
   - Paste: `https://github.com/YOUR_USERNAME/whatsapp-bot-builder`
   - Click "Import"

## Step 3: Add Environment Variables to Vercel (2 minutes)

In Vercel project settings → Environment Variables:

```
STRIPE_SECRET_KEY = sk_test_... (from Stripe)
STRIPE_PRICE_ID = price_... (from Stripe)
NEXT_PUBLIC_URL = https://whatsapp-bot-builder.vercel.app
```

Click "Deploy" when done.

## Step 4: Verify Deployment (1 minute)

- Visit `https://whatsapp-bot-builder.vercel.app`
- Click "Get Started Now" → Test Stripe flow
- You should see Stripe checkout

## Step 5: Set Up Stripe Webhook (Optional but Recommended)

1. Stripe Dashboard → Webhooks → Add endpoint
   - URL: `https://whatsapp-bot-builder.vercel.app/api/webhooks/stripe`
   - Events: `checkout.session.completed`, `customer.subscription.updated`
2. Copy **Signing Secret** (starts with `whsec_`)
3. Add to Vercel env vars:
   ```
   STRIPE_WEBHOOK_SECRET = whsec_...
   ```

## Step 6: Promote on X (Twitter)

Post this:

```
🚀 Just shipped: WhatsApp Reply Bot Builder

Create custom AI bots for WhatsApp in 60 seconds. 
No coding required.

✅ Customer support
✅ Lead qualification  
✅ Applicant screening
✅ Appointment booking

$9 one-time → https://whatsapp-bot-builder.vercel.app

Built with @openclaw_ai

#AI #WhatsApp #NoCode #SaaS
```

## Step 7: Monitor Sales & Costs

1. Check Stripe dashboard for payments
2. Run `/usage full` to monitor OpenClaw token costs
3. If costs > $1, you're already profitable at $9/sale

---

## Troubleshooting

**"Stripe button does nothing"**
- Check that `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID` are in Vercel env vars
- Restart deployment after adding env vars

**"Deploy fails"**
- Run `npm install` locally, check for errors
- Ensure `node_modules/` is not committed

**"Can't create checkout"**
- Verify Stripe keys are correct
- Check browser console (F12) for errors

---

**Deployed?** Reply with the live URL. Let's get your first sale! 🎉
