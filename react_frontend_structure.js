// ========================================
// REACT FRONTEND PROJECT STRUCTURE
// Complete folder organization
// ========================================

/*
crm-frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── api/                      # API client and services
│   │   ├── client.js             # Axios instance with interceptors
│   │   ├── auth.js               # Authentication API calls
│   │   ├── accounts.js           # Accounts API
│   │   ├── contacts.js           # Contacts API
│   │   ├── leads.js              # Leads API
│   │   ├── deals.js              # Deals API
│   │   ├── quotes.js             # Quotes API
│   │   ├── salesOrders.js        # Sales Orders API
│   │   ├── vendors.js            # Vendors API
│   │   ├── territories.js        # Territories API
│   │   └── reports.js            # Reports API
│   │
│   ├── components/               # Reusable components
│   │   ├── common/              # Common UI components
│   │   │   ├── Button.jsx
│   │   │   ├── Input.jsx
│   │   │   ├── Select.jsx
│   │   │   ├── Modal.jsx
│   │   │   ├── Table.jsx
│   │   │   ├── Pagination.jsx
│   │   │   ├── SearchBar.jsx
│   │   │   ├── FilterPanel.jsx
│   │   │   ├── LoadingSpinner.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   ├── ErrorBoundary.jsx
│   │   │   └── Toast.jsx
│   │   │
│   │   ├── layout/              # Layout components
│   │   │   ├── Sidebar.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Footer.jsx
│   │   │   ├── MainLayout.jsx
│   │   │   └── CompanySwitcher.jsx
│   │   │
│   │   ├── forms/               # Form components
│   │   │   ├── AccountForm.jsx
│   │   │   ├── ContactForm.jsx
│   │   │   ├── LeadForm.jsx
│   │   │   ├── DealForm.jsx
│   │   │   ├── QuoteForm.jsx
│   │   │   ├── VendorForm.jsx
│   │   │   └── FormField.jsx
│   │   │
│   │   ├── cards/               # Card components
│   │   │   ├── AccountCard.jsx
│   │   │   ├── ContactCard.jsx
│   │   │   ├── DealCard.jsx
│   │   │   ├── StatCard.jsx
│   │   │   └── ActivityCard.jsx
│   │   │
│   │   ├── charts/              # Chart components
│   │   │   ├── PipelineChart.jsx
│   │   │   ├── RevenueChart.jsx
│   │   │   ├── ConversionFunnel.jsx
│   │   │   ├── TerritoryMap.jsx
│   │   │   └── DSOTrendChart.jsx
│   │   │
│   │   └── widgets/             # Dashboard widgets
│   │       ├── PipelineWidget.jsx
│   │       ├── TasksWidget.jsx
│   │       ├── ActivitiesWidget.jsx
│   │       ├── QuotaWidget.jsx
│   │       └── RevenueWidget.jsx
│   │
│   ├── pages/                   # Page components
│   │   ├── Auth/
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── ForgotPassword.jsx
│   │   │   └── ResetPassword.jsx
│   │   │
│   │   ├── Dashboard/
│   │   │   ├── Dashboard.jsx
│   │   │   └── widgets/
│   │   │
│   │   ├── Accounts/
│   │   │   ├── AccountsList.jsx
│   │   │   ├── AccountDetail.jsx
│   │   │   ├── CreateAccount.jsx
│   │   │   └── EditAccount.jsx
│   │   │
│   │   ├── Contacts/
│   │   │   ├── ContactsList.jsx
│   │   │   ├── ContactDetail.jsx
│   │   │   ├── CreateContact.jsx
│   │   │   └── EditContact.jsx
│   │   │
│   │   ├── Leads/
│   │   │   ├── LeadsList.jsx
│   │   │   ├── LeadDetail.jsx
│   │   │   ├── CreateLead.jsx
│   │   │   ├── EditLead.jsx
│   │   │   └── ConvertLead.jsx
│   │   │
│   │   ├── Deals/
│   │   │   ├── DealsList.jsx
│   │   │   ├── DealDetail.jsx
│   │   │   ├── CreateDeal.jsx
│   │   │   ├── EditDeal.jsx
│   │   │   ├── PipelineKanban.jsx
│   │   │   └── Forecast.jsx
│   │   │
│   │   ├── Quotes/
│   │   │   ├── QuotesList.jsx
│   │   │   ├── QuoteDetail.jsx
│   │   │   ├── CreateQuote.jsx
│   │   │   ├── EditQuote.jsx
│   │   │   ├── QuoteApproval.jsx
│   │   │   └── QuotePreview.jsx
│   │   │
│   │   ├── RFQ/
│   │   │   ├── RFQList.jsx
│   │   │   ├── CreateRFQ.jsx
│   │   │   ├── RFQDetail.jsx
│   │   │   └── ConvertRFQToQuote.jsx
│   │   │
│   │   ├── SalesOrders/
│   │   │   ├── SalesOrdersList.jsx
│   │   │   ├── SalesOrderDetail.jsx
│   │   │   ├── CreateSalesOrder.jsx
│   │   │   └── Shipments.jsx
│   │   │
│   │   ├── Invoices/
│   │   │   ├── InvoicesList.jsx
│   │   │   ├── InvoiceDetail.jsx
│   │   │   ├── CreateInvoice.jsx
│   │   │   ├── AgingReport.jsx
│   │   │   └── DSOReport.jsx
│   │   │
│   │   ├── Vendors/
│   │   │   ├── VendorsList.jsx
│   │   │   ├── VendorDetail.jsx
│   │   │   ├── CreateVendor.jsx
│   │   │   ├── EditVendor.jsx
│   │   │   ├── VendorScorecard.jsx
│   │   │   └── VendorPerformance.jsx
│   │   │
│   │   ├── Procurement/
│   │   │   ├── PurchaseRequisitions.jsx
│   │   │   ├── VendorRFQs.jsx
│   │   │   ├── VendorQuoteComparison.jsx
│   │   │   └── PurchaseOrders.jsx
│   │   │
│   │   ├── Territories/
│   │   │   ├── TerritoriesList.jsx
│   │   │   ├── TerritoryDetail.jsx
│   │   │   ├── TerritoryHierarchy.jsx
│   │   │   ├── TerritoryRules.jsx
│   │   │   └── TerritoryPerformance.jsx
│   │   │
│   │   ├── Products/
│   │   │   ├── ProductsList.jsx
│   │   │   ├── ProductDetail.jsx
│   │   │   ├── CreateProduct.jsx
│   │   │   ├── EditProduct.jsx
│   │   │   └── PriceLists.jsx
│   │   │
│   │   ├── Activities/
│   │   │   ├── ActivitiesList.jsx
│   │   │   ├── ActivityTimeline.jsx
│   │   │   └── LogActivity.jsx
│   │   │
│   │   ├── Tasks/
│   │   │   ├── TasksList.jsx
│   │   │   ├── MyTasks.jsx
│   │   │   ├── TodayTasks.jsx
│   │   │   └── OverdueTasks.jsx
│   │   │
│   │   ├── Calendar/
│   │   │   ├── Calendar.jsx
│   │   │   └── EventDetail.jsx
│   │   │
│   │   ├── Reports/
│   │   │   ├── ReportsDashboard.jsx
│   │   │   ├── PipelineReport.jsx
│   │   │   ├── SalesForecast.jsx
│   │   │   ├── TerritoryReport.jsx
│   │   │   ├── ConversionReport.jsx
│   │   │   ├── DSOReport.jsx
│   │   │   ├── VendorPerformanceReport.jsx
│   │   │   └── CustomReportBuilder.jsx
│   │   │
│   │   ├── Settings/
│   │   │   ├── Profile.jsx
│   │   │   ├── CompanySettings.jsx
│   │   │   ├── UserManagement.jsx
│   │   │   ├── PipelineStages.jsx
│   │   │   ├── CustomFields.jsx
│   │   │   ├── EmailTemplates.jsx
│   │   │   ├── DocumentTemplates.jsx
│   │   │   ├── WorkflowRules.jsx
│   │   │   └── Integrations.jsx
│   │   │
│   │   └── NotFound.jsx
│   │
│   ├── context/                 # React Context
│   │   ├── AuthContext.jsx      # Authentication context
│   │   ├── CompanyContext.jsx   # Active company context
│   │   ├── ThemeContext.jsx     # Theme/dark mode
│   │   └── NotificationContext.jsx
│   │
│   ├── hooks/                   # Custom hooks
│   │   ├── useAuth.js
│   │   ├── useCompany.js
│   │   ├── useDebounce.js
│   │   ├── useLocalStorage.js   # DO NOT USE - browser storage not supported
│   │   ├── usePagination.js
│   │   ├── useTable.js
│   │   ├── useForm.js
│   │   └── useApi.js
│   │
│   ├── utils/                   # Utility functions
│   │   ├── formatters.js        # Date, currency, number formatters
│   │   ├── validators.js        # Form validation
│   │   ├── helpers.js           # General helpers
│   │   ├── constants.js         # App constants
│   │   └── permissions.js       # Permission checking
│   │
│   ├── routes/                  # Routing
│   │   ├── index.js             # Main router
│   │   ├── PrivateRoute.jsx     # Protected routes
│   │   └── PublicRoute.jsx      # Public routes
│   │
│   ├── styles/                  # Global styles
│   │   ├── index.css            # Main CSS with Tailwind
│   │   ├── variables.css        # CSS variables
│   │   └── animations.css       # Custom animations
│   │
│   ├── App.jsx                  # Main App component
│   ├── index.js                 # Entry point
│   └── setupTests.js            # Test setup
│
├── .env.example                 # Environment variables template
├── .env.development
├── .env.production
├── .gitignore
├── package.json
├── tailwind.config.js
├── postcss.config.js
└── README.md
*/

