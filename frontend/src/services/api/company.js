// frontend/src/services/api/company.js
// Company API Service

import api from './base';

export const companyAPI = {
  // Get user companies
  getCompanies: () => api.get('/auth/companies/'),
  
  // Get current company
  getCurrentCompany: () => api.get('/auth/current-company/'),
  
  // Switch company
  switchCompany: (companyId) => api.post('/auth/switch-company/', { company_id: companyId }),
  
  // Get company details
  getCompanyDetails: (companyId) => api.get(`/companies/${companyId}/`),
  
  // Update company
  updateCompany: (companyId, data) => api.put(`/companies/${companyId}/`, data),
  
  // Get company users
  getCompanyUsers: (companyId) => api.get(`/companies/${companyId}/users/`),
  
  // Add user to company
  addUserToCompany: (companyId, data) => api.post(`/companies/${companyId}/users/`, data),
  
  // Remove user from company
  removeUserFromCompany: (companyId, userId) => api.delete(`/companies/${companyId}/users/${userId}/`),
  
  // Update user access
  updateUserAccess: (companyId, userId, data) => api.put(`/companies/${companyId}/users/${userId}/`, data),
};
