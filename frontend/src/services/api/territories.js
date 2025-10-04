// frontend/src/services/api/territories.js
// Territories API Service

import api from './base';

export const territoriesAPI = {
  // Territories
  territories: {
    getAll: (params) => api.get('/territories/territories/', { params }),
    getById: (id) => api.get(`/territories/territories/${id}/`),
    create: (data) => api.post('/territories/territories/', data),
    update: (id, data) => api.put(`/territories/territories/${id}/`, data),
    delete: (id) => api.delete(`/territories/territories/${id}/`),
    getChildren: (id) => api.get(`/territories/territories/${id}/children/`),
    getUsers: (id) => api.get(`/territories/territories/${id}/users/`),
    getAccounts: (id) => api.get(`/territories/territories/${id}/accounts/`),
    getLeads: (id) => api.get(`/territories/territories/${id}/leads/`),
    getDeals: (id) => api.get(`/territories/territories/${id}/deals/`),
    getStats: (id) => api.get(`/territories/territories/${id}/stats/`),
    assignUser: (id, data) => api.post(`/territories/territories/${id}/assign-user/`, data),
    removeUser: (id, data) => api.post(`/territories/territories/${id}/remove-user/`, data),
  },
  
  // Territory Rules
  rules: {
    getAll: (params) => api.get('/territories/rules/', { params }),
    getById: (id) => api.get(`/territories/rules/${id}/`),
    create: (data) => api.post('/territories/rules/', data),
    update: (id, data) => api.put(`/territories/rules/${id}/`, data),
    delete: (id) => api.delete(`/territories/rules/${id}/`),
    testRule: (id, data) => api.post(`/territories/rules/${id}/test-rule/`, data),
    applyRule: (id, data) => api.post(`/territories/rules/${id}/apply-rule/`, data),
  },
};
