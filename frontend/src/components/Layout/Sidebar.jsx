// frontend/src/components/Layout/Sidebar.jsx
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Typography,
  Divider,
} from '@mui/material';
import {
  Dashboard,
  Business,
  Contacts,
  PersonAdd,
  TrendingUp,
  Assignment,
  Task,
  Event,
  Inventory,
  AttachMoney,
  ShoppingCart,
  Receipt,
  Store,
  Assessment,
  Campaign,
  Public,
  Settings,
  ExpandLess,
  ExpandMore,
} from '@mui/icons-material';

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [openMenus, setOpenMenus] = useState({});

  const handleMenuToggle = (menu) => {
    setOpenMenus(prev => ({
      ...prev,
      [menu]: !prev[menu]
    }));
  };

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <Dashboard />,
      path: '/dashboard',
    },
    {
      id: 'crm',
      label: 'CRM Core',
      icon: <Business />,
      children: [
        { label: 'Accounts', icon: <Business />, path: '/accounts' },
        { label: 'Contacts', icon: <Contacts />, path: '/contacts' },
        { label: 'Leads', icon: <PersonAdd />, path: '/leads' },
      ],
    },
    {
      id: 'sales',
      label: 'Sales',
      icon: <TrendingUp />,
      children: [
        { label: 'Deals', icon: <TrendingUp />, path: '/deals' },
        { label: 'Activities', icon: <Assignment />, path: '/activities' },
        { label: 'Tasks', icon: <Task />, path: '/tasks' },
        { label: 'Events', icon: <Event />, path: '/events' },
      ],
    },
    {
      id: 'products',
      label: 'Products',
      icon: <Inventory />,
      children: [
        { label: 'Products', icon: <Inventory />, path: '/products' },
        { label: 'Price Lists', icon: <AttachMoney />, path: '/price-lists' },
        { label: 'Categories', icon: <Inventory />, path: '/product-categories' },
      ],
    },
    {
      id: 'sales-documents',
      label: 'Sales Documents',
      icon: <Receipt />,
      children: [
        { label: 'Quotes', icon: <Receipt />, path: '/quotes' },
        { label: 'Sales Orders', icon: <ShoppingCart />, path: '/sales-orders' },
        { label: 'Invoices', icon: <Receipt />, path: '/invoices' },
        { label: 'Payments', icon: <AttachMoney />, path: '/payments' },
      ],
    },
    {
      id: 'vendors',
      label: 'Vendors',
      icon: <Store />,
      children: [
        { label: 'Vendors', icon: <Store />, path: '/vendors' },
        { label: 'Purchase Orders', icon: <ShoppingCart />, path: '/purchase-orders' },
        { label: 'Procurement', icon: <Store />, path: '/procurement' },
      ],
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: <Assessment />,
      children: [
        { label: 'Reports', icon: <Assessment />, path: '/reports' },
        { label: 'Dashboards', icon: <Dashboard />, path: '/dashboards' },
        { label: 'Charts', icon: <Assessment />, path: '/charts' },
      ],
    },
    {
      id: 'marketing',
      label: 'Marketing',
      icon: <Campaign />,
      children: [
        { label: 'Campaigns', icon: <Campaign />, path: '/campaigns' },
        { label: 'Email Marketing', icon: <Campaign />, path: '/email-marketing' },
        { label: 'Lead Scoring', icon: <PersonAdd />, path: '/lead-scoring' },
        { label: 'Marketing Analytics', icon: <Assessment />, path: '/marketing-analytics' },
      ],
    },
    {
      id: 'territories',
      label: 'Territories',
      icon: <Public />,
      children: [
        { label: 'Territories', icon: <Public />, path: '/territories' },
        { label: 'Territory Rules', icon: <Public />, path: '/territory-rules' },
      ],
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: <Settings />,
      children: [
        { label: 'User Management', icon: <Contacts />, path: '/settings/users' },
        { label: 'Company Settings', icon: <Business />, path: '/settings/company' },
        { label: 'System Configuration', icon: <Settings />, path: '/settings/system' },
        { label: 'Integrations', icon: <Settings />, path: '/settings/integrations' },
        { label: 'Custom Fields', icon: <Settings />, path: '/settings/custom-fields' },
        { label: 'Workflows', icon: <Settings />, path: '/settings/workflows' },
        { label: 'Master Data', icon: <Settings />, path: '/settings/master-data' },
        { label: 'Security Settings', icon: <Settings />, path: '/settings/security' },
        { label: 'Email Settings', icon: <Settings />, path: '/settings/email' },
        { label: 'Backup Settings', icon: <Settings />, path: '/settings/backup' },
        { label: 'System Health', icon: <Settings />, path: '/settings/health' },
      ],
    },
  ];

  const renderMenuItem = (item) => {
    const isOpen = openMenus[item.id];
    const isActive = location.pathname === item.path || 
      (item.children && item.children.some(child => location.pathname === child.path));

    if (item.children) {
      return (
        <Box key={item.id}>
          <ListItemButton
            onClick={() => handleMenuToggle(item.id)}
            sx={{
              backgroundColor: isActive ? 'primary.light' : 'transparent',
              '&:hover': { backgroundColor: 'primary.light' },
            }}
          >
            <ListItemIcon sx={{ color: isActive ? 'primary.main' : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.label} />
            {isOpen ? <ExpandLess /> : <ExpandMore />}
          </ListItemButton>
          <Collapse in={isOpen} timeout="auto" unmountOnExit>
            <List component="div" disablePadding>
              {item.children.map((child) => (
                <ListItemButton
                  key={child.path}
                  onClick={() => navigate(child.path)}
                  sx={{
                    pl: 4,
                    backgroundColor: location.pathname === child.path ? 'primary.light' : 'transparent',
                    '&:hover': { backgroundColor: 'primary.light' },
                  }}
                >
                  <ListItemIcon sx={{ color: location.pathname === child.path ? 'primary.main' : 'inherit' }}>
                    {child.icon}
                  </ListItemIcon>
                  <ListItemText primary={child.label} />
                </ListItemButton>
              ))}
            </List>
          </Collapse>
        </Box>
      );
    }

    return (
      <ListItem key={item.id} disablePadding>
        <ListItemButton
          onClick={() => navigate(item.path)}
          sx={{
            backgroundColor: isActive ? 'primary.light' : 'transparent',
            '&:hover': { backgroundColor: 'primary.light' },
          }}
        >
          <ListItemIcon sx={{ color: isActive ? 'primary.main' : 'inherit' }}>
            {item.icon}
          </ListItemIcon>
          <ListItemText primary={item.label} />
        </ListItemButton>
      </ListItem>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
          CRM System
        </Typography>
      </Box>
      <Divider />
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List>
          {menuItems.map(renderMenuItem)}
        </List>
      </Box>
    </Box>
  );
};

export default Sidebar;
