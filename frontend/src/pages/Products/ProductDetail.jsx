// frontend/src/pages/Products/ProductDetail.jsx
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
  Inventory,
  AttachMoney,
  Category,
  Description,
  Schedule,
} from '@mui/icons-material';

const ProductDetail = () => {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState(0);
  const [editDialogOpen, setEditDialogOpen] = useState(false);

  // Mock data
  const product = {
    id: id,
    name: 'CRM Software License',
    sku: 'CRM-001',
    description: 'Enterprise CRM software license with full features and support',
    unit_price: 1000,
    category: 'Software',
    status: 'Active',
    created_at: '2024-01-15',
    updated_at: '2024-01-20',
    long_description: 'Comprehensive CRM software solution designed for enterprise use. Includes all core CRM features, advanced reporting, and 24/7 support.',
  };

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
            {product.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip label={product.status} color={getStatusColor(product.status)} size="small" />
            <Typography variant="body2" color="text.secondary">
              SKU: {product.sku}
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
                  <Inventory />
                </Avatar>
                <Box>
                  <Typography variant="h6">{product.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {product.category}
                  </Typography>
                </Box>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Inventory />
                  </ListItemIcon>
                  <ListItemText primary="SKU" secondary={product.sku} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Category />
                  </ListItemIcon>
                  <ListItemText primary="Category" secondary={product.category} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AttachMoney />
                  </ListItemIcon>
                  <ListItemText primary="Price" secondary={`$${product.unit_price.toLocaleString()}`} />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Schedule />
                  </ListItemIcon>
                  <ListItemText primary="Created" secondary={new Date(product.created_at).toLocaleDateString()} />
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
                <Tab label="Details" />
                <Tab label="Pricing" />
                <Tab label="Notes" />
              </Tabs>
            </Box>

            <TabPanel value={activeTab} index={0}>
              <Typography variant="h6" gutterBottom>
                Product Description
              </Typography>
              <Typography variant="body1" paragraph>
                {product.description}
              </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={1}>
              <Typography variant="h6" gutterBottom>
                Product Details
              </Typography>
              <Typography variant="body1" paragraph>
                {product.long_description}
              </Typography>
            </TabPanel>

            <TabPanel value={activeTab} index={2}>
              <Typography variant="h6" gutterBottom>
                Pricing Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Unit Price
                  </Typography>
                  <Typography variant="h6">
                    ${product.unit_price.toLocaleString()}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Category
                  </Typography>
                  <Typography variant="h6">
                    {product.category}
                  </Typography>
                </Grid>
              </Grid>
            </TabPanel>

            <TabPanel value={activeTab} index={3}>
              <Typography variant="h6" gutterBottom>
                Notes
              </Typography>
              <Typography variant="body1" color="text.secondary">
                No notes available. Add a note to track important information about this product.
              </Typography>
            </TabPanel>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Product</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Product Name" defaultValue={product.name} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="SKU" defaultValue={product.sku} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Category" defaultValue={product.category} />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField fullWidth label="Unit Price" type="number" defaultValue={product.unit_price} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Description" defaultValue={product.description} multiline rows={3} />
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

export default ProductDetail;
