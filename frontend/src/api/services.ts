import api from './axios';

export const storesApi = {
  getNearby: async (params: { lat: number; lng: number; radius?: number; category?: string }) => {
    const response = await api.get('/stores/nearby', { params });
    return response.data;
  },
  getCheaperAlternatives: async (expenseId: number, radiusKm?: number) => {
    const response = await api.post('/stores/cheaper-alternatives', { expense_id: expenseId, radius_km: radiusKm });
    return response.data;
  }
};

export const recommendationsApi = {
  get: async () => {
    const response = await api.get('/recommendations');
    return response.data;
  }
};

export interface BudgetPaceItem { category: string; limit: number; spent: number; projected: number; status: 'over' | 'overshoot' | 'tight' | 'ok'; safe_daily?: number }

export const budgetsApi = {
  pace: async (): Promise<{ day: number; days_in_month: number; items: BudgetPaceItem[] }> => (await api.get('/budgets/pace')).data,
  getAll: async (month?: string) => {
    const response = await api.get('/budgets', { params: { month } });
    return response.data;
  },
  createOrUpdate: async (data: any) => {
    const response = await api.post('/budgets', data);
    return response.data;
  }
};

export const profileApi = {
  get: async () => {
    const response = await api.get('/profile');
    return response.data;
  },
  update: async (data: any) => {
    const response = await api.put('/profile', data);
    return response.data;
  }
};

export const parentApi = {
  getChildren: async () => {
    const response = await api.get('/parent/children');
    return response.data;
  },
  getChildSummary: async (childId: number) => {
    const response = await api.get(`/parent/children/${childId}/summary`);
    return response.data;
  },
  weekly: async (childId: number): Promise<{ headline: string; total: number; previous_total: number; change_percent: number | null; daily: { date: string; amount: number }[]; no_spend_days: number; top_category: { name: string; amount: number } | null }> =>
    (await api.get(`/parent/children/${childId}/weekly`)).data,
  weeklyEmail: async (): Promise<boolean> => (await api.get('/parent/weekly-email')).data.enabled,
  setWeeklyEmail: async (enabled: boolean): Promise<boolean> => (await api.put('/parent/weekly-email', { enabled })).data.enabled,
  weeklyPreview: async (): Promise<{ message: string }> => (await api.post('/parent/weekly-email/preview')).data,
  remind: async (childId: number, note?: string) => (await api.post(`/parent/children/${childId}/remind`, { note })).data,
};
