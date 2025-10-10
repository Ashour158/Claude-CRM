// frontend/src/services/userManagementService.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

class UserManagementService {
  // User Management
  async getUsers(params = {}) {
    const response = await apiClient.get('/core/users/', { params });
    return response.data;
  }

  async getUserById(userId) {
    const response = await apiClient.get(`/core/users/${userId}/`);
    return response.data;
  }

  async createUser(userData) {
    const response = await apiClient.post('/core/users/', userData);
    return response.data;
  }

  async updateUser(userId, userData) {
    const response = await apiClient.put(`/core/users/${userId}/`, userData);
    return response.data;
  }

  async deleteUser(userId) {
    const response = await apiClient.delete(`/core/users/${userId}/`);
    return response.data;
  }

  async getUserStatistics() {
    const response = await apiClient.get('/core/users/statistics/');
    return response.data;
  }

  async bulkUserAction(userIds, action) {
    const response = await apiClient.post('/core/users/bulk_action/', {
      user_ids: userIds,
      action: action,
    });
    return response.data;
  }

  async getUserActivities(userId) {
    const response = await apiClient.get(`/core/users/${userId}/activities/`);
    return response.data;
  }

  // Permission Management
  async getPermissions(params = {}) {
    const response = await apiClient.get('/core/permissions/', { params });
    return response.data;
  }

  // Role Management
  async getRoles(params = {}) {
    const response = await apiClient.get('/core/roles/', { params });
    return response.data;
  }

  async getRoleById(roleId) {
    const response = await apiClient.get(`/core/roles/${roleId}/`);
    return response.data;
  }

  async createRole(roleData) {
    const response = await apiClient.post('/core/roles/', roleData);
    return response.data;
  }

  async updateRole(roleId, roleData) {
    const response = await apiClient.put(`/core/roles/${roleId}/`, roleData);
    return response.data;
  }

  async deleteRole(roleId) {
    const response = await apiClient.delete(`/core/roles/${roleId}/`);
    return response.data;
  }

  async assignPermissionsToRole(roleId, permissionIds) {
    const response = await apiClient.post(
      `/core/roles/${roleId}/assign_permissions/`,
      { permission_ids: permissionIds }
    );
    return response.data;
  }

  // User Role Assignment
  async getUserRoles(params = {}) {
    const response = await apiClient.get('/core/user-roles/', { params });
    return response.data;
  }

  async assignRoleToUser(userId, roleId, data = {}) {
    const response = await apiClient.post('/core/user-roles/', {
      user: userId,
      role: roleId,
      ...data,
    });
    return response.data;
  }

  async removeUserRole(userRoleId) {
    const response = await apiClient.delete(`/core/user-roles/${userRoleId}/`);
    return response.data;
  }

  // User Activity
  async getActivities(params = {}) {
    const response = await apiClient.get('/core/user-activities/', { params });
    return response.data;
  }

  // User Preferences
  async getMyPreferences() {
    const response = await apiClient.get('/core/user-preferences/my_preferences/');
    return response.data;
  }

  async updateMyPreferences(preferences) {
    const response = await apiClient.patch(
      '/core/user-preferences/update_my_preferences/',
      preferences
    );
    return response.data;
  }

  // User Invitations
  async getInvitations(params = {}) {
    const response = await apiClient.get('/core/user-invitations/', { params });
    return response.data;
  }

  async createInvitation(invitationData) {
    const response = await apiClient.post('/core/user-invitations/', invitationData);
    return response.data;
  }

  async resendInvitation(invitationId) {
    const response = await apiClient.post(`/core/user-invitations/${invitationId}/resend/`);
    return response.data;
  }

  async cancelInvitation(invitationId) {
    const response = await apiClient.post(`/core/user-invitations/${invitationId}/cancel/`);
    return response.data;
  }

  // Export/Import
  async exportUsers(format = 'csv') {
    const response = await apiClient.get('/core/users/export/', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  async importUsers(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/core/users/import/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
}

export default new UserManagementService();
