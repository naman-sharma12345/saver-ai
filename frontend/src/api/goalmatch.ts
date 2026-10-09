import api from './axios';

export interface ChildGoal {
  id: number; name: string; target_amount: number; saved_amount: number;
  match_percent: number; match_cap: number | null; matched_amount: number;
}

export const goalMatchApi = {
  list: async (studentId: number): Promise<ChildGoal[]> => (await api.get(`/parent/children/${studentId}/goals`)).data.goals,
  set: async (studentId: number, goalId: number, percent: number, cap: number | null): Promise<ChildGoal> =>
    (await api.put(`/parent/children/${studentId}/goals/${goalId}/match`, { percent, cap })).data,
};
