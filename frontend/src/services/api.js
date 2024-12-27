import axios from 'axios';

const API_URL = 'https://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 5000,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: {
    'Content-Type': 'application/json',
  }
});

// The CSRF token will be automatically handled by Django's CSRF middleware
// No need to manually set it in headers

export const register = async (userData) => {
  try {
    const response = await api.post('/accounts/register/', userData);
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const login = async (credentials) => {
  try {
    const response = await api.post('/accounts/login/', credentials);
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const logout = async () => {
  try {
    const response = await api.post('/accounts/logout/');
    return response.data;
  } catch (error) {
    console.error('Logout error:', error);
    throw error;
  }
};

export const refreshToken = async (refresh_token) => {
  const response = await api.post('/accounts/token/refresh/', { refresh: refresh_token });
  return response.data;
};

export const setupMFA = async () => {
  const response = await api.get('/accounts/mfa/setup/');
  return response.data;
};

export const verifyMFA = async (code) => {
  const response = await api.post('/accounts/mfa/setup/', { totp_code: code });
  return response.data;
};

export const loginWithMFA = async (credentials) => {
  const response = await api.post('/accounts/login/', credentials);
  return response.data;
};

export const checkAuth = async () => {
  try {
    const response = await api.get('/accounts/check-auth/');
    return response.data;
  } catch (error) {
    throw error;
  }
};

export const getUsers = async () => {
  const response = await api.get('/accounts/users/');
  return response.data;
};

export const updateUserRole = async (userId, role) => {
  const response = await api.put('/accounts/users/', { id: userId, role });
  return response.data;
};

export const getFiles = async () => {
  const response = await api.get('/files/');
  return response.data;
};

export const uploadFile = async (formData) => {
  const response = await api.post('/files/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const downloadFile = async (fileId) => {
  try {
    const response = await api.get(`/files/download/${fileId}/`);
    
    if (response.data.error) {
      throw new Error(response.data.error);
    }
    
    // Convert base64 strings back to Uint8Arrays
    const salt = base64ToArrayBuffer(response.data.salt);
    const iv = base64ToArrayBuffer(response.data.iv);
    const content = base64ToArrayBuffer(response.data.content);
    
    // Generate decryption key
    const encoder = new TextEncoder();
    const keyMaterial = await window.crypto.subtle.importKey(
      'raw',
      encoder.encode(process.env.REACT_APP_FILE_KEY),
      { name: 'PBKDF2' },
      false,
      ['deriveBits']
    );
    
    // Derive the key using PBKDF2
    const key = await window.crypto.subtle.deriveBits(
      {
        name: 'PBKDF2',
        salt: salt,
        iterations: 100000,
        hash: 'SHA-256'
      },
      keyMaterial,
      256 // 256 bits for AES-256
    );
    
    // Import the derived bits as an AES-CBC key
    const aesKey = await window.crypto.subtle.importKey(
      'raw',
      key,
      { name: 'AES-CBC' },
      false,
      ['decrypt']
    );
    
    // Decrypt the file
    const decryptedContent = await window.crypto.subtle.decrypt(
      {
        name: 'AES-CBC',
        iv: iv
      },
      aesKey,
      content
    );
    
    // Remove padding
    const paddingLength = new Uint8Array(decryptedContent)[decryptedContent.byteLength - 1];
    const unpadded = decryptedContent.slice(0, decryptedContent.byteLength - paddingLength);
    
    // Create and download the file
    const blob = new Blob([unpadded], { type: response.data.content_type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', response.data.filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    console.error('Download error:', error);
    throw error;
  }
};

// Helper function to convert base64 to ArrayBuffer
const base64ToArrayBuffer = (base64) => {
  const binaryString = window.atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes.buffer;
};

export const deleteFile = async (fileId) => {
  const response = await api.delete(`/files/${fileId}/`);
  return response.data;
};

export const getSharedFiles = async () => {
  const response = await api.get('/files/shared/');
  return response.data;
};

export const shareFile = async (fileId, email) => {
  const response = await api.post(`/files/${fileId}/share/`, {
    email: email
  });
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