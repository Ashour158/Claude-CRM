// frontend/src/services/api/deals.js
// Deals API Service

import api from './base';

export const dealsAPI = {
  // Deals
  deals: {
    getAll: (params) => api.get('/deals/deals/', { params }),
    getById: (id) => api.get(`/deals/deals/${id}/`),
    create: (data) => api.post('/deals/deals/', data),
    update: (id, data) => api.put(`/deals/deals/${id}/`, data),
    delete: (id) => api.delete(`/deals/deals/${id}/`),
    win: (id, data) => api.post(`/deals/deals/${id}/win/`, data),
    lose: (id, data) => api.post(`/deals/deals/${id}/lose/`, data),
    convert: (id, data) => api.post(`/deals/deals/${id}/convert/`, data),
    getProducts: (id) => api.get(`/deals/deals/${id}/products/`),
    addProduct: (id, data) => api.post(`/deals/deals/${id}/add-product/`, data),
    getCompetitors: (id) => api.get(`/deals/deals/${id}/competitors/`),
    addCompetitor: (id, data) => api.post(`/deals/deals/${id}/add-competitor/`, data),
    getNotes: (id) => api.get(`/deals/deals/${id}/notes/`),
    addNote: (id, data) => api.post(`/deals/deals/${id}/add-note/`, data),
    getPipeline: () => api.get('/deals/deals/pipeline/'),
    getOverdue: () => api.get('/deals/deals/overdue/'),
    getClosingSoon: () => api.get('/deals/deals/closing-soon/'),
    getMyDeals: () => api.get('/deals/deals/my-deals/'),
    getStats: (params) => api.get('/deals/deals/stats/', { params }),
  },
  
  // Pipeline Stages
  stages: {
    getAll: (params) => api.get('/deals/pipeline-stages/', { params }),
    getById: (id) => api.get(`/deals/pipeline-stages/${id}/`),
    create: (data) => api.post('/deals/pipeline-stages/', data),
    update: (id, data) => api.put(`/deals/pipeline-stages/${id}/`, data),
    delete: (id) => api.delete(`/deals/pipeline-stages/${id}/`),
    getDeals: (id) => api.get(`/deals/pipeline-stages/${id}/deals/`),
    reorder: (id, data) => api.post(`/deals/pipeline-stages/${id}/reorder/`, data),
  },
};
