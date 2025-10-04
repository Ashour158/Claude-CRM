// frontend/src/services/api/auth.js
// Authentication API Service

import api from './base';

export const authAPI = {
  // Login
  login: (credentials) => api.post('/auth/login/', credentials),
  
  // Register
  register: (userData) => api.post('/auth/register/', userData),
  
  // Logout
  logout: () => api.post('/auth/logout/'),
  
  // Get current user
  getCurrentUser: () => api.get('/auth/me/'),
  
  // Refresh token
  refreshToken: () => api.post('/auth/refresh/'),
  
  // Change password
  changePassword: (data) => api.post('/auth/change-password/', data),
  
  // Request password reset
  requestPasswordReset: (email) => api.post('/auth/password-reset/', { email }),
  
  // Confirm password reset
  confirmPasswordReset: (data) => api.post('/auth/password-reset-confirm/', data),
  
  // Verify email
  verifyEmail: (token) => api.post('/auth/verify-email/', { token }),
  
  // Get user companies
  getUserCompanies: () => api.get('/auth/companies/'),
  
  // Switch company
  switchCompany: (companyId) => api.post('/auth/switch-company/', { company_id: companyId }),
};
