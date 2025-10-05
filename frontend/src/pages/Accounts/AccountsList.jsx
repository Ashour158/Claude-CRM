// frontend/src/pages/Accounts/AccountsList.jsx
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Fab,
  InputAdornment,
} from '@mui/material';
import {
  Add,
  Search,
  MoreVert,
  Edit,
  Delete,
  Visibility,
  Business,
  Phone,
  Email,
  LocationOn,
} from '@mui/icons-material';

const AccountsList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Mock data - in real app, this would come from API
  const accounts = [
    {
      id: 1,
      name: 'Acme Corporation',
      type: 'Customer',
      industry: 'Technology',
      email: 'info@acme.com',
      phone: '+1-555-0123',
      address: '123 Main St, New York, NY',
      owner: 'John Doe',
      status: 'Active',
      created_at: '2024-01-15',
    },
    {
      id: 2,
      name: 'Tech Solutions Inc',
      type: 'Prospect',
      industry: 'Software',
      email: 'contact@techsolutions.com',
      phone: '+1-555-0124',
      address: '456 Tech Ave, San Francisco, CA',
      owner: 'Jane Smith',
      status: 'Active',
      created_at: '2024-01-10',
    },
    {
      id: 3,
      name: 'Global Enterprises',
      type: 'Partner',
      industry: 'Manufacturing',
      email: 'partnerships@global.com',
      phone: '+1-555-0125',
      address: '789 Industrial Blvd, Chicago, IL',
      owner: 'Mike Johnson',
      status: 'Inactive',
      created_at: '2024-01-05',
    },
  ];

  const handleMenuOpen = (event, account) => {
    setAnchorEl(event.currentTarget);
    setSelectedAccount(account);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedAccount(null);
  };

  const handleDelete = () => {
    // Handle delete logic
    console.log('Delete account:', selectedAccount);
    setDeleteDialogOpen(false);
    handleMenuClose();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Active':
        return 'success';
      case 'Inactive':
        return 'default';
      default:
        return 'default';
    }
  };

  const getTypeColor = (type) => {
    switch (type) {
      case 'Customer':
        return 'primary';
      case 'Prospect':
        return 'warning';
      case 'Partner':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const filteredAccounts = accounts.filter(account =>
    account.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    account.industry.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Accounts
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your customer accounts and prospects
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          size="large"
        >
          Add Account
        </Button>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search accounts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button variant="outlined" size="small">
                  Filter
                </Button>
                <Button variant="outlined" size="small">
                  Export
                </Button>
                <Button variant="outlined" size="small">
                  Import
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Accounts Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Account Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Industry</TableCell>
                <TableCell>Contact Info</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredAccounts.map((account) => (
                <TableRow key={account.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Business sx={{ mr: 1, color: 'primary.main' }} />
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {account.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {account.address}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={account.type}
                      color={getTypeColor(account.type)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {account.industry}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                        <Email sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {account.email}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Phone sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                        <Typography variant="body2">
                          {account.phone}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {account.owner}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={account.status}
                      color={getStatusColor(account.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(account.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      onClick={(e) => handleMenuOpen(e, account)}
                      size="small"
                    >
                      <MoreVert />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <Visibility sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Edit sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={() => setDeleteDialogOpen(true)}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Account</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "{selectedAccount?.name}"? This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
      >
        <Add />
      </Fab>
    </Box>
  );
};

export default AccountsList;
