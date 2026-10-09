import api from './axios';

export interface AllowanceRequest {
  id: number; amount: number; reason: string; status: 'pending' | 'approved' | 'declined';
  parent_note: string | null; student_name: string | null; created_at: string | null; decided_at: string | null;
}

export const requestsApi = {
  list: async (): Promise<{ requests: AllowanceRequest[]; pending: number }> => (await api.get('/requests')).data,
  create: async (body: { amount: number; reason: string }): Promise<AllowanceRequest> => (await api.post('/requests', body)).data,
  decide: async (id: number, decision: 'approve' | 'decline', note?: string): Promise<AllowanceRequest> =>
    (await api.post(`/requests/${id}/decision`, { decision, note })).data,
};
