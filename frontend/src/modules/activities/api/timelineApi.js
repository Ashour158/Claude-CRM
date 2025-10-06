// frontend/src/modules/activities/api/timelineApi.js
/**
 * Timeline/Activities API client
 */

export const timelineApi = {
  /**
   * Get timeline events for an entity
   * GET /api/v1/activities/timeline/
   */
  getTimeline: async (entityType, entityId, options = {}) => {
    const params = new URLSearchParams({
      entity_type: entityType,
      entity_id: entityId,
      limit: options.limit || 50,
      ...(options.eventTypes && { event_types: options.eventTypes.join(',') })
    });
    
    console.log('Fetching timeline:', params.toString());
    return Promise.resolve({
      count: 0,
      events: []
    });
  },

  /**
   * Record a new timeline event
   */
  recordEvent: async (eventData) => {
    console.log('Recording event:', eventData);
    return Promise.resolve(eventData);
  },

  /**
   * Get recent activities for organization
   */
  getRecent: async (days = 7, limit = 20) => {
    console.log('Fetching recent activities:', { days, limit });
    return Promise.resolve([]);
  }
};
