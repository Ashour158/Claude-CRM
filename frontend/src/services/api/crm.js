// frontend/src/services/api/crm.js
// CRM API Service

import api from './base';

export const crmAPI = {
  // Accounts
  accounts: {
    getAll: (params) => api.get('/crm/accounts/', { params }),
    getById: (id) => api.get(`/crm/accounts/${id}/`),
    create: (data) => api.post('/crm/accounts/', data),
    update: (id, data) => api.put(`/crm/accounts/${id}/`, data),
    delete: (id) => api.delete(`/crm/accounts/${id}/`),
    getContacts: (id) => api.get(`/crm/accounts/${id}/contacts/`),
    getDeals: (id) => api.get(`/crm/accounts/${id}/deals/`),
    getActivities: (id) => api.get(`/crm/accounts/${id}/activities/`),
    getStats: (id) => api.get(`/crm/accounts/${id}/stats/`),
    import: (data) => api.post('/crm/accounts/import/', data),
    export: (params) => api.get('/crm/accounts/export/', { params, responseType: 'blob' }),
    assignTerritory: (id, territoryId) => api.post(`/crm/accounts/${id}/assign-territory/`, { territory_id: territoryId }),
    assignOwner: (id, ownerId) => api.post(`/crm/accounts/${id}/assign-owner/`, { owner_id: ownerId }),
  },
  
  // Contacts
  contacts: {
    getAll: (params) => api.get('/crm/contacts/', { params }),
    getById: (id) => api.get(`/crm/contacts/${id}/`),
    create: (data) => api.post('/crm/contacts/', data),
    update: (id, data) => api.put(`/crm/contacts/${id}/`, data),
    delete: (id) => api.delete(`/crm/contacts/${id}/`),
    getActivities: (id) => api.get(`/crm/contacts/${id}/activities/`),
    getDeals: (id) => api.get(`/crm/contacts/${id}/deals/`),
    getStats: (id) => api.get(`/crm/contacts/${id}/stats/`),
    import: (data) => api.post('/crm/contacts/import/', data),
    export: (params) => api.get('/crm/contacts/export/', { params, responseType: 'blob' }),
    bulkAction: (data) => api.post('/crm/contacts/bulk-action/', data),
    setPrimary: (id) => api.post(`/crm/contacts/${id}/set-primary/`),
    merge: (id, data) => api.post(`/crm/contacts/${id}/merge/`, data),
  },
  
  // Leads
  leads: {
    getAll: (params) => api.get('/crm/leads/', { params }),
    getById: (id) => api.get(`/crm/leads/${id}/`),
    create: (data) => api.post('/crm/leads/', data),
    update: (id, data) => api.put(`/crm/leads/${id}/`, data),
    delete: (id) => api.delete(`/crm/leads/${id}/`),
    convert: (id, data) => api.post(`/crm/leads/${id}/convert/`, data),
    qualify: (id) => api.post(`/crm/leads/${id}/qualify/`),
    disqualify: (id) => api.post(`/crm/leads/${id}/disqualify/`),
    score: (id) => api.post(`/crm/leads/${id}/score/`),
    getStats: (id) => api.get(`/crm/leads/${id}/stats/`),
    import: (data) => api.post('/crm/leads/import/', data),
    export: (params) => api.get('/crm/leads/export/', { params, responseType: 'blob' }),
    bulkAction: (data) => api.post('/crm/leads/bulk-action/', data),
  },
};
