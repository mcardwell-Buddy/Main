import React, { useState } from 'react';
import './AgentTodoList.css';

/**
 * AgentTodoList Component
 * 
 * Displays the agent's reasoning steps as an interactive todo list.
 * Shows:
 * - Current step and total steps
 * - Step status (pending, in-progress, complete)
 * - Expandable details for each step
 * - Overall confidence/progress
 */

const AgentTodoList = ({ todos = [], confidence = 0, currentGoal = '', isOpen = false, onToggle = () => {} }) => {
  const [expandedStep, setExpandedStep] = useState(null);
  
  if (!isOpen || !todos || todos.length === 0) {
    return null;
  }
  
  const completedSteps = todos.filter(t => t.status === 'complete').length;
  const failedSteps = todos.filter(t => t.status === 'failed').length;
  const totalSteps = todos.length;
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete':
        return '✓';
      case 'in-progress':
        return '⟳';
      case 'failed':
        return '✗';
      default:
        return '○';
    }
  };
  
  const getStatusLabel = (status) => {
    switch (status) {
      case 'complete':
        return 'Complete';
      case 'in-progress':
        return 'In Progress';
      case 'failed':
        return 'Failed';
      default:
        return 'Pending';
    }
  };
  
  const formatResult = (result) => {
    if (!result) return null;
    
    if (typeof result === 'string') {
      return result.length > 100 ? result.substring(0, 100) + '...' : result;
    }
    
    if (typeof result === 'object') {
      const keys = Object.keys(result).slice(0, 3);
      return keys.map(k => `${k}: ${JSON.stringify(result[k]).substring(0, 30)}`).join(', ');
    }
    
    return JSON.stringify(result);
  };
  
  return (
    <div className="agent-todo-list">
      <div className="todo-list-header">
        <div className="header-left">
          <h3>🎯 Reasoning Progress</h3>
          <p className="goal-summary">{currentGoal}</p>
        </div>
        
        <button className="close-button" onClick={onToggle}>✕</button>
      </div>
      
      <div className="progress-stats">
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${(completedSteps / totalSteps) * 100}%` }}
          ></div>
        </div>
        
        <div className="progress-info">
          <span className="progress-text">
            {completedSteps} of {totalSteps} steps complete
          </span>
          
          <div className="confidence-meter">
            <div className="confidence-label">Confidence</div>
            <div className="confidence-bar">
              <div 
                className="confidence-fill"
                style={{ width: `${(confidence || 0) * 100}%` }}
              ></div>
            </div>
            <div className="confidence-value">{((confidence || 0) * 100).toFixed(0)}%</div>
          </div>
        </div>
      </div>
      
      <div className="steps-list">
        {todos.map((todo, idx) => (
          <div 
            key={idx}
            className={`step-item step-${todo.status}`}
            onClick={() => setExpandedStep(expandedStep === idx ? null : idx)}
          >
            <div className="step-header">
              <span className={`step-icon icon-${todo.status}`}>
                {getStatusIcon(todo.status)}
              </span>
              
              <span className="step-number">Step {todo.step}</span>
              
              <span className="step-task">{todo.task}</span>
              
              <span className={`step-status status-${todo.status}`}>
                {getStatusLabel(todo.status)}
              </span>
              
              {todo.result && (
                <span className="step-has-result">📋</span>
              )}
              
              <span className={`step-chevron ${expandedStep === idx ? 'open' : ''}`}>
                ▶
              </span>
            </div>
            
            {expandedStep === idx && todo.result && (
              <div className="step-details">
                <div className="details-content">
                  <strong>Result:</strong>
                  <pre>{JSON.stringify(todo.result, null, 2)}</pre>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {failedSteps > 0 && (
        <div className="warning-message">
          ⚠️ {failedSteps} step(s) failed. Check details above.
        </div>
      )}
    </div>
  );
};

export default AgentTodoList;
