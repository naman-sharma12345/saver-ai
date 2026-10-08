import api from './axios';

export const authApi = {
  login: async (data: any) => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },
  register: async (data: any) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },
  forgotPassword: async (email: string) => (await api.post('/auth/forgot-password', { email })).data,
  resetPassword: async (token: string, password: string) => (await api.post('/auth/reset-password', { token, password })).data,
  verifyEmail: async (token: string) => (await api.post('/auth/verify-email', { token })).data,
  guardianInfo: async (token: string) => (await api.get('/auth/guardian-consent', { params: { token } })).data,
  guardianConsent: async (token: string, approve: boolean) => (await api.post('/auth/guardian-consent', { token, approve })).data,
  exportData: async () => (await api.get('/auth/export')).data,
  deleteAccount: async (password: string) => (await api.delete('/auth/me', { data: { password } })).data,
  sendVerification: async () => (await api.post('/auth/send-verification')).data,
};
