import React, { useState } from 'react';

/**
 * Success Feedback - Rate Buddy's Response
 * 
 * This is the critical feedback loop that drives improvement.
 * Measures multiple dimensions of success.
 */
const SuccessFeedback = ({ goalId, messageIndex, onFeedbackSubmitted }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ratings, setRatings] = useState({
    helpfulness: 0,
    accuracy: 0,
    completeness: 0,
    actionability: 0,
    codeQuality: 0,
  });
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const dimensions = [
    {
      key: 'helpfulness',
      label: '💡 Was this response helpful?',
      description: 'Did it provide useful information?'
    },
    {
      key: 'accuracy',
      label: '✓ Was it accurate?',
      description: 'Was the information correct?'
    },
    {
      key: 'completeness',
      label: '📋 Was it complete?',
      description: 'Did it fully answer your question?'
    },
    {
      key: 'actionability',
      label: '🎯 Can you act on it?',
      description: 'Is it practical and actionable?'
    },
    {
      key: 'codeQuality',
      label: '🔧 Code Quality (if applicable)',
      description: 'For code solutions, does it work?'
    },
  ];

  const handleSubmitFeedback = async () => {
    setIsSubmitting(true);

    try {
      const response = await fetch('http://localhost:8000/success/submit-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          goal_id: goalId,
          helpfulness: ratings.helpfulness || null,
          accuracy: ratings.accuracy || null,
          completeness: ratings.completeness || null,
          actionability: ratings.actionability || null,
          code_quality: ratings.codeQuality || null,
          notes: notes
        })
      });

      const data = await response.json();

      if (data.success) {
        setSubmitted(true);
        setTimeout(() => {
          setIsOpen(false);
          setSubmitted(false);
          setRatings({ helpfulness: 0, accuracy: 0, completeness: 0, actionability: 0, codeQuality: 0 });
          setNotes('');
          if (onFeedbackSubmitted) onFeedbackSubmitted(data.success_score);
        }, 1500);
      }
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="success-feedback submitted">
        <div className="checkmark">✓</div>
        <p>Thank you! Your feedback helps me improve.</p>
      </div>
    );
  }

  return (
    <>
      {!isOpen && (
        <button
          className="feedback-trigger"
          onClick={() => setIsOpen(true)}
          title="Rate this response - your feedback helps me improve"
        >
          👍 Rate Response
        </button>
      )}

      {isOpen && (
        <div className="success-feedback-panel">
          <div className="feedback-header">
            <h3>How helpful was this response?</h3>
            <button className="close-btn" onClick={() => setIsOpen(false)}>✕</button>
          </div>

          <div className="feedback-dimensions">
            {dimensions.map((dim) => (
              <div key={dim.key} className="dimension">
                <label>{dim.label}</label>
                <p className="description">{dim.description}</p>
                <div className="rating-buttons">
                  {[1, 2, 3, 4, 5].map((score) => (
                    <button
                      key={score}
                      className={`rating-btn ${ratings[dim.key] === score ? 'selected' : ''}`}
                      onClick={() => setRatings({ ...ratings, [dim.key]: score })}
                      data-score={score}
                    >
                      {score}
                    </button>
                  ))}
                </div>
                <div className="scale-label">
                  <span>Not helpful</span>
                  <span>Very helpful</span>
                </div>
              </div>
            ))}
          </div>

          <div className="feedback-notes">
            <label>📝 Additional Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What could I improve? Any specific issues?"
              rows="3"
            />
          </div>

          <div className="feedback-actions">
            <button
              className="submit-feedback-btn"
              onClick={handleSubmitFeedback}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
            <button className="cancel-btn" onClick={() => setIsOpen(false)}>
              Skip
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .feedback-trigger {
          padding: 6px 12px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 13px;
          font-weight: 500;
          margin-top: 8px;
          transition: all 0.2s ease;
        }

        .feedback-trigger:hover {
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .success-feedback {
          margin-top: 12px;
          padding: 12px;
          background: #f0f4ff;
          border-left: 4px solid #667eea;
          border-radius: 6px;
          text-align: center;
        }

        .success-feedback.submitted {
          background: #f0fdf4;
          border-left-color: #22c55e;
        }

        .success-feedback .checkmark {
          font-size: 24px;
          margin-bottom: 8px;
          animation: scaleIn 0.3s ease;
        }

        @keyframes scaleIn {
          from {
            transform: scale(0);
          }
          to {
            transform: scale(1);
          }
        }

        .success-feedback p {
          margin: 0;
          color: #666;
          font-size: 13px;
        }

        .success-feedback-panel {
          margin-top: 12px;
          padding: 16px;
          background: #f8fafc;
          border: 2px solid #e0e7ff;
          border-radius: 8px;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        }

        .feedback-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          border-bottom: 2px solid #e0e7ff;
          padding-bottom: 12px;
        }

        .feedback-header h3 {
          margin: 0;
          color: #1e293b;
          font-size: 14px;
          font-weight: 600;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 18px;
          cursor: pointer;
          color: #999;
          padding: 0;
          width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .close-btn:hover {
          color: #333;
        }

        .feedback-dimensions {
          display: flex;
          flex-direction: column;
          gap: 16px;
          margin-bottom: 16px;
        }

        .dimension {
          background: white;
          padding: 12px;
          border-radius: 6px;
          border: 1px solid #e5e7eb;
        }

        .dimension label {
          display: block;
          font-weight: 600;
          color: #1e293b;
          font-size: 13px;
          margin-bottom: 4px;
        }

        .description {
          margin: 4px 0 8px 0;
          color: #666;
          font-size: 12px;
        }

        .rating-buttons {
          display: flex;
          gap: 6px;
          margin-bottom: 6px;
        }

        .rating-btn {
          flex: 1;
          padding: 8px;
          border: 2px solid #e5e7eb;
          background: white;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
          transition: all 0.2s ease;
          color: #666;
        }

        .rating-btn:hover {
          border-color: #667eea;
          color: #667eea;
        }

        .rating-btn.selected {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-color: #667eea;
        }

        .scale-label {
          display: flex;
          justify-content: space-between;
          font-size: 11px;
          color: #999;
        }

        .feedback-notes {
          margin-bottom: 16px;
        }

        .feedback-notes label {
          display: block;
          font-weight: 600;
          color: #1e293b;
          font-size: 13px;
          margin-bottom: 6px;
        }

        .feedback-notes textarea {
          width: 100%;
          padding: 8px;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          font-family: inherit;
          font-size: 13px;
          resize: vertical;
          font-family: monospace;
        }

        .feedback-notes textarea:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .feedback-actions {
          display: flex;
          gap: 8px;
        }

        .submit-feedback-btn {
          flex: 1;
          padding: 10px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
          transition: all 0.2s ease;
        }

        .submit-feedback-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }

        .submit-feedback-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .cancel-btn {
          padding: 10px 16px;
          background: white;
          color: #666;
          border: 1px solid #e5e7eb;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
          font-size: 13px;
          transition: all 0.2s ease;
        }

        .cancel-btn:hover {
          border-color: #667eea;
          color: #667eea;
        }
      `}</style>
    </>
  );
};

export default SuccessFeedback;
