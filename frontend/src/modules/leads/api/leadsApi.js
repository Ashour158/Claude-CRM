// frontend/src/modules/leads/api/leadsApi.js
/**
 * Leads API client
 */

export const leadsApi = {
  list: async (filters = {}) => {
    console.log('Fetching leads with filters:', filters);
    return Promise.resolve({ data: [], total: 0 });
  },

  getById: async (leadId) => {
    console.log('Fetching lead:', leadId);
    return Promise.resolve(null);
  },

  create: async (leadData) => {
    console.log('Creating lead:', leadData);
    return Promise.resolve(leadData);
  },

  update: async (leadId, leadData) => {
    console.log('Updating lead:', leadId, leadData);
    return Promise.resolve(leadData);
  },

  /**
   * Convert lead to account/contact/deal
   */
  convert: async (leadId, options = {}) => {
    // POST /api/v1/leads/convert/
    console.log('Converting lead:', leadId, options);
    return Promise.resolve({
      success: true,
      account: {},
      contact: {},
      deal: null
    });
  },

  calculateScore: async (leadId) => {
    console.log('Calculating lead score:', leadId);
    return Promise.resolve({ score: 0 });
  }
};
