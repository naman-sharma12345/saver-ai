<div align="center">

# SaverAI

**Know where your money goes. Before it's gone.**

The money app for students and the parents who fund them.
Track spending, see how many days your allowance really lasts, and get coached by machine learning that runs on our own servers. No LLMs, no third-party model APIs, no per-user AI bill.

[Features](#what-saverai-does) · [How the AI works](#the-ai-is-ours) · [Plans](#plans) · [Quick start](#quick-start) · [Configuration](#configuration) · [Roadmap](#roadmap)

</div>

---

## Why SaverAI

Indian students run a monthly allowance on UPI. Existing apps show *what* you spent in pie charts. They do not tell you the one thing that matters on the 12th of the month: **how many days your money lasts and what is about to go wrong.**

SaverAI is built around that moment.

- **Allowance runway.** "You have Rs 12,000 left, about Rs 522 a day for the next 23 days."
- **Coaching, not judging.** Nudges based on your own patterns, flagged unusual spend, cheaper places nearby.
- **Parents in the loop, students in control.** Parents set the allowance and see a summary. Students keep their own data view.
- **Private by design.** Your data is yours. Built with India's DPDP Rules 2025 in mind, including parental consent for under-18 users (in progress, see roadmap).

## What SaverAI does

| | Free | Pro |
|---|:-:|:-:|
| Expense tracking with ML auto-categorization | ✅ | ✅ |
| Budgets with over-budget alerts | ✅ | ✅ |
| Allowance runway (what you can spend per day) | ✅ | ✅ |
| Financial health score (0-100) | ✅ | ✅ |
| Unusual spending alerts (anomaly detection) | ✅ | ✅ |
| Smart tips | 1 a day | All |
| Subscription finder | Count and monthly cost | Which ones, yearly cost, next renewal |
| Spending forecast | This month's run rate | Next-month ML forecast with confidence range |
| Cheaper nearby store finder | | ✅ |
| Parent link and allowance view | | ✅ |
| Light, Dark and Auto themes | ✅ | ✅ |

Every new account gets a **7-day Pro trial, no card needed**. Prices are placeholders to be validated with real users (Rs 79 a month or Rs 599 a year, set in `frontend/src/config/plans.ts` and `backend/plans.py`).

## The AI is ours

Everything marked "AI" runs locally with classical machine learning. There is no LLM and no external model API key anywhere in this repo.

| Feature | Technique |
|---|---|
| Expense auto-categorization | TF-IDF + calibrated LinearSVC, keyword fallback |
| Unusual spending | Isolation Forest on amount and timing |
| Financial health score | Composite of savings ratio, budget adherence and spending discipline |
| Spending forecast | Regression on monthly history with 95% confidence intervals |
| Subscription detection | Logistic regression over gap regularity, amount stability and cycle fit (weekly, monthly, yearly), trained in-process on synthetic patterns with a fixed seed |
| Cheaper stores | Geodesic distance plus price-level model over a store table |

Why this matters for a startup: zero marginal AI cost per user, no data leaves our servers for inference, and the models are ours to improve.

## Architecture

```
React 19 + Vite + TypeScript + Tailwind v4 (PWA)
        |  JWT over HTTPS, React Query
        v
Flask API  ->  SQLAlchemy  ->  SQLite (dev) / PostgreSQL (prod)
   |
   +-- ml/          scikit-learn models (categorizer, anomaly, forecast, subscriptions)
   +-- plans.py     plans, trial and entitlement checks (single source of truth)
   +-- routes/      auth, expenses, budgets, analytics, stores, parent, billing, subscriptions
   +-- APScheduler  daily recommendation job
```

Billing is behind clean seams:

- **Mock mode** (default): no keys needed. Checkout simulates an upgrade so the whole paywall flow works in development. Disabled in production.
- **Live mode**: set the Razorpay variables and checkout creates real subscriptions (UPI Autopay, cards, eMandate). A signed webhook (`POST /api/billing/webhook`, HMAC-SHA256) activates and renews Pro.

## Quick start

Requirements: Python 3.11+, Node 20+.

```bash
git clone https://github.com/naman-sharma12345/saver-ai.git
cd saver-ai

# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set JWT_SECRET_KEY at minimum
python seed_db.py               # demo data and trains the categorizer
python run.py                   # http://localhost:5000

# Frontend (new terminal)
cd frontend
npm ci --legacy-peer-deps
VITE_API_URL=http://localhost:5000/api npm run dev   # http://localhost:5173
```

Demo logins after seeding: `student1@test.com` (with a linked parent `parent@test.com`), password `Test@123`. Change or delete these before any real deployment.

Docker:

```bash
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
docker compose up --build
```

### Tests

```bash
cd backend && pytest -q           # API, ML, billing and entitlement tests
cd frontend && npm test && npm run build
```

CI runs both on every push and pull request.

## Configuration

All settings are environment variables (see `backend/.env.example`).

| Variable | Purpose |
|---|---|
| `JWT_SECRET_KEY` | Required in production |
| `DATABASE_URI` | SQLite by default, use PostgreSQL in production |
| `CORS_ORIGINS` | Allowed frontend origins |
| `ADMIN_EMAILS` | Who may retrain the ML model |
| `TRIAL_DAYS` | Free trial length, default 7 |
| `FRONTEND_URL` | Base URL used in emailed links |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` | Email for reset and verification links. Empty `SMTP_HOST` only logs emails (development) |
| `RATELIMIT_ENABLED`, `TRUST_PROXY` | Auth rate limits (on by default); set `TRUST_PROXY=1` behind a reverse proxy |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_JWT_SECRET` | Reserved for a future Supabase auth/db swap, unused today |
| `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET` | Enable live billing |
| `RAZORPAY_WEBHOOK_SECRET` | Verify Razorpay webhooks |
| `RAZORPAY_PLAN_ID_MONTHLY`, `RAZORPAY_PLAN_ID_YEARLY` | Plans created in the Razorpay dashboard |

Point the Razorpay webhook at `/api/billing/webhook` for `subscription.activated`, `subscription.charged`, `subscription.cancelled`, `subscription.halted`, `subscription.completed`.

## Roadmap

Shipped: Apple-style design system, dark mode, landing page, 7-day trial, paywall and pricing, Razorpay seam, subscription detection, auth hardening (rate limits, password reset, email verification), tested API and CI.

Next, roughly in order:

- [ ] Savings goals with projected finish dates
- [x] Auth hardening: rate limiting, password reset, email verification (Supabase swap-in is a documented seam)
- [ ] DPDP consent flow and age gate for under-18 users
- [ ] Money stored as integer paise, user-entered expense dates
- [ ] UPI / bank statement import (CSV and PDF)
- [ ] Account Aggregator integration for consented bank data
- [ ] Receipt scanning
- [ ] "Ask your money": natural-language questions answered by our own query engine, no LLM
- [ ] PostgreSQL by default and one-command deploy

## Security

- Passwords hashed with bcrypt, 8 character minimum. JWT access and refresh tokens.
- Rate limits on login, register and password reset. Reset links are signed, expire in one hour and work once. The forgot-password endpoint never reveals whether an email has an account.
- Production refuses to start without `JWT_SECRET_KEY`.
- Model retraining is limited to `ADMIN_EMAILS`.
- Webhooks are accepted only with a valid HMAC signature.
- Found a vulnerability? Please open a private security advisory on GitHub instead of a public issue.

## Research

The market, competitor and monetization research behind these choices is summarised in the project history. Highlights: UPI handles 24 billion transactions a month, Jar reached profitability by moving money rather than charging for tracking, and the median freemium app converts about 2 percent, which is why the free tier here is a real product and not a demo.

## Contributing

Branch from `main`, keep PRs small, run the tests above, and update this README when behaviour changes.

## License

All rights reserved for now. A license will be added before any public release.
