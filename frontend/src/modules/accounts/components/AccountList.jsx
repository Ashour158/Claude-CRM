// frontend/src/modules/accounts/components/AccountList.jsx
/**
 * Account list component
 * Placeholder for Phase 2 scaffolding
 */
import React from 'react';

const AccountList = ({ accounts = [], onAccountClick }) => {
  return (
    <div className="account-list">
      <h2>Accounts</h2>
      {accounts.length === 0 ? (
        <p>No accounts found.</p>
      ) : (
        <ul>
          {accounts.map(account => (
            <li key={account.id} onClick={() => onAccountClick?.(account)}>
              <strong>{account.name}</strong>
              {account.email && <span> - {account.email}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default AccountList;
