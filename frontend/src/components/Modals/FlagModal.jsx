import React, { useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { API_BASE } from '../../api/apiClient';

export default function FlagModal({ 
  showFlagModal, 
  setShowFlagModal,
  selectedStudent,
  activeQuestion,

  practiceVisualAnswer
}) {
  const [flagReason, setFlagReason] = useState('incorrect');
  const [flagComment, setFlagComment] = useState('');
  const [isFlagging, setIsFlagging] = useState(false);

  if (!showFlagModal) return null;
  return (
    <>
<div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(5, 8, 22, 0.85)',
            backdropFilter: 'blur(15px)',
            WebkitBackdropFilter: 'blur(15px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 2000,
            animation: 'fade-in 0.3s ease-out'
          }}
          onClick={() => setShowFlagModal(false)}
        >
          <div 
            className="glass-card animate-scale-up" 
            style={{
              maxWidth: '500px',
              width: '90%',
              padding: '30px',
              position: 'relative',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
              border: '1px solid rgba(239, 68, 68, 0.25)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ textAlign: 'center', marginBottom: '25px' }}>
              <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 15px' }}>
                <AlertTriangle className="w-8 h-8 text-red-400" style={{ color: '#f87171' }} />
              </div>
              <h3 style={{ fontSize: '22px', fontWeight: 800, color: '#f8fafc' }}>Flag Question for Review</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '13px', marginTop: '6px' }}>
                Notice an error? Your feedback helps us maintain high-quality academic content.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '25px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Reason for Flagging:</label>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  {[
                    ['incorrect', 'Incorrect Answer'],
                    ['double_answer', 'Double Answer'],
                    ['typo', 'Typo/Error'],
                    ['other', 'Other']
                  ].map(([val, label]) => (
                    <button
                      key={val}
                      onClick={() => setFlagReason(val)}
                      style={{
                        padding: '10px',
                        borderRadius: '10px',
                        fontSize: '13px',
                        fontWeight: 600,
                        background: flagReason === val ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255,255,255,0.03)',
                        border: flagReason === val ? '1px solid #f87171' : '1px solid rgba(255,255,255,0.1)',
                        color: flagReason === val ? '#f87171' : '#f1f5f9',
                        transition: 'all 0.2s ease'
                      }}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <label style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Additional Comments (Optional):</label>
                <textarea
                  className="premium-input"
                  placeholder="Tell us what's wrong with this question..."
                  value={flagComment}
                  onChange={(e) => setFlagComment(e.target.value)}
                  style={{ minHeight: '100px', fontSize: '14px', padding: '12px' }}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                className="btn-secondary" 
                onClick={() => setShowFlagModal(false)}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button 
                className="btn-primary" 
                onClick={async () => {
                  setIsFlagging(true);
                  try {
                    await fetch(`${API_BASE}/practice/flag`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        student_id: selectedStudent?.id || 0,
                        skill_id: activeQuestion?.skill_id || activeQuestion?.node_id || '',
                        skeleton_id: activeQuestion?.skeleton_id || activeQuestion?.problem_id || '',
                        stem: activeQuestion?.stem || activeQuestion?.question_text || '',
                        correct_answer: String(activeQuestion?.correct_answer || activeQuestion?.format_data?.correct_key || ''),
                        selected_answer: (typeof practiceVisualAnswer === 'object' ? JSON.stringify(practiceVisualAnswer) : String(practiceVisualAnswer || '')) || '',
                        reason: flagReason,
                        comment: flagComment
                      })
                    });
                  } catch (e) {
                    console.error("Failed to submit flag", e);
                  } finally {
                    setIsFlagging(false);
                    setShowFlagModal(false);
                    setFlagReason('incorrect');
                    setFlagComment('');
                  }
                }}
                disabled={isFlagging}
                style={{ flex: 2, background: '#ef4444', borderColor: '#ef4444' }}
              >
                {isFlagging ? 'Flagging...' : '🚩 Submit Flag'}
              </button>
            </div>
          </div>
        </div>
    </>
  );
}
