// frontend/src/components/common/PerformanceOptimizer.jsx
// Enterprise-grade performance optimization components

import React, { memo, useMemo, useCallback, Suspense, lazy } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { Skeleton } from '@mui/material';

// Lazy loading components
const DataTable = lazy(() => import('./DataTable'));
const Chart = lazy(() => import('./Chart'));
const Map = lazy(() => import('./Map'));

// Memoized components for performance
const MemoizedDataTable = memo(DataTable);
const MemoizedChart = memo(Chart);
const MemoizedMap = memo(Map);

// Virtual scrolling for large datasets
export const VirtualList = memo(({ 
  items, 
  itemHeight = 50, 
  containerHeight = 400,
  renderItem 
}) => {
  const [scrollTop, setScrollTop] = React.useState(0);
  
  const visibleItems = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight) + 1,
      items.length
    );
    
    return items.slice(startIndex, endIndex).map((item, index) => ({
      ...item,
      index: startIndex + index
    }));
  }, [items, scrollTop, itemHeight, containerHeight]);
  
  const totalHeight = items.length * itemHeight;
  const offsetY = Math.floor(scrollTop / itemHeight) * itemHeight;
  
  return (
    <div 
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={(e) => setScrollTop(e.target.scrollTop)}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item) => (
            <div key={item.index} style={{ height: itemHeight }}>
              {renderItem(item)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

// Infinite scrolling hook
export const useInfiniteScroll = (fetchMore, hasMore, loading) => {
  const [isFetching, setIsFetching] = React.useState(false);
  
  const handleScroll = useCallback(() => {
    if (window.innerHeight + document.documentElement.scrollTop 
        >= document.documentElement.offsetHeight - 1000) {
      if (hasMore && !loading && !isFetching) {
        setIsFetching(true);
        fetchMore().finally(() => setIsFetching(false));
      }
    }
  }, [fetchMore, hasMore, loading, isFetching]);
  
  React.useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);
  
  return isFetching;
};

// Debounced search hook
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = React.useState(value);
  
  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(handler);
  }, [value, delay]);
  
  return debouncedValue;
};

// Performance monitoring component
export const PerformanceMonitor = ({ children, name }) => {
  const startTime = React.useRef(performance.now());
  
  React.useEffect(() => {
    const endTime = performance.now();
    const duration = endTime - startTime.current;
    
    if (duration > 100) { // Log slow components
      console.warn(`Slow component: ${name} took ${duration.toFixed(2)}ms`);
    }
  });
  
  return children;
};

// Error boundary with fallback
export const ErrorFallback = ({ error, resetErrorBoundary }) => (
  <div role="alert" style={{ padding: '20px', textAlign: 'center' }}>
    <h2>Something went wrong:</h2>
    <pre style={{ color: 'red' }}>{error.message}</pre>
    <button onClick={resetErrorBoundary}>Try again</button>
  </div>
);

// Loading skeleton component
export const LoadingSkeleton = ({ variant = 'rectangular', ...props }) => (
  <Skeleton variant={variant} {...props} />
);

// Optimized data table with virtualization
export const OptimizedDataTable = memo(({ 
  data, 
  columns, 
  loading = false,
  onRowClick,
  ...props 
}) => {
  const [sortConfig, setSortConfig] = React.useState({ key: null, direction: 'asc' });
  const [filterConfig, setFilterConfig] = React.useState({});
  
  // Memoized sorted and filtered data
  const processedData = useMemo(() => {
    let result = [...data];
    
    // Apply sorting
    if (sortConfig.key) {
      result.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    
    // Apply filtering
    Object.entries(filterConfig).forEach(([key, value]) => {
      if (value) {
        result = result.filter(item => 
          String(item[key]).toLowerCase().includes(value.toLowerCase())
        );
      }
    });
    
    return result;
  }, [data, sortConfig, filterConfig]);
  
  const handleSort = useCallback((key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  }, []);
  
  const handleFilter = useCallback((key, value) => {
    setFilterConfig(prev => ({
      ...prev,
      [key]: value
    }));
  }, []);
  
  if (loading) {
    return <LoadingSkeleton variant="rectangular" height={400} />;
  }
  
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Suspense fallback={<LoadingSkeleton variant="rectangular" height={400} />}>
        <MemoizedDataTable
          data={processedData}
          columns={columns}
          onRowClick={onRowClick}
          onSort={handleSort}
          onFilter={handleFilter}
          sortConfig={sortConfig}
          filterConfig={filterConfig}
          {...props}
        />
      </Suspense>
    </ErrorBoundary>
  );
});

// Optimized chart component
export const OptimizedChart = memo(({ 
  data, 
  type = 'line',
  loading = false,
  ...props 
}) => {
  const memoizedData = useMemo(() => data, [data]);
  
  if (loading) {
    return <LoadingSkeleton variant="rectangular" height={300} />;
  }
  
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Suspense fallback={<LoadingSkeleton variant="rectangular" height={300} />}>
        <MemoizedChart
          data={memoizedData}
          type={type}
          {...props}
        />
      </Suspense>
    </ErrorBoundary>
  );
});

// Optimized map component
export const OptimizedMap = memo(({ 
  locations, 
  loading = false,
  ...props 
}) => {
  const memoizedLocations = useMemo(() => locations, [locations]);
  
  if (loading) {
    return <LoadingSkeleton variant="rectangular" height={400} />;
  }
  
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <Suspense fallback={<LoadingSkeleton variant="rectangular" height={400} />}>
        <MemoizedMap
          locations={memoizedLocations}
          {...props}
        />
      </Suspense>
    </ErrorBoundary>
  );
});

// Performance-optimized form component
export const OptimizedForm = memo(({ 
  initialValues,
  onSubmit,
  validationSchema,
  children,
  ...props 
}) => {
  const [values, setValues] = React.useState(initialValues);
  const [errors, setErrors] = React.useState({});
  const [touched, setTouched] = React.useState({});
  
  const handleChange = useCallback((name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  }, [errors]);
  
  const handleBlur = useCallback((name) => {
    setTouched(prev => ({ ...prev, [name]: true }));
    
    // Validate field
    if (validationSchema && validationSchema[name]) {
      const error = validationSchema[name](values[name]);
      if (error) {
        setErrors(prev => ({ ...prev, [name]: error }));
      }
    }
  }, [values, validationSchema]);
  
  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    
    // Validate all fields
    const newErrors = {};
    if (validationSchema) {
      Object.keys(validationSchema).forEach(field => {
        const error = validationSchema[field](values[field]);
        if (error) {
          newErrors[field] = error;
        }
      });
    }
    
    if (Object.keys(newErrors).length === 0) {
      onSubmit(values);
    } else {
      setErrors(newErrors);
    }
  }, [values, validationSchema, onSubmit]);
  
  return (
    <form onSubmit={handleSubmit} {...props}>
      {React.Children.map(children, child => 
        React.cloneElement(child, {
          values,
          errors,
          touched,
          onChange: handleChange,
          onBlur: handleBlur
        })
      )}
    </form>
  );
});

// Export all components
export default {
  VirtualList,
  useInfiniteScroll,
  useDebounce,
  PerformanceMonitor,
  ErrorFallback,
  LoadingSkeleton,
  OptimizedDataTable,
  OptimizedChart,
  OptimizedMap,
  OptimizedForm
};
