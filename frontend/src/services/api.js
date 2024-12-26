import axios from 'axios';

const API_URL = 'https://localhost:8000/accounts';

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

// The CSRF token will be automatically handled by Django's CSRF middleware
// No need to manually set it in headers

export const register = async (userData) => {
  const response = await api.post('/register/', userData);
  return response.data;
};

export const login = async (credentials) => {
  try {
    const response = await api.post('/login/', credentials);
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = async () => {
  try {
    const response = await api.post('/logout/');
    return response.data;
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
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

export const checkAuth = async () => {
  try {
    const response = await api.get('/check-auth/');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getUsers = async () => {
  const response = await api.get('/users/');
  return response.data;
};

export const updateUserRole = async (userId, role) => {
  const response = await api.put('/users/', { id: userId, role });
  return response.data;
};

// Add an interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only try to refresh if it's a 401 error, not a login request, and hasn't been retried
    if (
      error.response?.status === 401 && 
      !originalRequest._retry &&
      !originalRequest.url.includes('/login/') &&
      !originalRequest.url.includes('/check-auth/')
    ) {
      originalRequest._retry = true;

      try {
        await api.post('/token/refresh/');
        return api(originalRequest);
      } catch (refreshError) {
        // If refresh fails, let the error propagate
        throw refreshError;
      }
    }

    throw error;
  }
);

export default api; 