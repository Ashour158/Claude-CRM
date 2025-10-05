// frontend/src/pages/Leads/LeadDetail.jsx
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
  LinearProgress,
} from '@mui/material';
import {
  Edit,
  Delete,
  Person,
  Phone,
  Email,
  Business,
  LocationOn,
  Assignment,
  Schedule,
  TrendingUp,
  Convert,
} from '@mui/icons-material';

const LeadDetail = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [convertDialogOpen, setConvertDialogOpen] = useState(false);

  // Mock data
  const lead = {
    id: id,
    first_name: 'John',
    last_name: 'Doe',
    company_name: 'Acme Corporation',
    title: 'CEO',
    email: 'john@acme.com',
    phone: '+1-555-0123',
    mobile: '+1-555-0124',
    source: 'Website',
    status: 'New',
    rating: 'Hot',
    lead_score: 85,
    industry: 'Technology',
    address: '123 Main St, New York, NY 10001',
    owner: 'Jane Smith',
    created_at: '2024-01-15',
    updated_at: '2024-01-20',
    notes: 'Interested in enterprise CRM solution. Budget approved for Q2.',
  };

  const activities = [
    { id: 1, type: 'call', title: 'Initial contact call', date: '2024-01-20', user: 'Jane Smith' },
    { id: 2, type: 'email', title: 'Product information sent', date: '2024-01-19', user: 'Mike Johnson' },
    { id: 3, type: 'meeting', title: 'Discovery meeting', date: '2024-01-18', user: 'John Doe' },
  ];

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'New':
        return 'primary';
      case 'Qualified':
        return 'success';
      case 'Converted':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getRatingColor = (rating) => {
    switch (rating) {
      case 'Hot':
        return 'error';
      case 'Warm':
        return 'warning';
      case 'Cold':
        return 'info';
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
            {lead.first_name} {lead.last_name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip label={lead.status} color={getStatusColor(lead.status)} size="small" />
            <Chip label={lead.rating} color={getRatingColor(lead.rating)} size="small" />
            <Typography variant="body2" color="text.secondary">
              Score: {lead.lead_score}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<Convert />}
            onClick={() => setConvertDialogOpen(true)}
          >
            Convert
          </Button>
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
                  {lead.first_name.charAt(0)}
                </Avatar>
                <Box>
                  <Typography variant="h6">{lead.first_name} {lead.last_name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {lead.title}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Business />
                  </ListItemIcon>
                  <ListItemText primary="Company" secondary={lead.company_name} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText primary="Email" secondary={lead.email} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Phone />
                  </ListItemIcon>
                  <ListItemText primary="Phone" secondary={lead.phone} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Phone />
                  </ListItemIcon>
                  <ListItemText primary="Mobile" secondary={lead.mobile} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LocationOn />
                  </ListItemIcon>
                  <ListItemText primary="Address" secondary={lead.address} />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Lead Information
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Source"
                    secondary={lead.source}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Industry"
                    secondary={lead.industry}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Owner"
                    secondary={lead.owner}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Created"
                    secondary={new Date(lead.created_at).toLocaleDateString()}
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Lead Score
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h4" color="primary">
                  {lead.lead_score}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  / 100
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={lead.lead_score}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={8}>
          <Card>
            <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
              <Tabs value={activeTab} onChange={handleTabChange}>
                <Tab label="Overview" />
                <Tab label="Activities" />
                <Tab label="Notes" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <Typography variant="h6" gutterBottom>
                Lead Description
              </Typography>
              <Typography variant="body1" paragraph>
                {lead.notes}
              </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">Recent Activities</Typography>
                <Button variant="outlined" size="small">Add Activity</Button>
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

            <TabPanel value={activeTab} index={2}>
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Typography variant="body1" color="text.secondary">
                No notes available. Add a note to track important information about this lead.
              </Typography>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Lead</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="First Name" defaultValue={lead.first_name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Last Name" defaultValue={lead.last_name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Company" defaultValue={lead.company_name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Title" defaultValue={lead.title} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Email" defaultValue={lead.email} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Phone" defaultValue={lead.phone} />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Save Changes</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={convertDialogOpen} onClose={() => setConvertDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Convert Lead</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Convert this lead to an account and contact. You can also create a deal if needed.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField fullWidth label="Account Name" defaultValue={lead.company_name} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Contact Name" defaultValue={`${lead.first_name} ${lead.last_name}`} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Deal Name" placeholder="Optional" />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Deal Amount" type="number" placeholder="Optional" />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConvertDialogOpen(false)}>Cancel</Button>
          <Button variant="contained">Convert Lead</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LeadDetail;
