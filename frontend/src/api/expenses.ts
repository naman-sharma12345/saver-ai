import api from './axios';

export const expensesApi = {
  getAll: async (params?: any) => {
    const response = await api.get('/expenses', { params });
    return response.data;
  },
  getAnomalies: async () => {
    const response = await api.get('/expenses/anomalies');
    return response.data;
  },
  create: async (data: any) => {
    const response = await api.post('/expenses', data);
    return response.data;
  },
  importStatement: async (src: { csv?: string; pdf_base64?: string }, commit: boolean) => (await api.post('/expenses/import', { ...src, commit })).data,
  delete: async (id: number) => {
    const response = await api.delete(`/expenses/${id}`);
    return response.data;
  }
};
