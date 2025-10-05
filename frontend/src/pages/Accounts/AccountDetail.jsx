// frontend/src/pages/Accounts/AccountDetail.jsx
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  Avatar,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import {
  Edit,
  Delete,
  Business,
  Phone,
  Email,
  LocationOn,
  Person,
  TrendingUp,
  Assignment,
  Schedule,
  AttachMoney,
} from '@mui/icons-material';

const AccountDetail = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Mock data - in real app, this would come from API
  const account = {
    id: id,
    name: 'Acme Corporation',
    type: 'Customer',
    industry: 'Technology',
    email: 'info@acme.com',
    phone: '+1-555-0123',
    website: 'https://acme.com',
    address: '123 Main St, New York, NY 10001',
    annual_revenue: 1000000,
    employee_count: 50,
    owner: 'John Doe',
    status: 'Active',
    created_at: '2024-01-15',
    updated_at: '2024-01-20',
    description: 'Leading technology company specializing in enterprise software solutions.',
  };

  const contacts = [
    { id: 1, name: 'Jane Smith', title: 'CEO', email: 'jane@acme.com', phone: '+1-555-0124' },
    { id: 2, name: 'Bob Johnson', title: 'CTO', email: 'bob@acme.com', phone: '+1-555-0125' },
  ];

  const deals = [
    { id: 1, name: 'Enterprise License', amount: 50000, stage: 'Proposal', probability: 75 },
    { id: 2, name: 'Support Contract', amount: 25000, stage: 'Negotiation', probability: 60 },
  ];

  const activities = [
    { id: 1, type: 'call', title: 'Follow-up call', date: '2024-01-20', user: 'John Doe' },
    { id: 2, type: 'email', title: 'Proposal sent', date: '2024-01-19', user: 'Jane Smith' },
    { id: 3, type: 'meeting', title: 'Product demo', date: '2024-01-18', user: 'Mike Johnson' },
  ];

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
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

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            {account.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={account.type}
              color={getTypeColor(account.type)}
              size="small"
            />
            <Chip
              label={account.status}
              color={getStatusColor(account.status)}
              size="small"
            />
            <Typography variant="body2" color="text.secondary">
              {account.industry}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Edit />}
            onClick={() => setEditDialogOpen(true)}
          >
            Edit
          </Button>
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
          >
            Delete
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Account Info */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2, width: 56, height: 56 }}>
                  <Business />
                </Avatar>
                <Box>
                  <Typography variant="h6">{account.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {account.industry}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText
                    primary="Email"
                    secondary={account.email}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Phone />
                  </ListItemIcon>
                  <ListItemText
                    primary="Phone"
                    secondary={account.phone}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LocationOn />
                  </ListItemIcon>
                  <ListItemText
                    primary="Address"
                    secondary={account.address}
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Person />
                  </ListItemIcon>
                  <ListItemText
                    primary="Owner"
                    secondary={account.owner}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Annual Revenue"
                    secondary={`$${account.annual_revenue.toLocaleString()}`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Employees"
                    secondary={account.employee_count}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Active Deals"
                    secondary={deals.length}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Total Contacts"
                    secondary={contacts.length}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Main Content */}
        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Overview" />
                <Tab label="Contacts" />
                <Tab label="Deals" />
                <Tab label="Activities" />
                <Tab label="Notes" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <Typography variant="h6" gutterBottom>
                Company Description
              </Typography>
              <Typography variant="body1" paragraph>
                {account.description}
              </Typography>
              
              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Company Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Website
                  </Typography>
                  <Typography variant="body1">
                    {account.website}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Created
                  </Typography>
                  <Typography variant="body1">
                    {new Date(account.created_at).toLocaleDateString()}
                  </Typography>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Contacts ({contacts.length})
                </Typography>
                <Button variant="outlined" size="small">
                  Add Contact
                </Button>
              </Box>
              <List>
                {contacts.map((contact) => (
                  <ListItem key={contact.id} divider>
                  <ListItemIcon>
                    <Person />
                  </ListItemIcon>
                  <ListItemText
                    primary={contact.name}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {contact.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {contact.email} • {contact.phone}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                ))}
              </List>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Deals ({deals.length})
                </Typography>
                <Button variant="outlined" size="small">
                  Add Deal
                </Button>
              </Box>
              <List>
                {deals.map((deal) => (
                  <ListItem key={deal.id} divider>
                  <ListItemIcon>
                    <TrendingUp />
                  </ListItemIcon>
                  <ListItemText
                    primary={deal.name}
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          ${deal.amount.toLocaleString()} • {deal.stage} • {deal.probability}%
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                ))}
              </List>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Recent Activities
                </Typography>
                <Button variant="outlined" size="small">
                  Add Activity
                </Button>
              </Box>
              <List>
                {activities.map((activity) => (
                  <ListItem key={activity.id} divider>
                  <ListItemIcon>
                    {activity.type === 'call' && <Phone />}
                    {activity.type === 'email' && <Email />}
                    {activity.type === 'meeting' && <Schedule />}
                  </ListItemIcon>
                  <ListItemText
                    primary={activity.title}
                    secondary={`${activity.user} • ${new Date(activity.date).toLocaleDateString()}`}
                  />
                </ListItem>
                ))}
              </List>
            </TabPanel>

            <TabPanel value={activeTab} index={4}>
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Typography variant="body1" color="text.secondary">
                No notes available. Add a note to track important information about this account.
              </Typography>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Account</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Account Name"
                defaultValue={account.name}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Industry"
                defaultValue={account.industry}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Email"
                defaultValue={account.email}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                defaultValue={account.phone}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Address"
                defaultValue={account.address}
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccountDetail;
