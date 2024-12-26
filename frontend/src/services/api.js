import axios from 'axios';

const API_URL = 'https://localhost:8000/accounts';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if it exists
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const register = async (userData) => {
  const response = await api.post('/register/', userData);
  return response.data;
};

export const login = async (credentials) => {
  const response = await api.post('/login/', credentials);
  return response.data;
};

export const logout = async (refresh_token) => {
  const response = await api.post('/logout/', { refresh: refresh_token });
  return response.data;
};

export const refreshToken = async (refresh_token) => {
  const response = await api.post('/token/refresh/', { refresh: refresh_token });
  return response.data;
};

export const setupMFA = async () => {
  const response = await api.get('/mfa/setup/');
  return response.data;
};

export const verifyMFA = async (code) => {
  const response = await api.post('/mfa/setup/', { totp_code: code });
  return response.data;
};

export const loginWithMFA = async (credentials) => {
  const response = await api.post('/login/', credentials);
  return response.data;
};

export default api; 