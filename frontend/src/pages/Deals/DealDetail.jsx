// frontend/src/pages/Deals/DealDetail.jsx
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
  TrendingUp,
  Business,
  Person,
  AttachMoney,
  Schedule,
  Assignment,
  Phone,
  Email,
} from '@mui/icons-material';

const DealDetail = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Mock data
  const deal = {
    id: id,
    name: 'Enterprise Software License',
    account: 'Acme Corporation',
    contact: 'John Doe',
    amount: 50000,
    stage: 'Proposal',
    probability: 75,
    close_date: '2024-03-01',
    owner: 'Jane Smith',
    status: 'Open',
    created_at: '2024-01-15',
    updated_at: '2024-01-20',
    description: 'Enterprise software license for 100 users with support and training.',
  };

  const activities = [
    { id: 1, type: 'call', title: 'Discovery call', date: '2024-01-20', user: 'Jane Smith' },
    { id: 2, type: 'email', title: 'Proposal sent', date: '2024-01-19', user: 'Mike Johnson' },
    { id: 3, type: 'meeting', title: 'Product demo', date: '2024-01-18', user: 'John Doe' },
  ];

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getStageColor = (stage) => {
    switch (stage) {
      case 'Prospecting':
        return 'default';
      case 'Qualification':
        return 'info';
      case 'Proposal':
        return 'warning';
      case 'Negotiation':
        return 'primary';
      case 'Closed Won':
        return 'success';
      case 'Closed Lost':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Open':
        return 'success';
      case 'Closed':
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
            {deal.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip label={deal.stage} color={getStageColor(deal.stage)} size="small" />
            <Chip label={deal.status} color={getStatusColor(deal.status)} size="small" />
            <Typography variant="body2" color="text.secondary">
              ${deal.amount.toLocaleString()}
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
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography variant="h6">{deal.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {deal.account}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Business />
                  </ListItemIcon>
                  <ListItemText primary="Account" secondary={deal.account} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Person />
                  </ListItemIcon>
                  <ListItemText primary="Contact" secondary={deal.contact} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AttachMoney />
                  </ListItemIcon>
                  <ListItemText primary="Amount" secondary={`$${deal.amount.toLocaleString()}`} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Schedule />
                  </ListItemIcon>
                  <ListItemText primary="Close Date" secondary={new Date(deal.close_date).toLocaleDateString()} />
                </ListItem>
              </List>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Deal Progress
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="h4" color="primary">
                  {deal.probability}%
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                  probability
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={deal.probability}
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
                <Tab label="Products" />
                <Tab label="Notes" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <Typography variant="h6" gutterBottom>
                Deal Description
              </Typography>
              <Typography variant="body1" paragraph>
                {deal.description}
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
                Products
              </Typography>
              <Typography variant="body1" color="text.secondary">
                No products added to this deal yet.
              </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Typography variant="body1" color="text.secondary">
                No notes available. Add a note to track important information about this deal.
              </Typography>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Deal</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField fullWidth label="Deal Name" defaultValue={deal.name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Account" defaultValue={deal.account} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Contact" defaultValue={deal.contact} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Amount" type="number" defaultValue={deal.amount} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Close Date" type="date" defaultValue={deal.close_date} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Stage" defaultValue={deal.stage} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Probability" type="number" defaultValue={deal.probability} />
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

export default DealDetail;
