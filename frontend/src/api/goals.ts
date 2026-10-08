import api from './axios';

export interface Goal {
  id: number; name: string; target_amount: number; saved_amount: number; deadline: string | null;
  progress: number; remaining: number; pace_per_month: number | null; pace_source: 'saved' | 'surplus' | null;
  projected_finish: string | null; needed_per_month: number | null;
  status: 'done' | 'on_track' | 'behind' | 'no_pace';
}

export const goalsApi = {
  list: async (): Promise<Goal[]> => (await api.get('/goals')).data.goals,
  create: async (body: { name: string; target_amount: number; deadline?: string | null }): Promise<Goal> =>
    (await api.post('/goals', body)).data,
  contribute: async (id: number, amount: number): Promise<Goal> =>
    (await api.post(`/goals/${id}/contribute`, { amount })).data,
  remove: async (id: number) => (await api.delete(`/goals/${id}`)).data,
};
