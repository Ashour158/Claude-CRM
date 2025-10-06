// frontend/src/modules/activities/components/TimelineWidget.jsx
/**
 * Timeline widget component - displays activity timeline
 */
import React from 'react';

const TimelineWidget = ({ events = [], entityType, entityId }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getEventIcon = (eventType) => {
    const icons = {
      call: '📞',
      email: '📧',
      meeting: '🤝',
      note: '📝',
      creation: '✨',
      update: '📝',
      conversion: '🎯',
      status_change: '🔄',
    };
    return icons[eventType] || '•';
  };

  return (
    <div className="timeline-widget">
      <h3>Activity Timeline</h3>
      {events.length === 0 ? (
        <p>No activities yet.</p>
      ) : (
        <ul className="timeline-list">
          {events.map(event => (
            <li key={event.id} className="timeline-item">
              <span className="timeline-icon">{getEventIcon(event.event_type)}</span>
              <div className="timeline-content">
                <strong>{event.title}</strong>
                {event.description && <p>{event.description}</p>}
                <small>
                  {formatDate(event.event_date)}
                  {event.actor && ` by ${event.actor.name}`}
                </small>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default TimelineWidget;
