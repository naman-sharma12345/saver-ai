// Single source of truth for plans shown in the UI. Prices are placeholders to be validated.
// The backend (app/plans.py) enforces entitlements; keep the two in sync.
export const PLANS = {
  trialDays: 7,
  free: {
    id: 'free', name: 'Free', priceMonthly: 0, priceYearly: 0,
    features: ['Manual expense tracking', 'Basic budgets', 'Monthly summary'],
  },
  pro: {
    id: 'pro', name: 'Pro', priceMonthly: 79, priceYearly: 599,
    features: ['Everything in Free', 'AI insights and coaching', 'Spending forecasts', 'Cheaper nearby store finder', 'Parent link and allowance view', 'Priority support'],
  },
} as const;
