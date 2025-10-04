// src/api/contacts.js
// API client for Contacts endpoints

import apiClient from './client';

export const contactsAPI = {
  /**
   * Get all contacts with optional filters
   * @param {Object} params - Query parameters (search, page, page_size, filters)
   * @returns {Promise}
   */
  getAll: (params) => apiClient.get('/contacts/', { params }),
  
  /**
   * Get single contact by ID
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  getById: (id) => apiClient.get(`/contacts/${id}/`),
  
  /**
   * Create new contact
   * @param {Object} data - Contact data
   * @returns {Promise}
   */
  create: (data) => apiClient.post('/contacts/', data),
  
  /**
   * Update contact
   * @param {string} id - Contact UUID
   * @param {Object} data - Updated contact data
   * @returns {Promise}
   */
  update: (id, data) => apiClient.patch(`/contacts/${id}/`, data),
  
  /**
   * Delete contact
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  delete: (id) => apiClient.delete(`/contacts/${id}/`),
  
  /**
   * Get activities for a contact
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  getActivities: (id) => apiClient.get(`/contacts/${id}/activities/`),
  
  /**
   * Get deals for a contact
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  getDeals: (id) => apiClient.get(`/contacts/${id}/deals/`),
  
  /**
   * Get contact statistics
   * @returns {Promise}
   */
  getStats: () => apiClient.get('/contacts/stats/'),
  
  /**
   * Import contacts from CSV
   * @param {File} file - CSV file
   * @param {string} accountId - Optional account ID to associate contacts with
   * @returns {Promise}
   */
  import: (file, accountId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (accountId) {
      formData.append('account_id', accountId);
    }
    return apiClient.post('/contacts/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  
  /**
   * Export contacts to CSV
   * @param {Object} params - Filter parameters
   * @returns {Promise}
   */
  export: (params) => apiClient.get('/contacts/export/', { 
    params, 
    responseType: 'blob' 
  }),
  
  /**
   * Perform bulk action on multiple contacts
   * @param {Object} data - { contact_ids: [], action: string, owner_id?: string }
   * @returns {Promise}
   */
  bulkAction: (data) => apiClient.post('/contacts/bulk-action/', data),
  
  /**
   * Set contact as primary for its account
   * @param {string} id - Contact UUID
   * @returns {Promise}
   */
  setPrimary: (id) => apiClient.post(`/contacts/${id}/set-primary/`),
  
  /**
   * Merge two contacts
   * @param {string} targetId - Target contact UUID (will remain)
   * @param {string} sourceId - Source contact UUID (will be deleted)
   * @returns {Promise}
   */
  merge: (targetId, sourceId) => apiClient.post(`/contacts/${targetId}/merge/`, {
    source_contact_id: sourceId
  }),
};

export default contactsAPI;