import api from './axios';

export interface CategoryRule { id: number; merchant: string; category: string }

export const categoryRulesApi = {
  list: async (): Promise<{ rules: CategoryRule[] }> => (await api.get('/category-rules')).data,
  remove: async (id: number) => (await api.delete(`/category-rules/${id}`)).data,
};
