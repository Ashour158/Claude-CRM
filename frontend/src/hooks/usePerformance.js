// frontend/src/hooks/usePerformance.js
// Enterprise-grade performance hooks

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

// Performance monitoring hook
export const usePerformanceMonitor = (componentName) => {
  const startTime = useRef(performance.now());
  const [metrics, setMetrics] = useState({
    renderTime: 0,
    renderCount: 0,
    memoryUsage: 0
  });

  useEffect(() => {
    const endTime = performance.now();
    const renderTime = endTime - startTime.current;
    
    setMetrics(prev => ({
      ...prev,
      renderTime,
      renderCount: prev.renderCount + 1,
      memoryUsage: performance.memory?.usedJSHeapSize || 0
    }));

    // Log performance issues
    if (renderTime > 100) {
      console.warn(`Slow render in ${componentName}: ${renderTime.toFixed(2)}ms`);
    }
  });

  return metrics;
};

// Debounced value hook
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// Throttled callback hook
export const useThrottle = (callback, delay) => {
  const lastRun = useRef(Date.now());

  return useCallback((...args) => {
    if (Date.now() - lastRun.current >= delay) {
      callback(...args);
      lastRun.current = Date.now();
    }
  }, [callback, delay]);
};

// Memoized selector hook
export const useMemoizedSelector = (selector, deps) => {
  return useMemo(() => selector(), deps);
};

// Optimized query hook with caching
export const useOptimizedQuery = (queryKey, queryFn, options = {}) => {
  const {
    staleTime = 5 * 60 * 1000, // 5 minutes
    cacheTime = 10 * 60 * 1000, // 10 minutes
    refetchOnWindowFocus = false,
    retry = 3,
    retryDelay = attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...restOptions
  } = options;

  return useQuery({
    queryKey,
    queryFn,
    staleTime,
    cacheTime,
    refetchOnWindowFocus,
    retry,
    retryDelay,
    ...restOptions
  });
};

// Optimized mutation hook
export const useOptimizedMutation = (mutationFn, options = {}) => {
  const queryClient = useQueryClient();
  
  const {
    onSuccess,
    onError,
    onSettled,
    ...restOptions
  } = options;

  return useMutation({
    mutationFn,
    onSuccess: (data, variables, context) => {
      // Invalidate related queries
      queryClient.invalidateQueries();
      onSuccess?.(data, variables, context);
    },
    onError,
    onSettled,
    ...restOptions
  });
};

// Infinite scroll hook
export const useInfiniteScroll = (fetchNextPage, hasNextPage, isFetching) => {
  const [isFetchingMore, setIsFetchingMore] = useState(false);

  const handleScroll = useCallback(() => {
    if (
      window.innerHeight + document.documentElement.scrollTop
      >= document.documentElement.offsetHeight - 1000
    ) {
      if (hasNextPage && !isFetching && !isFetchingMore) {
        setIsFetchingMore(true);
        fetchNextPage().finally(() => setIsFetchingMore(false));
      }
    }
  }, [fetchNextPage, hasNextPage, isFetching, isFetchingMore]);

  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  return isFetchingMore;
};

// Virtual scrolling hook
export const useVirtualScroll = (items, itemHeight, containerHeight) => {
  const [scrollTop, setScrollTop] = useState(0);

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

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);

  return {
    visibleItems,
    totalHeight,
    offsetY,
    handleScroll
  };
};

// Local storage hook with performance optimization
export const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
};

// Session storage hook
export const useSessionStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.sessionStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading sessionStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.sessionStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting sessionStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
};

// Intersection observer hook for lazy loading
export const useIntersectionObserver = (options = {}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const ref = useRef();

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        if (entry.isIntersecting && !hasIntersected) {
          setHasIntersected(true);
        }
      },
      {
        threshold: 0.1,
        ...options
      }
    );

    observer.observe(element);

    return () => {
      observer.unobserve(element);
    };
  }, [hasIntersected, options]);

  return [ref, isIntersecting, hasIntersected];
};

// Web worker hook
export const useWebWorker = (workerScript) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const workerRef = useRef();

  useEffect(() => {
    workerRef.current = new Worker(workerScript);
    
    workerRef.current.onmessage = (event) => {
      setData(event.data);
      setLoading(false);
    };

    workerRef.current.onerror = (error) => {
      setError(error);
      setLoading(false);
    };

    return () => {
      workerRef.current?.terminate();
    };
  }, [workerScript]);

  const postMessage = useCallback((message) => {
    if (workerRef.current) {
      setLoading(true);
      setError(null);
      workerRef.current.postMessage(message);
    }
  }, []);

  return { data, error, loading, postMessage };
};

// Performance metrics hook
export const usePerformanceMetrics = () => {
  const [metrics, setMetrics] = useState({
    fps: 0,
    memory: 0,
    renderTime: 0
  });

  useEffect(() => {
    let frameCount = 0;
    let lastTime = performance.now();
    let animationId;

    const measurePerformance = () => {
      frameCount++;
      const currentTime = performance.now();
      
      if (currentTime - lastTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (currentTime - lastTime));
        const memory = performance.memory?.usedJSHeapSize || 0;
        
        setMetrics(prev => ({
          ...prev,
          fps,
          memory: Math.round(memory / 1024 / 1024) // MB
        }));
        
        frameCount = 0;
        lastTime = currentTime;
      }
      
      animationId = requestAnimationFrame(measurePerformance);
    };

    animationId = requestAnimationFrame(measurePerformance);

    return () => {
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
    };
  }, []);

  return metrics;
};

// Batch updates hook
export const useBatchUpdates = () => {
  const [updates, setUpdates] = useState([]);
  const timeoutRef = useRef();

  const addUpdate = useCallback((update) => {
    setUpdates(prev => [...prev, update]);
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      // Process all updates
      updates.forEach(update => update());
      setUpdates([]);
    }, 16); // ~60fps
  }, [updates]);

  return addUpdate;
};

// Memory usage hook
export const useMemoryUsage = () => {
  const [memoryInfo, setMemoryInfo] = useState({
    used: 0,
    total: 0,
    limit: 0
  });

  useEffect(() => {
    const updateMemoryInfo = () => {
      if (performance.memory) {
        setMemoryInfo({
          used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
          total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
          limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
        });
      }
    };

    updateMemoryInfo();
    const interval = setInterval(updateMemoryInfo, 1000);

    return () => clearInterval(interval);
  }, []);

  return memoryInfo;
};

export default {
  usePerformanceMonitor,
  useDebounce,
  useThrottle,
  useMemoizedSelector,
  useOptimizedQuery,
  useOptimizedMutation,
  useInfiniteScroll,
  useVirtualScroll,
  useLocalStorage,
  useSessionStorage,
  useIntersectionObserver,
  useWebWorker,
  usePerformanceMetrics,
  useBatchUpdates,
  useMemoryUsage
};
