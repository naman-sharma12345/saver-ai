// Single source of truth for plans shown in the UI. Prices are placeholders to be validated.
// The backend (app/plans.py) enforces entitlements; keep the two in sync.
export const PLANS = {
  trialDays: 7,
  free: {
    id: 'free', name: 'Free', priceMonthly: 0, priceYearly: 0,
    features: ['Expense tracking with auto-categories', 'Budgets and over-budget alerts', 'Allowance runway: what you can spend per day', 'Financial health score', 'Unusual spending alerts', 'One smart tip a day', 'See how much your subscriptions cost'],
  },
  pro: {
    id: 'pro', name: 'Pro', priceMonthly: 79, priceYearly: 599,
    features: ['Everything in Free', 'Every smart tip, not just one', 'Next-month spending forecast', 'Subscription details and renewal dates', 'Cheaper nearby store finder', 'Parent link and allowance view', 'Priority support'],
  },
} as const;
