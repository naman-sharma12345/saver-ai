import api from './axios';

export interface AskAnswer {
  intent: string; period: string; answer: string; locked: boolean; value?: number;
  breakdown?: { category: string; amount: number }[];
  rows?: { store: string; amount: number; date: string }[];
}

export const askApi = {
  ask: async (question: string, previous?: string): Promise<AskAnswer> => (await api.post('/ask', { question, previous })).data,
};
