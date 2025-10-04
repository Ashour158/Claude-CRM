// frontend/src/pages/Settings/SystemConfiguration.jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Save,
  Refresh,
  Settings,
  Security,
  Notifications,
  Language,
  Schedule,
} from '@mui/icons-material';

const SystemConfiguration = () => {
  const [config, setConfig] = useState({
    // General Settings
    company_name: '',
    company_logo: '',
    timezone: 'UTC',
    currency: 'USD',
    date_format: 'MM/DD/YYYY',
    time_format: '12h',
    language: 'en',
    
    // Security Settings
    password_min_length: 8,
    password_require_special: true,
    password_require_numbers: true,
    session_timeout: 30,
    two_factor_auth: false,
    ip_whitelist: '',
    
    // Notification Settings
    email_notifications: true,
    sms_notifications: false,
    push_notifications: true,
    notification_frequency: 'immediate',
    
    // System Settings
    maintenance_mode: false,
    debug_mode: false,
    log_level: 'info',
    backup_frequency: 'daily',
    data_retention_days: 365,
  });

  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    fetchConfiguration();
  }, []);

  const fetchConfiguration = async () => {
    // Mock configuration data
    setConfig({
      company_name: 'CRM System',
      company_logo: '',
      timezone: 'UTC',
      currency: 'USD',
      date_format: 'MM/DD/YYYY',
      time_format: '12h',
      language: 'en',
      password_min_length: 8,
      password_require_special: true,
      password_require_numbers: true,
      session_timeout: 30,
      two_factor_auth: false,
      ip_whitelist: '',
      email_notifications: true,
      sms_notifications: false,
      push_notifications: true,
      notification_frequency: 'immediate',
      maintenance_mode: false,
      debug_mode: false,
      log_level: 'info',
      backup_frequency: 'daily',
      data_retention_days: 365,
    });
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // Save configuration logic here
      console.log('Saving configuration:', config);
      setSnackbar({
        open: true,
        message: 'Configuration saved successfully',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error saving configuration',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    fetchConfiguration();
    setSnackbar({
      open: true,
      message: 'Configuration reset to defaults',
      severity: 'info',
    });
  };

  const handleChange = (field, value) => {
    setConfig(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            System Configuration
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure global system settings and preferences
          </Typography>
        </Box>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleReset}
            sx={{ mr: 2 }}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={loading}
          >
            Save Changes
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Settings />}
              title="General Settings"
              subheader="Basic system configuration"
            />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Company Name"
                    value={config.company_name}
                    onChange={(e) => handleChange('company_name', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Company Logo URL"
                    value={config.company_logo}
                    onChange={(e) => handleChange('company_logo', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Timezone</InputLabel>
                    <Select
                      value={config.timezone}
                      onChange={(e) => handleChange('timezone', e.target.value)}
                    >
                      <MenuItem value="UTC">UTC</MenuItem>
                      <MenuItem value="America/New_York">Eastern Time</MenuItem>
                      <MenuItem value="America/Chicago">Central Time</MenuItem>
                      <MenuItem value="America/Denver">Mountain Time</MenuItem>
                      <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Currency</InputLabel>
                    <Select
                      value={config.currency}
                      onChange={(e) => handleChange('currency', e.target.value)}
                    >
                      <MenuItem value="USD">USD - US Dollar</MenuItem>
                      <MenuItem value="EUR">EUR - Euro</MenuItem>
                      <MenuItem value="GBP">GBP - British Pound</MenuItem>
                      <MenuItem value="CAD">CAD - Canadian Dollar</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Date Format</InputLabel>
                    <Select
                      value={config.date_format}
                      onChange={(e) => handleChange('date_format', e.target.value)}
                    >
                      <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                      <MenuItem value="DD/MM/YYYY">DD/MM/YYYY</MenuItem>
                      <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Time Format</InputLabel>
                    <Select
                      value={config.time_format}
                      onChange={(e) => handleChange('time_format', e.target.value)}
                    >
                      <MenuItem value="12h">12 Hour (AM/PM)</MenuItem>
                      <MenuItem value="24h">24 Hour</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Language</InputLabel>
                    <Select
                      value={config.language}
                      onChange={(e) => handleChange('language', e.target.value)}
                    >
                      <MenuItem value="en">English</MenuItem>
                      <MenuItem value="es">Spanish</MenuItem>
                      <MenuItem value="fr">French</MenuItem>
                      <MenuItem value="de">German</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Security Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Security />}
              title="Security Settings"
              subheader="Authentication and security configuration"
            />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Password Minimum Length"
                    type="number"
                    value={config.password_min_length}
                    onChange={(e) => handleChange('password_min_length', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Session Timeout (minutes)"
                    type="number"
                    value={config.session_timeout}
                    onChange={(e) => handleChange('session_timeout', parseInt(e.target.value))}
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.password_require_special}
                        onChange={(e) => handleChange('password_require_special', e.target.checked)}
                      />
                    }
                    label="Require special characters in passwords"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.password_require_numbers}
                        onChange={(e) => handleChange('password_require_numbers', e.target.checked)}
                      />
                    }
                    label="Require numbers in passwords"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.two_factor_auth}
                        onChange={(e) => handleChange('two_factor_auth', e.target.checked)}
                      />
                    }
                    label="Enable two-factor authentication"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="IP Whitelist (comma-separated)"
                    value={config.ip_whitelist}
                    onChange={(e) => handleChange('ip_whitelist', e.target.value)}
                    helperText="Leave empty to allow all IPs"
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Notifications />}
              title="Notification Settings"
              subheader="Configure notification preferences"
            />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.email_notifications}
                        onChange={(e) => handleChange('email_notifications', e.target.checked)}
                      />
                    }
                    label="Enable email notifications"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.sms_notifications}
                        onChange={(e) => handleChange('sms_notifications', e.target.checked)}
                      />
                    }
                    label="Enable SMS notifications"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.push_notifications}
                        onChange={(e) => handleChange('push_notifications', e.target.checked)}
                      />
                    }
                    label="Enable push notifications"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Notification Frequency</InputLabel>
                    <Select
                      value={config.notification_frequency}
                      onChange={(e) => handleChange('notification_frequency', e.target.value)}
                    >
                      <MenuItem value="immediate">Immediate</MenuItem>
                      <MenuItem value="hourly">Hourly</MenuItem>
                      <MenuItem value="daily">Daily</MenuItem>
                      <MenuItem value="weekly">Weekly</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* System Settings */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              avatar={<Settings />}
              title="System Settings"
              subheader="Advanced system configuration"
            />
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.maintenance_mode}
                        onChange={(e) => handleChange('maintenance_mode', e.target.checked)}
                      />
                    }
                    label="Maintenance Mode"
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.debug_mode}
                        onChange={(e) => handleChange('debug_mode', e.target.checked)}
                      />
                    }
                    label="Debug Mode"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Log Level</InputLabel>
                    <Select
                      value={config.log_level}
                      onChange={(e) => handleChange('log_level', e.target.value)}
                    >
                      <MenuItem value="debug">Debug</MenuItem>
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="warning">Warning</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Backup Frequency</InputLabel>
                    <Select
                      value={config.backup_frequency}
                      onChange={(e) => handleChange('backup_frequency', e.target.value)}
                    >
                      <MenuItem value="hourly">Hourly</MenuItem>
                      <MenuItem value="daily">Daily</MenuItem>
                      <MenuItem value="weekly">Weekly</MenuItem>
                      <MenuItem value="monthly">Monthly</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Data Retention (days)"
                    type="number"
                    value={config.data_retention_days}
                    onChange={(e) => handleChange('data_retention_days', parseInt(e.target.value))}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SystemConfiguration;
