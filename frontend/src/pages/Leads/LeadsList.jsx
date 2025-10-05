// frontend/src/pages/Leads/LeadsList.jsx
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
} from '@mui/material';
import {
  Add,
  Search,
  MoreVert,
  Edit,
  Delete,
  Visibility,
  Person,
  Phone,
  Email,
  Business,
  TrendingUp,
} from '@mui/icons-material';

const LeadsList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedLead, setSelectedLead] = useState(null);

  // Mock data
  const leads = [
    {
      id: 1,
      first_name: 'John',
      last_name: 'Doe',
      company_name: 'Acme Corp',
      email: 'john@acme.com',
      phone: '+1-555-0123',
      source: 'Website',
      status: 'New',
      rating: 'Hot',
      lead_score: 85,
      owner: 'Jane Smith',
      created_at: '2024-01-15',
    },
    {
      id: 2,
      first_name: 'Jane',
      last_name: 'Smith',
      company_name: 'Tech Solutions',
      email: 'jane@techsolutions.com',
      phone: '+1-555-0124',
      source: 'Referral',
      status: 'Qualified',
      rating: 'Warm',
      lead_score: 65,
      owner: 'Mike Johnson',
      created_at: '2024-01-10',
    },
  ];

  const handleMenuOpen = (event, lead) => {
    setAnchorEl(event.currentTarget);
    setSelectedLead(lead);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedLead(null);
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

  const filteredLeads = leads.filter(lead =>
    `${lead.first_name} ${lead.last_name}`.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    lead.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Leads
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your sales leads
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} size="large">
          Add Lead
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search leads..."
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
                <TableCell>Lead</TableCell>
                <TableCell>Company</TableCell>
                <TableCell>Source</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Rating</TableCell>
                <TableCell>Score</TableCell>
                <TableCell>Owner</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredLeads.map((lead) => (
                <TableRow key={lead.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                        {lead.first_name.charAt(0)}
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {lead.first_name} {lead.last_name}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                          <Email sx={{ fontSize: 14, mr: 0.5, color: 'text.secondary' }} />
                          <Typography variant="body2" color="text.secondary">
                            {lead.email}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Business sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {lead.company_name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {lead.source}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={lead.status}
                      color={getStatusColor(lead.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={lead.rating}
                      color={getRatingColor(lead.rating)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <TrendingUp sx={{ fontSize: 16, mr: 0.5, color: 'primary.main' }} />
                      <Typography variant="body2" fontWeight="medium">
                        {lead.lead_score}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {lead.owner}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(lead.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton onClick={(e) => handleMenuOpen(e, lead)} size="small">
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
          Convert
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default LeadsList;
