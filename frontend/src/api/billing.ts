import api from './axios';

export interface Entitlement {
  status: 'trial' | 'active' | 'free' | 'expired';
  plan: 'free' | 'pro';
  is_pro: boolean;
  trial_ends_at: string | null;
  trial_days_left: number;
  plan_expires_at: string | null;
  features: string[];
}

export interface BillingStatus {
  entitlement: Entitlement;
  mode: 'mock' | 'live';
  prices_inr: { monthly: number; yearly: number };
  trial_days: number;
}

export const billingApi = {
  status: async (): Promise<BillingStatus> => (await api.get('/billing/status')).data,
  checkout: async (interval: 'monthly' | 'yearly') => (await api.post('/billing/checkout', { interval })).data,
  cancel: async () => (await api.post('/billing/cancel')).data,
};
