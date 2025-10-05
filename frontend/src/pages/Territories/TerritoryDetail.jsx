// frontend/src/pages/Territories/TerritoryDetail.jsx
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
  Public,
  Person,
  Business,
  Schedule,
  Assignment,
} from '@mui/icons-material';

const TerritoryDetail = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Mock data
  const territory = {
    id: id,
    name: 'North America',
    description: 'North American sales territory covering US, Canada, and Mexico',
    manager: 'Jane Smith',
    accounts_count: 25,
    contacts_count: 150,
    deals_count: 12,
    status: 'Active',
    created_at: '2024-01-15',
    updated_at: '2024-01-20',
    notes: 'High-performing territory with strong growth potential.',
  };

  const accounts = [
    { id: 1, name: 'Acme Corporation', type: 'Customer', owner: 'Jane Smith' },
    { id: 2, name: 'Tech Solutions Inc', type: 'Prospect', owner: 'Mike Johnson' },
  ];

  const activities = [
    { id: 1, type: 'call', title: 'Territory review meeting', date: '2024-01-20', user: 'Jane Smith' },
    { id: 2, type: 'email', title: 'Monthly report sent', date: '2024-01-19', user: 'Mike Johnson' },
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            {territory.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip label={territory.status} color={getStatusColor(territory.status)} size="small" />
            <Typography variant="body2" color="text.secondary">
              {territory.accounts_count} accounts
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<Edit />} onClick={() => setEditDialogOpen(true)}>
            Edit
          </Button>
          <Button variant="outlined" color="error" startIcon={<Delete />}>
            Delete
          </Button>
        </Box>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2, width: 56, height: 56 }}>
                  <Public />
                </Avatar>
                <Box>
                  <Typography variant="h6">{territory.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {territory.manager}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Person />
                  </ListItemIcon>
                  <ListItemText primary="Manager" secondary={territory.manager} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Business />
                  </ListItemIcon>
                  <ListItemText primary="Accounts" secondary={territory.accounts_count} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Person />
                  </ListItemIcon>
                  <ListItemText primary="Contacts" secondary={territory.contacts_count} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Assignment />
                  </ListItemIcon>
                  <ListItemText primary="Deals" secondary={territory.deals_count} />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Overview" />
                <Tab label="Accounts" />
                <Tab label="Activities" />
                <Tab label="Notes" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <Typography variant="h6" gutterBottom>
                Territory Description
              </Typography>
              <Typography variant="body1" paragraph>
                {territory.description}
              </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Accounts ({accounts.length})</Typography>
                <Button variant="outlined" size="small">Add Account</Button>
              </Box>
              <List>
                {accounts.map((account) => (
                  <ListItem key={account.id} divider>
                    <ListItemIcon>
                      <Business />
                    </ListItemIcon>
                    <ListItemText
                      primary={account.name}
                      secondary={`${account.type} • ${account.owner}`}
                    />
                  </ListItem>
                ))}
              </List>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Recent Activities</Typography>
                <Button variant="outlined" size="small">Add Activity</Button>
              </Box>
              <List>
                {activities.map((activity) => (
                  <ListItem key={activity.id} divider>
                    <ListItemIcon>
                      {activity.type === 'call' && <Assignment />}
                      {activity.type === 'email' && <Assignment />}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.title}
                      secondary={`${activity.user} • ${new Date(activity.date).toLocaleDateString()}`}
                    />
                  </ListItem>
                ))}
              </List>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {territory.notes}
              </Typography>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Territory</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField fullWidth label="Territory Name" defaultValue={territory.name} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Description" defaultValue={territory.description} multiline rows={3} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Manager" defaultValue={territory.manager} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Status" defaultValue={territory.status} />
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

export default TerritoryDetail;
