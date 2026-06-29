import React from 'react';
import { SortOrderInteractive } from './VisualSkeletons';
import NumberBondInteractive from './NumberBondInteractive';
import { renderMath } from '../utils/mathUtils';
import { renderVisualInner } from '../utils/renderUtils';
import { Zap } from 'lucide-react';

export default function QuestionRenderer({ question, answer, setAnswer, answerResult }) {
  const questionMode = question.question_mode || question.format;

  // Normalize options to a list of {key, text} objects to support all generator pipelines
  const rawOptions = question.format_data?.mcq_options || question.mcq_options || question.options || [];
  const optionsList = Array.isArray(rawOptions)
    ? rawOptions.map(o => ({
        key: o.key,
        text: String(o.text !== undefined && o.text !== null ? o.text : (o.value ?? ''))
      }))
    : (rawOptions && typeof rawOptions === 'object')
      ? Object.entries(rawOptions).map(([key, val]) => ({
          key,
          text: String(val && typeof val === 'object' ? (val.text !== undefined ? val.text : (val.value ?? '')) : (val ?? ''))
        }))
      : [];

  return (
    <>
      {question.is_worked_example && question.worked_example_steps && (
        <div className="glass-card" style={{ borderLeft: '4px solid hsl(var(--warning))', background: 'rgba(245, 158, 11, 0.05)', marginBottom: '30px', padding: '20px' }}>
          <h4 style={{ color: '#fbbf24', display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '10px' }}>
            <Zap className="w-5 h-5" />
            <span>Worked Example Guidance Scaffold Active</span>
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '15px' }}>
            {question.worked_example_steps.map((step, idx) => (
              <div key={idx} style={{ padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                {step}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Visual Question Rendering OR MCQ Options */}
      {question.is_visual ? (
        /* Visual Question Rendering */
        <div style={{ marginBottom: '30px' }}>
          {question.visual_type === 'SortOrder' || questionMode === 'ordering' ? (
            <SortOrderInteractive 
              params={question.visual_params}
              onAnswer={(ans) => setAnswer(ans)}
              disabled={!!answerResult}
            />
          ) : question.visual_type === 'NumberBond' ? (
            <NumberBondInteractive 
              params={question.visual_params}
              answer={answer}
              onAnswer={(ans) => setAnswer(ans)}
              disabled={!!answerResult}
            />
          ) : question.answer_collection === 'mcq' ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
              {renderVisualInner(
                question.visual_type,
                { ...question.visual_params, is_interactive: false },
                () => {},
                true,
                question.problem_id || question.skeleton_id
              )}
              {optionsList.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', maxWidth: '400px' }}>
                  {optionsList.map(opt => {
                    const isSelected = answer === opt.key;
                    // Properly handle both result structures (lab vs portal)
                    const correctAnsStr = answerResult ? (answerResult.correct_answer !== undefined ? String(answerResult.correct_answer) : null) : null;
                    const optValueStr = String(opt.text);
                    const isCorrectOpt = answerResult && (
                      opt.is_correct || 
                      opt.key === answerResult.correct_answer ||
                      optValueStr === correctAnsStr ||
                      opt.text === correctAnsStr
                    );
                    const isWrong = answerResult && isSelected && !answerResult.is_correct;
                    return (
                      <button
                        key={opt.key}
                        className={`option-btn ${isWrong ? 'incorrect' : isCorrectOpt ? 'correct' : isSelected ? (answerResult ? 'correct' : 'selected') : ''}`}
                        onClick={() => { if (!answerResult) setAnswer(opt.key); }}
                        disabled={!!answerResult}
                        style={{ textAlign: 'left' }}
                      >
                        <div className="option-badge">{isSelected && !answerResult ? '✓' : opt.key}</div>
                        <span>{renderMath(opt.text)}</span>
                      </button>
                    );
                  })}
                </div>
              )}
              {answerResult && question.visual_params?.reveal_display && (
                <div style={{ 
                  marginTop: '12px', 
                  padding: '16px', 
                  background: answerResult.is_correct ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', 
                  borderRadius: '8px',
                  textAlign: 'center',
                }}>
                  <div style={{ fontSize: '28px', letterSpacing: '4px', marginBottom: '8px' }}>
                    {question.visual_params.reveal_display}
                  </div>
                  {question.visual_params.reveal_text && (
                    <div style={{ fontSize: '16px', color: '#94a3b8' }}>
                      {question.visual_params.reveal_text} left
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (question.visual_params?.is_interactive || question.interaction_mode === 'set') ? (
            renderVisualInner(
              question.visual_type,
              question.visual_params,
              (ans) => setAnswer(ans),
              !!answerResult,
              question.problem_id || question.skeleton_id
            )
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
              {renderVisualInner(
                question.visual_type,
                { ...question.visual_params, is_interactive: false },
                () => {},
                true,
                question.problem_id || question.skeleton_id
              )}
              <input
                type="text"
                className="premium-input"
                placeholder="Enter your answer..."
                value={answer ?? ''}
                onChange={e => setAnswer(e.target.value)}
                disabled={!!answerResult}
                style={{ 
                  padding: '14px 16px', 
                  fontSize: '18px', 
                  textAlign: 'center',
                  fontWeight: 600,
                  borderRadius: '10px',
                  maxWidth: '250px',
                }}
                autoFocus
              />
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '30px', width: '100%', alignItems: 'center' }}>
          {/* Cloze / fill-in-blank format */}
          {(questionMode === 'cloze' || questionMode === 'fill_in_blank') && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '300px' }}>
              <input
                type="text"
                className="premium-input"
                placeholder="Fill in the blank..."
                value={answer ?? ''}
                onChange={e => setAnswer(e.target.value)}
                disabled={!!answerResult}
                style={{ 
                  padding: '14px 16px', 
                  fontSize: '18px', 
                  textAlign: 'center',
                  fontWeight: 600,
                  borderRadius: '10px',
                }}
                autoFocus
              />
            </div>
          )}

          {/* Numeric input format */}
          {(questionMode === 'numeric_input' || questionMode === 'integer' || questionMode === 'decimal') && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '300px' }}>
              <input
                type="number"
                className="premium-input"
                placeholder="Enter number..."
                value={answer ?? ''}
                onChange={e => setAnswer(e.target.value)}
                disabled={!!answerResult}
                style={{ 
                  padding: '14px 16px', 
                  fontSize: '18px', 
                  textAlign: 'center',
                  fontWeight: 600,
                  borderRadius: '10px',
                }}
                autoFocus
              />
            </div>
          )}

          {/* Text input fallback */}
          {(questionMode === 'writing_prompt' || questionMode === 'text_input') && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
              <textarea
                className="premium-input"
                placeholder="Write your answer here..."
                value={answer ?? ''}
                onChange={e => setAnswer(e.target.value)}
                disabled={!!answerResult}
                rows={4}
                style={{ 
                  padding: '14px 16px', 
                  fontSize: '16px', 
                  borderRadius: '10px',
                  resize: 'vertical',
                }}
                autoFocus
              />
            </div>
          )}

          {/* Standard MCQ format */}
          {(questionMode === 'mcq' && optionsList.length > 0) && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', maxWidth: '500px' }}>
              {optionsList.map((opt) => {
                const isSelected = answer === opt.key;
                const correctAnsStr = answerResult ? (answerResult.correct_answer !== undefined ? String(answerResult.correct_answer) : null) : null;
                const optValueStr = String(opt.text);
                const isCorrectOpt = answerResult && (
                  opt.is_correct || 
                  opt.key === answerResult.correct_answer ||
                  optValueStr === correctAnsStr ||
                  opt.text === correctAnsStr
                );
                const isWrong = answerResult && isSelected && !answerResult.is_correct;

                return (
                  <button
                    key={opt.key}
                    className={`option-btn ${isWrong ? 'incorrect' : isCorrectOpt ? 'correct' : isSelected ? (answerResult ? 'correct' : 'selected') : ''}`}
                    onClick={() => { if (!answerResult) setAnswer(opt.key); }}
                    disabled={!!answerResult}
                    style={{ textAlign: 'left' }}
                  >
                    <div className="option-badge">{isSelected && !answerResult ? '✓' : opt.key}</div>
                    <span>{renderMath(opt.text)}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* True/False format */}
          {questionMode === 'true_false' && (
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', width: '100%', maxWidth: '400px' }}>
              {['True', 'False'].map(val => {
                const isSelected = answer === val;
                const isCorrect = answerResult && answerResult.is_correct && isSelected;
                const isWrong = answerResult && !answerResult.is_correct && isSelected;
                const isCorrectAnswer = answerResult && !answerResult.is_correct && String(question.correct_answer) === val;
                return (
                  <button
                    key={val}
                    className={`option-btn ${isWrong ? 'incorrect' : (isCorrect || isCorrectAnswer) ? 'correct' : isSelected ? 'selected' : ''}`}
                    onClick={() => { if (!answerResult) setAnswer(val); }}
                    disabled={!!answerResult}
                    style={{ 
                      flex: 1, 
                      padding: '16px 24px', 
                      fontSize: '16px',
                      fontWeight: 600,
                      justifyContent: 'center',
                    }}
                  >
                    {val}
                  </button>
                );
              })}
            </div>
          )}

          {/* Ordering format */}
          {questionMode === 'ordering' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '400px' }}>
              <p style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', margin: 0, textAlign: 'center' }}>
                Enter the values in the correct order, separated by commas:
              </p>
              <input
                type="text"
                className="premium-input"
                placeholder="e.g., 1, 2, 3, 4"
                value={answer ?? ''}
                onChange={e => setAnswer(e.target.value)}
                disabled={!!answerResult}
                style={{ 
                  padding: '14px 16px', 
                  fontSize: '16px', 
                  textAlign: 'center',
                }}
                autoFocus
              />
            </div>
          )}
        </div>
      )}
    </>
  );
}
