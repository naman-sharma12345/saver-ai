import api from './axios';

export const analyticsApi = {
  getSpendingByCategory: async (month?: string) => {
    const response = await api.get('/analytics/spending-by-category', { params: { month } });
    return response.data;
  },
  getSpendingOverTime: async (months: number = 6) => {
    const response = await api.get('/analytics/spending-over-time', { params: { months } });
    return response.data;
  },
  getBudgetVsActual: async (month: string) => {
    const response = await api.get('/analytics/budget-vs-actual', { params: { month } });
    return response.data;
  },
  getHealthScore: async () => {
    const response = await api.get('/analytics/financial-health-score');
    return response.data;
  },
  getNextMonthPrediction: async () => {
    const response = await api.get('/analytics/next-month-prediction');
    return response.data;
  }
};
