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
  sendVerification: async () => (await api.post('/auth/send-verification')).data,
};
