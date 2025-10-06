// frontend/src/shared/components/GlobalSearch.jsx
/**
 * Global search component
 * Placeholder for Phase 2 scaffolding
 */
import React, { useState } from 'react';

const GlobalSearch = ({ onSearch, onResultClick }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    try {
      // TODO: Implement actual search
      const searchResults = await onSearch?.(query);
      setResults(searchResults || []);
    } catch (error) {
      console.error('Search error:', error);
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="global-search">
      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search accounts, contacts, leads..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={searching}>
          {searching ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results.length > 0 && (
        <div className="search-results">
          {results.map(result => (
            <div
              key={result.id}
              className="search-result"
              onClick={() => onResultClick?.(result)}
            >
              <strong>{result.title}</strong>
              <span className="result-type">{result.type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GlobalSearch;
