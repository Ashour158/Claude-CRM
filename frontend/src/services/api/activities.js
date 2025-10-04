// frontend/src/services/api/activities.js
// Activities API Service

import api from './base';

export const activitiesAPI = {
  // Activities
  activities: {
    getAll: (params) => api.get('/activities/activities/', { params }),
    getById: (id) => api.get(`/activities/activities/${id}/`),
    create: (data) => api.post('/activities/activities/', data),
    update: (id, data) => api.put(`/activities/activities/${id}/`, data),
    delete: (id) => api.delete(`/activities/activities/${id}/`),
    getByType: (params) => api.get('/activities/activities/by-type/', { params }),
    getByStatus: (params) => api.get('/activities/activities/by-status/', { params }),
    getRecent: (params) => api.get('/activities/activities/recent/', { params }),
    getStats: (params) => api.get('/activities/activities/stats/', { params }),
  },
  
  // Tasks
  tasks: {
    getAll: (params) => api.get('/activities/tasks/', { params }),
    getById: (id) => api.get(`/activities/tasks/${id}/`),
    create: (data) => api.post('/activities/tasks/', data),
    update: (id, data) => api.put(`/activities/tasks/${id}/`, data),
    delete: (id) => api.delete(`/activities/tasks/${id}/`),
    complete: (id, data) => api.post(`/activities/tasks/${id}/complete/`, data),
    reopen: (id) => api.post(`/activities/tasks/${id}/reopen/`),
    getOverdue: () => api.get('/activities/tasks/overdue/'),
    getDueToday: () => api.get('/activities/tasks/due-today/'),
    getMyTasks: () => api.get('/activities/tasks/my-tasks/'),
    getStats: (params) => api.get('/activities/tasks/stats/', { params }),
  },
  
  // Events
  events: {
    getAll: (params) => api.get('/activities/events/', { params }),
    getById: (id) => api.get(`/activities/events/${id}/`),
    create: (data) => api.post('/activities/events/', data),
    update: (id, data) => api.put(`/activities/events/${id}/`, data),
    delete: (id) => api.delete(`/activities/events/${id}/`),
    getCalendar: (params) => api.get('/activities/events/calendar/', { params }),
    getUpcoming: () => api.get('/activities/events/upcoming/'),
    getMyEvents: () => api.get('/activities/events/my-events/'),
    cancel: (id) => api.post(`/activities/events/${id}/cancel/`),
    getStats: (params) => api.get('/activities/events/stats/', { params }),
  },
};
