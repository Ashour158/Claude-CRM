// frontend/src/pages/Territories/TerritoriesList.jsx
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
  Public,
  Person,
  Business,
} from '@mui/icons-material';

const TerritoriesList = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedTerritory, setSelectedTerritory] = useState(null);

  // Mock data
  const territories = [
    {
      id: 1,
      name: 'North America',
      description: 'North American sales territory',
      manager: 'Jane Smith',
      accounts_count: 25,
      status: 'Active',
      created_at: '2024-01-15',
    },
    {
      id: 2,
      name: 'Europe',
      description: 'European sales territory',
      manager: 'Mike Johnson',
      accounts_count: 18,
      status: 'Active',
      created_at: '2024-01-10',
    },
  ];

  const handleMenuOpen = (event, territory) => {
    setAnchorEl(event.currentTarget);
    setSelectedTerritory(territory);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedTerritory(null);
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

  const filteredTerritories = territories.filter(territory =>
    territory.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    territory.manager.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Territories
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your sales territories
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} size="large">
          Add Territory
        </Button>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search territories..."
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
                <TableCell>Territory</TableCell>
                <TableCell>Manager</TableCell>
                <TableCell>Accounts</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTerritories.map((territory) => (
                <TableRow key={territory.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                        <Public />
                      </Avatar>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {territory.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {territory.description}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Person sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2">
                        {territory.manager}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Business sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2" fontWeight="medium">
                        {territory.accounts_count}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={territory.status}
                      color={getStatusColor(territory.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(territory.created_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <IconButton onClick={(e) => handleMenuOpen(e, territory)} size="small">
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
          <Delete sx={{ mr: 1 }} />
          Delete
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default TerritoriesList;
