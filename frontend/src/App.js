// frontend/src/App.js
// Main React App Component

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from './store/store';

// Components
import MainLayout from './components/Layout/MainLayout';
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';
import Dashboard from './pages/Dashboard/Dashboard';
import AccountsList from './pages/Accounts/AccountsList';
import AccountDetail from './pages/Accounts/AccountDetail';
import ContactsList from './pages/Contacts/ContactsList';
import ContactDetail from './pages/Contacts/ContactDetail';
import LeadsList from './pages/Leads/LeadsList';
import LeadDetail from './pages/Leads/LeadDetail';
import DealsList from './pages/Deals/DealsList';
import DealDetail from './pages/Deals/DealDetail';
import ActivitiesList from './pages/Activities/ActivitiesList';
import TasksList from './pages/Tasks/TasksList';
import EventsList from './pages/Events/EventsList';
import ProductsList from './pages/Products/ProductsList';
import ProductDetail from './pages/Products/ProductDetail';
import TerritoriesList from './pages/Territories/TerritoriesList';
import TerritoryDetail from './pages/Territories/TerritoryDetail';

// Settings Components
import SettingsLayout from './pages/Settings/SettingsLayout';
import UserManagement from './pages/Settings/UserManagement';
import SystemConfiguration from './pages/Settings/SystemConfiguration';

// Hooks
import { useAuth } from './hooks/useAuth';

// Create theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#0066CC',
      light: '#4d94ff',
      dark: '#004499',
    },
    secondary: {
      main: '#ff6b35',
      light: '#ff8a65',
      dark: '#e64a19',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
      },
    },
  },
});

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

// Public Route Component (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) {
    return <div>Loading...</div>;
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Router>
            <Box sx={{ display: 'flex', minHeight: '100vh' }}>
              <Routes>
                {/* Public Routes */}
                <Route 
                  path="/login" 
                  element={
                    <PublicRoute>
                      <Login />
                    </PublicRoute>
                  } 
                />
                <Route 
                  path="/register" 
                  element={
                    <PublicRoute>
                      <Register />
                    </PublicRoute>
                  } 
                />
                
                {/* Protected Routes */}
                <Route 
                  path="/dashboard" 
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <Dashboard />
                      </MainLayout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Accounts */}
                <Route 
                  path="/accounts" 
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <AccountsList />
                      </MainLayout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/accounts/:id" 
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <AccountDetail />
                      </MainLayout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Contacts */}
                <Route 
                  path="/contacts" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ContactsList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/contacts/:id" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ContactDetail />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Leads */}
                <Route 
                  path="/leads" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <LeadsList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/leads/:id" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <LeadDetail />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Deals */}
                <Route 
                  path="/deals" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <DealsList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/deals/:id" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <DealDetail />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Activities */}
                <Route 
                  path="/activities" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ActivitiesList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Tasks */}
                <Route 
                  path="/tasks" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <TasksList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Events */}
                <Route 
                  path="/events" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <EventsList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Products */}
                <Route 
                  path="/products" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ProductsList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/products/:id" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <ProductDetail />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Territories */}
                <Route 
                  path="/territories" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <TerritoriesList />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/territories/:id" 
                  element={
                    <ProtectedRoute>
                      <Layout>
                        <TerritoryDetail />
                      </Layout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Settings */}
                <Route 
                  path="/settings/users" 
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <SettingsLayout>
                          <UserManagement />
                        </SettingsLayout>
                      </MainLayout>
                    </ProtectedRoute>
                  } 
                />
                <Route 
                  path="/settings/system" 
                  element={
                    <ProtectedRoute>
                      <MainLayout>
                        <SettingsLayout>
                          <SystemConfiguration />
                        </SettingsLayout>
                      </MainLayout>
                    </ProtectedRoute>
                  } 
                />
                
                {/* Default redirect */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Box>
          </Router>
        </ThemeProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
