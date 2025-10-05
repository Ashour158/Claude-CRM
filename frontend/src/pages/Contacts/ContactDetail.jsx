// frontend/src/pages/Contacts/ContactDetail.jsx
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
  Person,
  Phone,
  Email,
  Business,
  LocationOn,
  Assignment,
  Schedule,
  TrendingUp,
} from '@mui/icons-material';

const ContactDetail = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Mock data
  const contact = {
    id: id,
    first_name: 'John',
    last_name: 'Doe',
    title: 'CEO',
    email: 'john@acme.com',
    phone: '+1-555-0123',
    mobile: '+1-555-0124',
    account: 'Acme Corporation',
    address: '123 Main St, New York, NY 10001',
    owner: 'Jane Smith',
    status: 'Active',
    created_at: '2024-01-15',
    updated_at: '2024-01-20',
    notes: 'Primary decision maker for enterprise software purchases.',
  };

  const activities = [
    { id: 1, type: 'call', title: 'Follow-up call', date: '2024-01-20', user: 'Jane Smith' },
    { id: 2, type: 'email', title: 'Proposal sent', date: '2024-01-19', user: 'Mike Johnson' },
    { id: 3, type: 'meeting', title: 'Product demo', date: '2024-01-18', user: 'John Doe' },
  ];

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
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
            {contact.first_name} {contact.last_name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              {contact.title}
            </Typography>
            <Chip label={contact.status} color="success" size="small" />
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
                  {contact.first_name.charAt(0)}
                </Avatar>
                <Box>
                  <Typography variant="h6">{contact.first_name} {contact.last_name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {contact.title}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Email />
                  </ListItemIcon>
                  <ListItemText primary="Email" secondary={contact.email} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Phone />
                  </ListItemIcon>
                  <ListItemText primary="Phone" secondary={contact.phone} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Phone />
                  </ListItemIcon>
                  <ListItemText primary="Mobile" secondary={contact.mobile} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Business />
                  </ListItemIcon>
                  <ListItemText primary="Account" secondary={contact.account} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <LocationOn />
                  </ListItemIcon>
                  <ListItemText primary="Address" secondary={contact.address} />
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
                <Tab label="Activities" />
                <Tab label="Notes" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <Typography variant="h6" gutterBottom>
                Contact Information
              </Typography>
              <Typography variant="body1" paragraph>
                {contact.notes}
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
                No notes available. Add a note to track important information about this contact.
              </Typography>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Contact</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="First Name" defaultValue={contact.first_name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Last Name" defaultValue={contact.last_name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Title" defaultValue={contact.title} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Email" defaultValue={contact.email} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Phone" defaultValue={contact.phone} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Mobile" defaultValue={contact.mobile} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Address" defaultValue={contact.address} multiline rows={2} />
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

export default ContactDetail;
