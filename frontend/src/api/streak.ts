import api from './axios';

export interface StreakInfo {
  current: number; best: number; logged_today: boolean;
  badges: { days: number; name: string; earned: boolean }[];
  next_milestone: { days: number; name: string; to_go: number } | null;
}

export const streakApi = { get: async (): Promise<StreakInfo> => (await api.get('/streak')).data };
