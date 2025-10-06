// frontend/src/shared/components/SavedViews.jsx
/**
 * Saved views/filters component
 * Placeholder for Phase 2 scaffolding
 */
import React, { useState } from 'react';

const SavedViews = ({ views = [], onViewSelect, onViewSave, onViewDelete }) => {
  const [activeView, setActiveView] = useState(null);

  const handleViewClick = (view) => {
    setActiveView(view);
    onViewSelect?.(view);
  };

  return (
    <div className="saved-views">
      <h3>Saved Views</h3>
      <ul>
        {views.map(view => (
          <li
            key={view.id}
            className={activeView?.id === view.id ? 'active' : ''}
            onClick={() => handleViewClick(view)}
          >
            <span>{view.name}</span>
            {view.description && <small>{view.description}</small>}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SavedViews;
