// frontend/src/store/slices/companySlice.js
// Company Redux Slice

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { companyAPI } from '../../services/api/company';

// Async thunks
export const getCompanies = createAsyncThunk(
  'company/getCompanies',
  async (_, { rejectWithValue }) => {
    try {
      const response = await companyAPI.getCompanies();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const switchCompany = createAsyncThunk(
  'company/switchCompany',
  async (companyId, { rejectWithValue }) => {
    try {
      const response = await companyAPI.switchCompany(companyId);
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

export const getCurrentCompany = createAsyncThunk(
  'company/getCurrentCompany',
  async (_, { rejectWithValue }) => {
    try {
      const response = await companyAPI.getCurrentCompany();
      return response.data;
    } catch (error) {
      return rejectWithValue(error.response?.data || error.message);
    }
  }
);

// Initial state
const initialState = {
  companies: [],
  currentCompany: null,
  isLoading: false,
  error: null,
};

// Company slice
const companySlice = createSlice({
  name: 'company',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setCurrentCompany: (state, action) => {
      state.currentCompany = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Get companies
      .addCase(getCompanies.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(getCompanies.fulfilled, (state, action) => {
        state.isLoading = false;
        state.companies = action.payload;
      })
      .addCase(getCompanies.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      
      // Switch company
      .addCase(switchCompany.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(switchCompany.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentCompany = action.payload;
      })
      .addCase(switchCompany.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      })
      
      // Get current company
      .addCase(getCurrentCompany.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(getCurrentCompany.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentCompany = action.payload;
      })
      .addCase(getCurrentCompany.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload;
      });
  },
});

export const { clearError, setCurrentCompany } = companySlice.actions;
export default companySlice.reducer;
