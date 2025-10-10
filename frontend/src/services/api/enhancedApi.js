// frontend/src/services/api/enhancedApi.js
// Enhanced API service with comprehensive error handling - Phase 7

import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Token refresh logic
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });

          const { access, refresh } = response.data;
          localStorage.setItem('access_token', access);
          if (refresh) {
            localStorage.setItem('refresh_token', refresh);
          }

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Error handler
const handleError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return {
          message: data.message || 'Bad request',
          errors: data.errors || null,
          status,
        };
      case 401:
        return {
          message: 'Unauthorized. Please login again.',
          status,
        };
      case 403:
        return {
          message: 'You do not have permission to perform this action.',
          status,
        };
      case 404:
        return {
          message: 'Resource not found.',
          status,
        };
      case 422:
        return {
          message: data.message || 'Validation failed',
          errors: data.errors || null,
          status,
        };
      case 500:
        return {
          message: 'Internal server error. Please try again later.',
          status,
        };
      default:
        return {
          message: data.message || 'An error occurred',
          status,
        };
    }
  } else if (error.request) {
    // Request was made but no response received
    return {
      message: 'Network error. Please check your connection.',
      status: 0,
    };
  } else {
    // Something else happened
    return {
      message: error.message || 'An unexpected error occurred',
      status: 0,
    };
  }
};

// API service methods
export const apiService = {
  // GET request
  get: async (url, config = {}) => {
    try {
      const response = await apiClient.get(url, config);
      return { data: response.data, error: null };
    } catch (error) {
      return { data: null, error: handleError(error) };
    }
  },

  // POST request
  post: async (url, data, config = {}) => {
    try {
      const response = await apiClient.post(url, data, config);
      return { data: response.data, error: null };
    } catch (error) {
      return { data: null, error: handleError(error) };
    }
  },

  // PUT request
  put: async (url, data, config = {}) => {
    try {
      const response = await apiClient.put(url, data, config);
      return { data: response.data, error: null };
    } catch (error) {
      return { data: null, error: handleError(error) };
    }
  },

  // PATCH request
  patch: async (url, data, config = {}) => {
    try {
      const response = await apiClient.patch(url, data, config);
      return { data: response.data, error: null };
    } catch (error) {
      return { data: null, error: handleError(error) };
    }
  },

  // DELETE request
  delete: async (url, config = {}) => {
    try {
      const response = await apiClient.delete(url, config);
      return { data: response.data, error: null };
    } catch (error) {
      return { data: null, error: handleError(error) };
    }
  },

  // File upload
  upload: async (url, file, onProgress = null) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress) {
            const percentCompleted = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            onProgress(percentCompleted);
          }
        },
      };

      const response = await apiClient.post(url, formData, config);
      return { data: response.data, error: null };
    } catch (error) {
      return { data: null, error: handleError(error) };
    }
  },
};

export default apiService;
