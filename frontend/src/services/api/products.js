// frontend/src/services/api/products.js
// Products API Service

import api from './base';

export const productsAPI = {
  // Products
  products: {
    getAll: (params) => api.get('/products/products/', { params }),
    getById: (id) => api.get(`/products/products/${id}/`),
    create: (data) => api.post('/products/products/', data),
    update: (id, data) => api.put(`/products/products/${id}/`, data),
    delete: (id) => api.delete(`/products/products/${id}/`),
    getPriceLists: (id) => api.get(`/products/products/${id}/price-lists/`),
    addToPriceList: (id, data) => api.post(`/products/products/${id}/add-to-price-list/`, data),
    getInventory: (id) => api.get(`/products/products/${id}/inventory/`),
    adjustInventory: (id, data) => api.post(`/products/products/${id}/adjust-inventory/`, data),
    getLowStock: () => api.get('/products/products/low-stock/'),
    getByCategory: () => api.get('/products/products/by-category/'),
    getStats: (params) => api.get('/products/products/stats/', { params }),
  },
  
  // Product Categories
  categories: {
    getAll: (params) => api.get('/products/categories/', { params }),
    getById: (id) => api.get(`/products/categories/${id}/`),
    create: (data) => api.post('/products/categories/', data),
    update: (id, data) => api.put(`/products/categories/${id}/`, data),
    delete: (id) => api.delete(`/products/categories/${id}/`),
    getProducts: (id) => api.get(`/products/categories/${id}/products/`),
    getChildren: (id) => api.get(`/products/categories/${id}/children/`),
    getHierarchy: (id) => api.get(`/products/categories/${id}/hierarchy/`),
  },
  
  // Price Lists
  priceLists: {
    getAll: (params) => api.get('/products/price-lists/', { params }),
    getById: (id) => api.get(`/products/price-lists/${id}/`),
    create: (data) => api.post('/products/price-lists/', data),
    update: (id, data) => api.put(`/products/price-lists/${id}/`, data),
    delete: (id) => api.delete(`/products/price-lists/${id}/`),
    getItems: (id) => api.get(`/products/price-lists/${id}/items/`),
    addItem: (id, data) => api.post(`/products/price-lists/${id}/add-item/`, data),
    getPricing: (id, params) => api.get(`/products/price-lists/${id}/pricing/`, { params }),
    getForTerritory: (params) => api.get('/products/price-lists/for-territory/', { params }),
    getForAccount: (params) => api.get('/products/price-lists/for-account/', { params }),
  },
};