// ========================================
// KEY FILES EXAMPLES
// ========================================

// ============ api/client.js ============
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config) => {
    // CRITICAL: Cannot use localStorage in Claude artifacts
    // In production, get token from React state/context
    const token = null; // Get from AuthContext instead
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle token expiration - redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// ============ api/accounts.js ============
import apiClient from './client';

export const accountsAPI = {
  getAll: (params) => apiClient.get('/accounts/', { params }),
  getById: (id) => apiClient.get(`/accounts/${id}/`),
  create: (data) => apiClient.post('/accounts/', data),
  update: (id, data) => apiClient.patch(`/accounts/${id}/`, data),
  delete: (id) => apiClient.delete(`/accounts/${id}/`),
  getContacts: (id) => apiClient.get(`/accounts/${id}/contacts/`),
  getDeals: (id) => apiClient.get(`/accounts/${id}/deals/`),
  getActivities: (id) => apiClient.get(`/accounts/${id}/activities/`),
  import: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/accounts/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  export: (params) => apiClient.get('/accounts/export/', { 
    params, 
    responseType: 'blob' 
  }),
};

// ============ context/AuthContext.jsx ============
import React, { createContext, useState, useEffect } from 'react';
import { authAPI } from '../api/auth';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Check if user is already logged in
    // In production, check token validity
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      // Verify token and get user info
      const response = await authAPI.me();
      setUser(response.data);
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    const response = await authAPI.login(email, password);
    setToken(response.data.access_token);
    setUser(response.data.user);
    return response.data;
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } finally {
      setUser(null);
      setToken(null);
    }
  };

  const register = async (userData) => {
    const response = await authAPI.register(userData);
    return response.data;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        register,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// ============ context/CompanyContext.jsx ============
import React, { createContext, useState, useEffect, useContext } from 'react';
import { AuthContext } from './AuthContext';
import { companyAPI } from '../api/company';

export const CompanyContext = createContext();

export const CompanyProvider = ({ children }) => {
  const { user, isAuthenticated } = useContext(AuthContext);
  const [activeCompany, setActiveCompany] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isAuthenticated) {
      loadCompanies();
    }
  }, [isAuthenticated]);

  const loadCompanies = async () => {
    try {
      const response = await companyAPI.getUserCompanies();
      setCompanies(response.data);
      
      // Set active company (primary or first)
      const primary = response.data.find(c => c.is_primary);
      setActiveCompany(primary || response.data[0]);
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const switchCompany = async (companyId) => {
    try {
      await companyAPI.switchCompany(companyId);
      const company = companies.find(c => c.id === companyId);
      setActiveCompany(company);
      
      // Reload page to refresh data for new company
      window.location.reload();
    } catch (error) {
      console.error('Failed to switch company:', error);
      throw error;
    }
  };

  return (
    <CompanyContext.Provider
      value={{
        activeCompany,
        companies,
        loading,
        switchCompany,
      }}
    >
      {children}
    </CompanyContext.Provider>
  );
};

// ============ hooks/useAuth.js ============
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// ============ routes/index.js ============
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import PrivateRoute from './PrivateRoute';
import PublicRoute from './PublicRoute';

// Auth pages
import Login from '../pages/Auth/Login';
import Register from '../pages/Auth/Register';

// Main pages
import Dashboard from '../pages/Dashboard/Dashboard';
import AccountsList from '../pages/Accounts/AccountsList';
import AccountDetail from '../pages/Accounts/AccountDetail';
import ContactsList from '../pages/Contacts/ContactsList';
import LeadsList from '../pages/Leads/LeadsList';
import DealsList from '../pages/Deals/DealsList';
import PipelineKanban from '../pages/Deals/PipelineKanban';
// ... import other pages

const AppRoutes = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
        <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
        
        {/* Private routes */}
        <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        
        {/* Accounts */}
        <Route path="/accounts" element={<PrivateRoute><AccountsList /></PrivateRoute>} />
        <Route path="/accounts/:id" element={<PrivateRoute><AccountDetail /></PrivateRoute>} />
        
        {/* Contacts */}
        <Route path="/contacts" element={<PrivateRoute><ContactsList /></PrivateRoute>} />
        
        {/* Leads */}
        <Route path="/leads" element={<PrivateRoute><LeadsList /></PrivateRoute>} />
        
        {/* Deals */}
        <Route path="/deals" element={<PrivateRoute><DealsList /></PrivateRoute>} />
        <Route path="/deals/pipeline" element={<PrivateRoute><PipelineKanban /></PrivateRoute>} />
        
        {/* ... more routes ... */}
        
        {/* 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRoutes;

// ============ App.jsx ============
import React from 'react';
import { AuthProvider } from './context/AuthContext';
import { CompanyProvider } from './context/CompanyContext';
import { ThemeProvider } from './context/ThemeContext';
import AppRoutes from './routes';
import './styles/index.css';

function App() {
  return (
    <AuthProvider>
      <CompanyProvider>
        <ThemeProvider>
          <AppRoutes />
        </ThemeProvider>
      </CompanyProvider>
    </AuthProvider>
  );
}

export default App;

// ========================================
// PACKAGE.JSON DEPENDENCIES
// ========================================

/*
{
  "name": "enterprise-crm-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0",
    "tailwindcss": "^3.3.0",
    "recharts": "^2.10.0",
    "date-fns": "^2.30.0",
    "react-hook-form": "^7.48.0",
    "react-query": "^3.39.0",
    "zustand": "^4.4.0",
    "lucide-react": "^0.263.1",
    "react-hot-toast": "^2.4.1",
    "react-beautiful-dnd": "^13.1.1",
    "react-datepicker": "^4.21.0"
  }
}
*/