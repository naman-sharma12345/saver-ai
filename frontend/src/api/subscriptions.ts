import api from './axios';

export interface DetectedSubscription {
  merchant: string; amount: number; period: 'weekly' | 'monthly' | 'yearly';
  confidence: number; charges: number; last_charged: string; next_expected: string;
  monthly_cost: number; annual_cost: number;
}

export const subscriptionsApi = {
  list: async (): Promise<{ subscriptions: DetectedSubscription[]; total_monthly: number; total_annual: number }> =>
    (await api.get('/subscriptions')).data,
};
