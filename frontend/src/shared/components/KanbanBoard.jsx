// frontend/src/shared/components/KanbanBoard.jsx
/**
 * Kanban board component for deals pipeline
 * Placeholder for Phase 2 scaffolding
 */
import React from 'react';

const KanbanBoard = ({ stages = [], cards = [], onCardMove }) => {
  const getStageCards = (stageId) => {
    return cards.filter(card => card.stageId === stageId);
  };

  return (
    <div className="kanban-board">
      <div className="kanban-stages">
        {stages.map(stage => (
          <div key={stage.id} className="kanban-stage">
            <h3>{stage.name}</h3>
            <div className="kanban-cards">
              {getStageCards(stage.id).map(card => (
                <div key={card.id} className="kanban-card">
                  <h4>{card.title}</h4>
                  {card.amount && <p>Amount: ${card.amount}</p>}
                  {card.owner && <small>Owner: {card.owner}</small>}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KanbanBoard;
