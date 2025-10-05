// frontend/src/pages/Dashboard/Dashboard.jsx
import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Avatar,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  People,
  Business,
  Assignment,
  AttachMoney,
  Schedule,
  CheckCircle,
  Warning,
} from '@mui/icons-material';

const Dashboard = () => {
  // Mock data - in real app, this would come from API
  const stats = {
    totalAccounts: 156,
    totalContacts: 892,
    totalLeads: 234,
    totalDeals: 89,
    totalRevenue: 1250000,
    activeTasks: 23,
    completedTasks: 45,
    overdueTasks: 3,
  };

  const recentActivities = [
    { id: 1, type: 'call', title: 'Follow-up call with Acme Corp', time: '2 hours ago', user: 'John Doe' },
    { id: 2, type: 'email', title: 'Proposal sent to Tech Solutions', time: '4 hours ago', user: 'Jane Smith' },
    { id: 3, type: 'meeting', title: 'Product demo scheduled', time: '6 hours ago', user: 'Mike Johnson' },
    { id: 4, type: 'task', title: 'Update customer records', time: '8 hours ago', user: 'Sarah Wilson' },
  ];

  const topDeals = [
    { id: 1, name: 'Enterprise Software License', amount: 50000, stage: 'Proposal', probability: 75 },
    { id: 2, name: 'CRM Implementation', amount: 35000, stage: 'Negotiation', probability: 60 },
    { id: 3, name: 'Support Contract', amount: 25000, stage: 'Qualification', probability: 40 },
    { id: 4, name: 'Training Services', amount: 15000, stage: 'Prospecting', probability: 25 },
  ];

  const StatCard = ({ title, value, icon, color = 'primary', trend = null }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUp sx={{ fontSize: 16, color: 'success.main', mr: 0.5 }} />
                <Typography variant="body2" color="success.main">
                  +{trend}% from last month
                </Typography>
              </Box>
            )}
          </Box>
          <Avatar sx={{ bgcolor: `${color}.main`, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Welcome back! Here's what's happening with your business.
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Accounts"
            value={stats.totalAccounts}
            icon={<Business />}
            color="primary"
            trend={12}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Contacts"
            value={stats.totalContacts}
            icon={<People />}
            color="secondary"
            trend={8}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Leads"
            value={stats.totalLeads}
            icon={<Assignment />}
            color="success"
            trend={15}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Revenue"
            value={`$${stats.totalRevenue.toLocaleString()}`}
            icon={<AttachMoney />}
            color="warning"
            trend={22}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Recent Activities */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activities
              </Typography>
              <List>
                {recentActivities.map((activity) => (
                  <ListItem key={activity.id} divider>
                    <ListItemIcon>
                      {activity.type === 'call' && <Assignment color="primary" />}
                      {activity.type === 'email' && <Assignment color="secondary" />}
                      {activity.type === 'meeting' && <Schedule color="success" />}
                      {activity.type === 'task' && <CheckCircle color="warning" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.title}
                      secondary={`${activity.user} • ${activity.time}`}
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Deals */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Deals
              </Typography>
              <List>
                {topDeals.map((deal) => (
                  <ListItem key={deal.id} divider>
                    <ListItemText
                      primary={deal.name}
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary">
                            ${deal.amount.toLocaleString()}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                            <Chip
                              label={deal.stage}
                              size="small"
                              color="primary"
                              variant="outlined"
                              sx={{ mr: 1 }}
                            />
                            <Box sx={{ width: '100%', mr: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={deal.probability}
                                sx={{ height: 6, borderRadius: 3 }}
                              />
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              {deal.probability}%
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Task Summary */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Task Summary
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {stats.activeTasks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Tasks
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {stats.completedTasks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="error">
                    {stats.overdueTasks}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Overdue
                  </Typography>
                </Box>
              </Box>
              <LinearProgress
                variant="determinate"
                value={(stats.completedTasks / (stats.activeTasks + stats.completedTasks)) * 100}
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Business sx={{ mr: 2, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="body1">Add New Account</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Create a new customer account
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <Assignment sx={{ mr: 2, color: 'secondary.main' }} />
                  <Box>
                    <Typography variant="body1">Create Lead</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Add a new sales lead
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
                  <TrendingUp sx={{ mr: 2, color: 'success.main' }} />
                  <Box>
                    <Typography variant="body1">New Deal</Typography>
                    <Typography variant="body2" color="text.secondary">
                      Start a new sales opportunity
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
