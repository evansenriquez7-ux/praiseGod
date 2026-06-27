import React from 'react';

export default function NumberBondInteractive({ params, answer, onAnswer, disabled }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
      {/* Number bond diagram: whole on top, two parts below, lines edge-to-edge */}
      <svg width="200" height="140" viewBox="0 0 200 140" style={{ overflow: 'visible' }}>
        {/* Lines from circle edge to circle edge */}
        <line x1="85.8" y1="54.1" x2="62.2" y2="94.3" stroke="#6366f1" strokeWidth="2.5" />
        <line x1="114.2" y1="54.1" x2="137.8" y2="94.3" stroke="#6366f1" strokeWidth="2.5" />
        
        {/* Whole circle (top) */}
        <circle cx="100" cy="30" r="28" fill={params?.blank_position === 'whole' ? 'rgba(99,102,241,0.15)' : 'transparent'} stroke="#6366f1" strokeWidth="3" />
        <text x="100" y="36" textAnchor="middle" fill="#f1f5f9" fontSize="20" fontWeight="700">
          {params?.blank_position === 'whole' ? '?' : params?.whole}
        </text>
        
        {/* Part1 circle (bottom-left) */}
        <circle cx="50" cy="115" r="24" fill={params?.blank_position === 'part1' ? 'rgba(16,185,129,0.15)' : 'transparent'} stroke="#10b981" strokeWidth="3" />
        <text x="50" y="121" textAnchor="middle" fill="#f1f5f9" fontSize="18" fontWeight="700">
          {params?.blank_position === 'part1' ? '?' : params?.part1}
        </text>
        
        {/* Part2 circle (bottom-right) */}
        <circle cx="150" cy="115" r="24" fill={params?.blank_position === 'part2' ? 'rgba(16,185,129,0.15)' : 'transparent'} stroke="#10b981" strokeWidth="3" />
        <text x="150" y="121" textAnchor="middle" fill="#f1f5f9" fontSize="18" fontWeight="700">
          {params?.blank_position === 'part2' ? '?' : params?.part2}
        </text>
      </svg>
      {/* Input field for the missing value */}
      <input
        type="number"
        className="premium-input"
        placeholder="Enter the missing number..."
        value={answer ?? ''}
        onChange={e => onAnswer(e.target.value)}
        disabled={disabled}
        style={{ 
          padding: '14px 16px', 
          fontSize: '18px', 
          textAlign: 'center',
          fontWeight: 600,
          borderRadius: '10px',
          maxWidth: '200px',
        }}
        autoFocus
      />
    </div>
  );
}
