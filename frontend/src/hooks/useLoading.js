// frontend/src/hooks/useLoading.js
// Loading state management hook - Phase 7

import { useState, useCallback } from 'react';

export const useLoading = (initialState = false) => {
  const [isLoading, setIsLoading] = useState(initialState);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const startLoading = useCallback(() => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);
  }, []);

  const stopLoading = useCallback(() => {
    setIsLoading(false);
  }, []);

  const setLoadingError = useCallback((errorMessage) => {
    setError(errorMessage);
    setIsLoading(false);
  }, []);

  const setLoadingSuccess = useCallback((successMessage) => {
    setSuccess(successMessage);
    setIsLoading(false);
  }, []);

  const resetLoading = useCallback(() => {
    setIsLoading(false);
    setError(null);
    setSuccess(null);
  }, []);

  const withLoading = useCallback(async (asyncFn) => {
    startLoading();
    try {
      const result = await asyncFn();
      stopLoading();
      return result;
    } catch (err) {
      setLoadingError(err.message || 'An error occurred');
      throw err;
    }
  }, [startLoading, stopLoading, setLoadingError]);

  return {
    isLoading,
    error,
    success,
    startLoading,
    stopLoading,
    setLoadingError,
    setLoadingSuccess,
    resetLoading,
    withLoading,
  };
};

export default useLoading;
