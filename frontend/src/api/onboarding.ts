import api from './axios';

export interface OnboardingStep { key: string; title: string; done: boolean; path: string }
export interface Onboarding { steps: OnboardingStep[]; done: number; total: number; complete: boolean }

export const onboardingApi = {
  get: async (): Promise<Onboarding> => (await api.get('/onboarding')).data,
};
