import api from './axios';

export interface WhatIf {
  categories: { category: string; monthly_spend: number; cut_percent: number; monthly_saving: number }[];
  monthly_saving: number;
  yearly_saving: number;
  goal: { name: string; remaining: number; months: number | null } | null;
}

export const whatIfApi = {
  run: async (cuts: Record<string, number>): Promise<WhatIf> => (await api.post('/whatif', { cuts })).data,
};
