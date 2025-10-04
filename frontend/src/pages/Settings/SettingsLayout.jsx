// frontend/src/pages/Settings/SettingsLayout.jsx
import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Paper,
} from '@mui/material';
import {
  Person,
  Business,
  Settings,
  Integration,
  Tune,
  AccountTree,
  Storage,
  Security,
  Email,
  Backup,
  Health,
} from '@mui/icons-material';

const SettingsLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const settingsItems = [
    {
      id: 'users',
      label: 'User Management',
      icon: <Person />,
      path: '/settings/users',
      description: 'Manage user accounts and permissions',
    },
    {
      id: 'company',
      label: 'Company Settings',
      icon: <Business />,
      path: '/settings/company',
      description: 'Company profile and preferences',
    },
    {
      id: 'system',
      label: 'System Configuration',
      icon: <Settings />,
      path: '/settings/system',
      description: 'Global system settings and preferences',
    },
    {
      id: 'integrations',
      label: 'Integrations',
      icon: <Integration />,
      path: '/settings/integrations',
      description: 'Third-party service integrations',
    },
    {
      id: 'custom-fields',
      label: 'Custom Fields',
      icon: <Tune />,
      path: '/settings/custom-fields',
      description: 'Manage custom fields and data structure',
    },
    {
      id: 'workflows',
      label: 'Workflows',
      icon: <AccountTree />,
      path: '/settings/workflows',
      description: 'Business process automation',
    },
    {
      id: 'master-data',
      label: 'Master Data',
      icon: <Storage />,
      path: '/settings/master-data',
      description: 'Master data management',
    },
    {
      id: 'security',
      label: 'Security Settings',
      icon: <Security />,
      path: '/settings/security',
      description: 'Security and access control',
    },
    {
      id: 'email',
      label: 'Email Settings',
      icon: <Email />,
      path: '/settings/email',
      description: 'Email configuration and templates',
    },
    {
      id: 'backup',
      label: 'Backup Settings',
      icon: <Backup />,
      path: '/settings/backup',
      description: 'Data backup and recovery',
    },
    {
      id: 'health',
      label: 'System Health',
      icon: <Health />,
      path: '/settings/health',
      description: 'System monitoring and diagnostics',
    },
  ];

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      {/* Settings Sidebar */}
      <Box sx={{ width: 300, bgcolor: 'background.paper', borderRight: 1, borderColor: 'divider' }}>
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure your CRM system
          </Typography>
        </Box>
        <Divider />
        <List>
          {settingsItems.map((item) => (
            <ListItem key={item.id} disablePadding>
              <ListItemButton
                onClick={() => navigate(item.path)}
                selected={location.pathname === item.path}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    '&:hover': {
                      backgroundColor: 'primary.light',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ color: location.pathname === item.path ? 'primary.main' : 'inherit' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  secondary={item.description}
                  secondaryTypographyProps={{
                    sx: { fontSize: '0.75rem' }
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Settings Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Paper sx={{ height: '100%', p: 3 }}>
          {children}
        </Paper>
      </Box>
    </Box>
  );
};

export default SettingsLayout;
