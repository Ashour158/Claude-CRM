// frontend/src/pages/Settings/AdminPanel.jsx
import React, { useState } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Paper,
  Typography,
} from '@mui/material';
import {
  People,
  VpnKey,
  History,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import UserManagement from './UserManagement';
import RoleManagement from './RoleManagement';

const TabPanel = (props) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
};

const AdminPanel = () => {
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <Box>
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="admin panel tabs"
        >
          <Tab icon={<People />} label="Users" iconPosition="start" />
          <Tab icon={<VpnKey />} label="Roles & Permissions" iconPosition="start" />
          <Tab icon={<History />} label="Activity Logs" iconPosition="start" />
          <Tab icon={<SettingsIcon />} label="System Settings" iconPosition="start" />
        </Tabs>
      </Paper>

      <TabPanel value={currentTab} index={0}>
        <UserManagement />
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <RoleManagement />
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Activity Logs Component
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Coming soon - Comprehensive activity tracking and audit logs
          </Typography>
        </Box>
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            System Settings Component
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Coming soon - Advanced system configuration
          </Typography>
        </Box>
      </TabPanel>
    </Box>
  );
};

export default AdminPanel;
