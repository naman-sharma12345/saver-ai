import api from './axios';

export interface WeeklyDigest {
  headline: string;
  period: { start: string; end: string };
  total: number;
  previous_total: number;
  change_percent: number | null;
  daily: { date: string; amount: number }[];
  no_spend_days: number;
  top_category: { name: string; amount: number } | null;
  biggest_expense: { description: string; amount: number; category: string } | null;
  upcoming_renewals: { merchant: string; amount: number; date: string }[];
  renewals_count: number;
  renewals_locked: boolean;
}

export const digestApi = {
  weekly: async (): Promise<WeeklyDigest> => (await api.get('/digest/weekly')).data,
};
