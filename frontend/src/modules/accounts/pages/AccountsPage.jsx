// frontend/src/modules/accounts/pages/AccountsPage.jsx
/**
 * Accounts page component
 * Placeholder for Phase 2 scaffolding
 */
import React, { useState, useEffect } from 'react';
import AccountList from '../components/AccountList';
import { accountsApi } from '../api/accountsApi';

const AccountsPage = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      const response = await accountsApi.list();
      setAccounts(response.data || []);
    } catch (error) {
      console.error('Error loading accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAccountClick = (account) => {
    console.log('Account clicked:', account);
    // TODO: Navigate to account detail
  };

  if (loading) {
    return <div>Loading accounts...</div>;
  }

  return (
    <div className="accounts-page">
      <h1>Accounts</h1>
      <AccountList accounts={accounts} onAccountClick={handleAccountClick} />
    </div>
  );
};

export default AccountsPage;
