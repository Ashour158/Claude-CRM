// frontend/src/pages/Deals/DealsList.jsx
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
  Chip,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  InputAdornment,
  LinearProgress,
} from '@mui/material';
import {
  Add,
  Search,
  MoreVert,
  Edit,
  Delete,
  Visibility,
  TrendingUp,
  Business,
  Person,
  AttachMoney,
} from '@mui/icons-material';

const DealsList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedDeal, setSelectedDeal] = useState(null);

  // Mock data
  const deals = [
    {
      id: 1,
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
    },
    {
      id: 2,
      name: 'CRM Implementation',
      account: 'Tech Solutions Inc',
      contact: 'Jane Smith',
      amount: 35000,
      stage: 'Negotiation',
      probability: 60,
      close_date: '2024-02-15',
      owner: 'Mike Johnson',
      status: 'Open',
      created_at: '2024-01-10',
    },
  ];

  const handleMenuOpen = (event, deal) => {
    setAnchorEl(event.currentTarget);
    setSelectedDeal(deal);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedDeal(null);
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

  const filteredDeals = deals.filter(deal =>
    deal.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    deal.account.toLowerCase().includes(searchTerm.toLowerCase()) ||
    deal.contact.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Deals
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your sales opportunities
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} size="large">
          Add Deal
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search deals..."
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
                <Button variant="outlined" size="small">Filter</Button>
                <Button variant="outlined" size="small">Export</Button>
                <Button variant="outlined" size="small">Import</Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Deal</TableCell>
                <TableCell>Account</TableCell>
                <TableCell>Contact</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Stage</TableCell>
                <TableCell>Probability</TableCell>
                <TableCell>Close Date</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredDeals.map((deal) => (
                <TableRow key={deal.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                        <TrendingUp />
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {deal.name}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Business sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {deal.account}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Person sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {deal.contact}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <AttachMoney sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2" fontWeight="medium">
                        ${deal.amount.toLocaleString()}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={deal.stage}
                      color={getStageColor(deal.stage)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress
                          variant="determinate"
                          value={deal.probability}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                      </Box>
                      <Typography variant="body2" fontWeight="medium">
                        {deal.probability}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(deal.close_date).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {deal.owner}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={deal.status}
                      color={getStatusColor(deal.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton onClick={(e) => handleMenuOpen(e, deal)} size="small">
                      <MoreVert />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
        <MenuItem onClick={handleMenuClose}>
          <Visibility sx={{ mr: 1 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Edit sx={{ mr: 1 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <TrendingUp sx={{ mr: 1 }} />
          Update Stage
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default DealsList;
