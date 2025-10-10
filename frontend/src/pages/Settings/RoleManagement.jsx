// frontend/src/pages/Settings/RoleManagement.jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  Grid,
  Card,
  CardContent,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  Divider,
  Alert,
  Tooltip,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  VpnKey,
  Security,
  People,
  Warning,
} from '@mui/icons-material';

const RoleManagement = () => {
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [openPermissionsDialog, setOpenPermissionsDialog] = useState(false);
  const [editingRole, setEditingRole] = useState(null);
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedPermissions, setSelectedPermissions] = useState([]);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });

  // Mock permissions grouped by module
  const mockPermissions = {
    'Contacts': [
      { id: 1, name: 'View Contacts', codename: 'view_contact', module: 'Contacts' },
      { id: 2, name: 'Create Contacts', codename: 'create_contact', module: 'Contacts' },
      { id: 3, name: 'Edit Contacts', codename: 'edit_contact', module: 'Contacts' },
      { id: 4, name: 'Delete Contacts', codename: 'delete_contact', module: 'Contacts' },
    ],
    'Leads': [
      { id: 5, name: 'View Leads', codename: 'view_lead', module: 'Leads' },
      { id: 6, name: 'Create Leads', codename: 'create_lead', module: 'Leads' },
      { id: 7, name: 'Edit Leads', codename: 'edit_lead', module: 'Leads' },
      { id: 8, name: 'Delete Leads', codename: 'delete_lead', module: 'Leads' },
    ],
    'Deals': [
      { id: 9, name: 'View Deals', codename: 'view_deal', module: 'Deals' },
      { id: 10, name: 'Create Deals', codename: 'create_deal', module: 'Deals' },
      { id: 11, name: 'Edit Deals', codename: 'edit_deal', module: 'Deals' },
      { id: 12, name: 'Delete Deals', codename: 'delete_deal', module: 'Deals' },
    ],
    'Reports': [
      { id: 13, name: 'View Reports', codename: 'view_report', module: 'Reports' },
      { id: 14, name: 'Create Reports', codename: 'create_report', module: 'Reports' },
      { id: 15, name: 'Export Data', codename: 'export_data', module: 'Reports' },
    ],
    'Settings': [
      { id: 16, name: 'Manage Users', codename: 'manage_users', module: 'Settings' },
      { id: 17, name: 'Manage Roles', codename: 'manage_roles', module: 'Settings' },
      { id: 18, name: 'System Configuration', codename: 'system_config', module: 'Settings' },
    ],
  };

  useEffect(() => {
    fetchRoles();
    fetchPermissions();
  }, []);

  const fetchRoles = async () => {
    // Mock roles - replace with actual API call
    const mockRoles = [
      {
        id: 1,
        name: 'Administrator',
        description: 'Full system access',
        permissions_count: 18,
        users_count: 3,
        is_system_role: true,
      },
      {
        id: 2,
        name: 'Sales Manager',
        description: 'Manage sales team and deals',
        permissions_count: 12,
        users_count: 5,
        is_system_role: false,
      },
      {
        id: 3,
        name: 'Sales Representative',
        description: 'Handle contacts and deals',
        permissions_count: 8,
        users_count: 15,
        is_system_role: false,
      },
      {
        id: 4,
        name: 'Viewer',
        description: 'Read-only access',
        permissions_count: 4,
        users_count: 8,
        is_system_role: false,
      },
    ];
    setRoles(mockRoles);
  };

  const fetchPermissions = async () => {
    // Flatten mock permissions
    const allPermissions = Object.values(mockPermissions).flat();
    setPermissions(allPermissions);
  };

  const handleOpenDialog = (role = null) => {
    setEditingRole(role);
    if (role) {
      setFormData({
        name: role.name,
        description: role.description,
      });
    } else {
      setFormData({
        name: '',
        description: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingRole(null);
  };

  const handleSaveRole = () => {
    console.log('Saving role:', formData);
    handleCloseDialog();
    fetchRoles();
  };

  const handleDeleteRole = (roleId) => {
    if (window.confirm('Are you sure you want to delete this role?')) {
      console.log('Deleting role:', roleId);
      fetchRoles();
    }
  };

  const handleManagePermissions = (role) => {
    setSelectedRole(role);
    // Mock: Load role's current permissions
    setSelectedPermissions([1, 2, 3, 5, 6, 9, 10]);
    setOpenPermissionsDialog(true);
  };

  const handleTogglePermission = (permissionId) => {
    setSelectedPermissions((prev) =>
      prev.includes(permissionId)
        ? prev.filter((id) => id !== permissionId)
        : [...prev, permissionId]
    );
  };

  const handleSavePermissions = () => {
    console.log('Saving permissions for role:', selectedRole.id, selectedPermissions);
    setOpenPermissionsDialog(false);
    fetchRoles();
  };

  const handleSelectAllModule = (module) => {
    const modulePermissions = mockPermissions[module].map(p => p.id);
    const allSelected = modulePermissions.every(id => selectedPermissions.includes(id));
    
    if (allSelected) {
      setSelectedPermissions(prev => prev.filter(id => !modulePermissions.includes(id)));
    } else {
      setSelectedPermissions(prev => [...new Set([...prev, ...modulePermissions])]);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            Role Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure roles and permissions for your organization
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => handleOpenDialog()}
        >
          Add Role
        </Button>
      </Box>

      {/* Role Statistics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <VpnKey />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Roles
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {roles.length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <Security />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    System Roles
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {roles.filter(r => r.is_system_role).length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <People />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Total Users
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {roles.reduce((sum, role) => sum + role.users_count, 0)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <Security />
                </Avatar>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Permissions
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                    {permissions.length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Roles Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Role Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Permissions</TableCell>
              <TableCell>Users</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {roles.map((role) => (
              <TableRow key={role.id}>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ mr: 2, width: 32, height: 32, bgcolor: 'primary.main' }}>
                      <VpnKey fontSize="small" />
                    </Avatar>
                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                      {role.name}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {role.description}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={`${role.permissions_count} permissions`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={`${role.users_count} users`}
                    size="small"
                    color="info"
                  />
                </TableCell>
                <TableCell>
                  {role.is_system_role ? (
                    <Chip label="System" size="small" color="warning" />
                  ) : (
                    <Chip label="Custom" size="small" color="default" />
                  )}
                </TableCell>
                <TableCell>
                  <Tooltip title="Manage Permissions">
                    <IconButton
                      size="small"
                      onClick={() => handleManagePermissions(role)}
                    >
                      <Security />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Edit Role">
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(role)}
                      disabled={role.is_system_role}
                    >
                      <Edit />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete Role">
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteRole(role.id)}
                      color="error"
                      disabled={role.is_system_role}
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Add/Edit Role Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingRole ? 'Edit Role' : 'Create New Role'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Role Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSaveRole} variant="contained">
            {editingRole ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Manage Permissions Dialog */}
      <Dialog
        open={openPermissionsDialog}
        onClose={() => setOpenPermissionsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Manage Permissions - {selectedRole?.name}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Select the permissions you want to assign to this role
          </Alert>
          {Object.entries(mockPermissions).map(([module, perms]) => (
            <Box key={module} sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="h6" color="primary">
                  {module}
                </Typography>
                <Button size="small" onClick={() => handleSelectAllModule(module)}>
                  Toggle All
                </Button>
              </Box>
              <List>
                {perms.map((permission) => (
                  <ListItem key={permission.id} dense button onClick={() => handleTogglePermission(permission.id)}>
                    <ListItemIcon>
                      <Checkbox
                        edge="start"
                        checked={selectedPermissions.includes(permission.id)}
                        tabIndex={-1}
                        disableRipple
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={permission.name}
                      secondary={permission.codename}
                    />
                  </ListItem>
                ))}
              </List>
              <Divider />
            </Box>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPermissionsDialog(false)}>Cancel</Button>
          <Button onClick={handleSavePermissions} variant="contained">
            Save Permissions
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RoleManagement;
