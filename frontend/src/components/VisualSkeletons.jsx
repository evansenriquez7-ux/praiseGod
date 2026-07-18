import React, { useState, useEffect, useRef } from 'react';
import { Play, CheckCircle, XCircle, RotateCcw, Plus, Minus } from 'lucide-react';

// ============================================================================
//  UTILITY: Render LaTeX/Math
// ============================================================================
// This assumes the parent App.jsx has a renderMath function available
// For now, we'll use a simple passthrough
const renderMath = (text) => {
  if (!text) return '';
  // Basic inline math rendering (can be enhanced with KaTeX/MathJax)
  return text;
};

// ============================================================================
//  NUMBER LINE INTERACTIVE
// ============================================================================
export function NumberLineInteractive({ params, onAnswer, disabled }) {
  // Extract params - support both old and new formats
  const {
    range,
    divisions,
    correct_position,
    value,
    content_type,
    labels,
    // New params for addition/subtraction read mode
    start = range?.[0] ?? 0,
    end = range?.[1] ?? divisions ?? 10,
    is_interactive = true,
  } = params || {};

  const major_interval = params?.major_interval ?? params?.interval ?? 1;
  const minor_interval = params?.minor_interval ?? params?.interval ?? 1;
  const dot_value = params?.dot_value ?? params?.value ?? params?.correct_position;
  const move_by = params?.move_by ?? 0;

  // Calculate total divisions from end-start
  const totalRange = (end - start) || 10;
  const totalDivisions = divisions ?? Math.round(totalRange / minor_interval) ?? 10;
  
  // Safe resolved values
  const safeMinorInterval = minor_interval || 1;
  const safeMajorInterval = major_interval || 1;

  // Helper to find division index from any dot_value or actual value
  const getDivisionIndex = (val) => {
    if (val === undefined || val === null) return 0;
    if (val >= start && val <= end && totalRange > 0) {
      return Math.round(((val - start) / totalRange) * totalDivisions);
    }
    return Math.max(0, Math.min(totalDivisions, Math.round(val)));
  };

  // position is the actual VALUE on the number line
  const [position, setPosition] = useState(() => {
    // In interactive mode, start at middle; in read mode, use dot_value
    if (is_interactive) {
      return start + Math.floor(totalDivisions / 2) * safeMinorInterval;
    }
    const initialDivIndex = dot_value !== undefined ? getDivisionIndex(dot_value) : Math.floor(totalDivisions / 2);
    return start + initialDivIndex * safeMinorInterval;
  });
  const [isDragging, setIsDragging] = useState(false);
  const hasInteractedRef = useRef(false);
  
  useEffect(() => {
    if (onAnswer && !disabled && !isDragging && hasInteractedRef.current) {
      onAnswer(Math.round(position * 100) / 100);
    }
  }, [position, disabled]);
  const containerRef = useRef(null);
  const dotRef = useRef(null);

  // Reset position when start/end/divisions/intervals change (prevents hanging out-of-bounds dot)
  useEffect(() => {
    const getDivisionIndexLocal = (val) => {
      if (val === undefined || val === null) return 0;
      if (val >= start && val <= end && totalRange > 0) {
        return Math.round(((val - start) / totalRange) * totalDivisions);
      }
      return Math.max(0, Math.min(totalDivisions, Math.round(val)));
    };
    const divIndex = dot_value !== undefined ? getDivisionIndexLocal(dot_value) : Math.floor(totalDivisions / 2);
    setPosition(start + divIndex * safeMinorInterval);
  }, [start, end, totalDivisions, safeMinorInterval, dot_value, totalRange]);

  const handlePositionChange = (snappedPosIndex) => {
    hasInteractedRef.current = true;
    const clampedPosIndex = Math.max(0, Math.min(totalDivisions, snappedPosIndex));
    const actualValue = start + clampedPosIndex * safeMinorInterval;
    setPosition(actualValue);
    if (onAnswer) onAnswer(actualValue);
  };

  // Mouse/Touch dragging
  const handlePointerDown = (e) => {
    if (disabled || !is_interactive) return;
    e.preventDefault();
    setIsDragging(true);
  };

  const handlePointerMove = (e) => {
    if (!isDragging || disabled || !is_interactive) return;
    e.preventDefault();
    
    const rect = containerRef.current.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const x = clientX - rect.left;
    const segmentWidth = rect.width / totalDivisions;
    const snappedPos = Math.round(x / segmentWidth);
    handlePositionChange(snappedPos);
  };

  const handlePointerUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handlePointerMove);
      window.addEventListener('mouseup', handlePointerUp);
      window.addEventListener('touchmove', handlePointerMove);
      window.addEventListener('touchend', handlePointerUp);
      return () => {
        window.removeEventListener('mousemove', handlePointerMove);
        window.removeEventListener('mouseup', handlePointerUp);
        window.removeEventListener('touchmove', handlePointerMove);
        window.removeEventListener('touchend', handlePointerUp);
      };
    }
  }, [isDragging, disabled, is_interactive]);

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (disabled || !is_interactive) return;
    const currentIndex = Math.round((position - start) / safeMinorInterval);
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      handlePositionChange(currentIndex - 1);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      handlePositionChange(currentIndex + 1);
    } else if (e.key === 'Home') {
      e.preventDefault();
      handlePositionChange(0);
    } else if (e.key === 'End') {
      e.preventDefault();
      handlePositionChange(totalDivisions);
    }
  };

  // Click to snap
  const handleTrackClick = (e) => {
    if (disabled || isDragging || !is_interactive) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const segmentWidth = rect.width / totalDivisions;
    const snappedPos = Math.round(x / segmentWidth);
    handlePositionChange(snappedPos);
  };

  // For read mode: show static number line with dot at dot_value
  const isReadMode = dot_value !== undefined && !is_interactive;
  const dotPosition = isReadMode ? dot_value : position;
  const dotDivIndex = getDivisionIndex(dotPosition);
  const dotPercent = totalDivisions > 0 ? (dotDivIndex / totalDivisions) * 100 : 0;

  // Build tick marks with major/minor intervals
  const ticks = [];
  const ticksPerMajor = Math.round(safeMajorInterval / safeMinorInterval);
  for (let i = 0; i <= totalDivisions; i++) {
    const val = start + i * (totalRange / totalDivisions);
    const pct = (i / totalDivisions) * 100;
    
    // Check if it is a major tick
    const isMajor = (ticksPerMajor > 0 && i % ticksPerMajor === 0) || i === 0 || i === totalDivisions;
    
    ticks.push({ value: Math.round(val * 100) / 100, pct, isMajor });
  }


  return (
    <div
      className="number-line-container"
      ref={containerRef}
      tabIndex={disabled || !is_interactive ? -1 : 0}
      onKeyDown={handleKeyDown}
      style={{
        padding: '40px 20px',
        outline: 'none',
        cursor: disabled || !is_interactive ? 'default' : 'pointer',
        width: '100%',
        maxWidth: '500px',
        margin: '0 auto',
      }}
    >
      {/* Number line track */}
      <div
        className="number-line-track"
        onClick={is_interactive ? handleTrackClick : undefined}
        style={{
          position: 'relative',
          height: '6px',
          background: 'hsl(var(--border-color))',
          borderRadius: '3px',
          margin: '20px 0',
          width: '100%',
        }}
      >
        {/* Tick marks with major/minor distinction */}
        {ticks.map((tick, i) => (
          <React.Fragment key={i}>
            {/* Tick line */}
            <div
              className="tick-mark"
              style={{
                position: 'absolute',
                left: `${tick.pct}%`,
                top: '50%',
                transform: 'translate(-50%, -50%)',
                width: tick.isMajor ? '2px' : '1px',
                height: tick.isMajor ? '20px' : '12px',
                background: 'hsl(var(--text-muted))',
                opacity: tick.isMajor ? 1 : 0.5,
              }}
            />
            {/* Label for major ticks */}
            {tick.isMajor && (
              <div
                style={{
                  position: 'absolute',
                  left: `${tick.pct}%`,
                  top: '24px',
                  transform: 'translateX(-50%)',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'hsl(var(--text))',
                  whiteSpace: 'nowrap',
                }}
              >
                {tick.value}
              </div>
            )}
          </React.Fragment>
        ))}

        {/* The dot */}
        <div
          ref={dotRef}
          className="number-line-dot"
          onMouseDown={is_interactive ? handlePointerDown : undefined}
          onTouchStart={is_interactive ? handlePointerDown : undefined}
          style={{
            position: 'absolute',
            left: `${dotPercent}%`,
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: disabled ? 'hsl(var(--text-muted))' : 'hsl(var(--primary))',
            border: '3px solid hsl(var(--card-bg))',
            cursor: disabled || !is_interactive ? 'default' : 'grab',
            transition: isDragging ? 'none' : 'left 0.15s ease-out',
            zIndex: 10,
            boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
          }}
        />
      </div>

      {/* Spacer for tick labels */}
      <div style={{ height: '24px' }} />

      {/* Current selection display - only for interactive mode */}
      {is_interactive && (
        <div
          className="visual-selection"
          style={{
            marginTop: '16px',
            fontSize: '13px',
            color: 'hsl(var(--text-muted))',
            textAlign: 'center',
          }}
        >
          Your answer: Position <strong>{position}</strong>
          {content_type === 'fraction' && ` (${position}/${totalDivisions})`}
          {content_type === 'decimal' && ` (${(position / totalDivisions).toFixed(2)})`}
        </div>
      )}

      {/* Keyboard hint - only for interactive mode */}
      {is_interactive && !disabled && (
        <div
          style={{
            marginTop: '12px',
            fontSize: '11px',
            color: 'hsl(var(--text-muted))',
            textAlign: 'center',
            opacity: 0.6,
          }}
        >
          Click track, drag dot, or use ← → arrow keys
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  CLOCK SET INTERACTIVE
// ============================================================================
export function ClockSetInteractive({ params, onAnswer, disabled }) {
  const { target_time, use_24_hour, show_minutes, hours: targetHours, minutes: targetMinutes } = params;
  const isReadOnly = params.interaction_mode === 'read' || params.is_read_only || !onAnswer;
  const [hours, setHours] = useState(() => {
    if (isReadOnly) {
      return targetHours !== undefined ? targetHours : 3;
    }
    return 12; // In set mode, start at 12:00 to prevent answer leak
  });
  const [minutes, setMinutes] = useState(() => {
    if (isReadOnly) {
      return targetMinutes !== undefined ? targetMinutes : 0;
    }
    return 0; // In set mode, start at 12:00 to prevent answer leak
  });
  const [selectedHand, setSelectedHand] = useState('minute'); // 'hour' or 'minute'
  const canvasRef = useRef(null);
  const [isDraggingHour, setIsDraggingHour] = useState(false);
  const [isDraggingMinute, setIsDraggingMinute] = useState(false);
  const hasInteractedRef = useRef(false);
  const firstRenderRef = useRef(true);

  useEffect(() => {
    firstRenderRef.current = false;
  }, []);

  useEffect(() => {
    if (onAnswer && !isReadOnly && hasInteractedRef.current) {
      const hourStr = String(hours).padStart(2, '0');
      const minStr = String(minutes).padStart(2, '0');
      onAnswer(`${hourStr}:${minStr}`);
    }
  }, [hours, minutes]);

  useEffect(() => {
    drawClock();
  }, [hours, minutes, disabled, selectedHand]);

  const drawClock = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 10;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw clock face with proper colors
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.fillStyle = '#1a1f2e'; // Dark background
    ctx.fill();
    ctx.strokeStyle = '#3d4663'; // Border
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw hour marks
    ctx.fillStyle = '#e8eaed'; // Light text
    ctx.font = '16px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let i = 1; i <= 12; i++) {
      const angle = (i - 3) * (Math.PI / 6);
      const x = centerX + Math.cos(angle) * (radius - 25);
      const y = centerY + Math.sin(angle) * (radius - 25);
      ctx.fillText(i.toString(), x, y);
    }

    // Draw minute hand (longer, thinner, purple)
    // Highlight if selected
    const minuteAngle = (minutes - 15) * (Math.PI / 30);
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(
      centerX + Math.cos(minuteAngle) * (radius - 35),
      centerY + Math.sin(minuteAngle) * (radius - 35)
    );
    if (disabled) {
      ctx.strokeStyle = '#8891a8';
    } else if (selectedHand === 'minute') {
      ctx.strokeStyle = '#8b5cf6'; // Purple - active
      ctx.lineWidth = 5; // Thicker when selected
    } else {
      ctx.strokeStyle = '#6b46c1'; // Darker purple - inactive
      ctx.lineWidth = 3;
    }
    ctx.stroke();

    // Draw hour hand (shorter, thicker, cyan)
    // Highlight if selected
    const hourAngle = ((hours % 12) - 3) * (Math.PI / 6) + (minutes / 60) * (Math.PI / 6);
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(
      centerX + Math.cos(hourAngle) * (radius - 55),
      centerY + Math.sin(hourAngle) * (radius - 55)
    );
    if (disabled) {
      ctx.strokeStyle = '#8891a8';
    } else if (selectedHand === 'hour') {
      ctx.strokeStyle = '#06b6d4'; // Cyan - active
      ctx.lineWidth = 7; // Thicker when selected
    } else {
      ctx.strokeStyle = '#0891b2'; // Darker cyan - inactive
      ctx.lineWidth = 5;
    }
    ctx.stroke();

    // Center dot
    ctx.beginPath();
    ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
    ctx.fillStyle = '#e8eaed';
    ctx.fill();
  };

  const handleCanvasClick = (e) => {
    if (disabled) return;
    hasInteractedRef.current = true;
    firstRenderRef.current = false;
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left - canvas.width / 2;
    const y = e.clientY - rect.top - canvas.height / 2;
    const angle = Math.atan2(y, x);
    const degrees = (angle * 180 / Math.PI + 90 + 360) % 360;

    // Use the selected hand mode
    if (selectedHand === 'minute') {
      // Adjust minutes
      const newMinutes = Math.round(degrees / 6) % 60;
      setMinutes(newMinutes);
    } else {
      // Adjust hours - clock face only shows 12 hours
      const newHours12 = Math.round(degrees / 30) % 12;
      const displayHour = newHours12 === 0 ? 12 : newHours12;
      
      // For 24-hour mode, preserve AM/PM by keeping in same half of day
      if (use_24_hour) {
        const isAfternoon = hours >= 12;
        const newHours24 = isAfternoon ? (displayHour === 12 ? 12 : displayHour + 12) : (displayHour === 12 ? 0 : displayHour);
        setHours(newHours24);
      } else {
        setHours(displayHour);
      }
    }
  };

  const adjustTime = (hourDelta, minuteDelta) => {
    hasInteractedRef.current = true;
    let newMinutes = minutes + minuteDelta;
    let newHours = hours + hourDelta;

    if (newMinutes >= 60) {
      newMinutes -= 60;
      newHours++;
    } else if (newMinutes < 0) {
      newMinutes += 60;
      newHours--;
    }

    if (use_24_hour) {
      // 24-hour mode: 0-23
      if (newHours > 23) newHours = 0;
      if (newHours < 0) newHours = 23;
    } else {
      // 12-hour mode: 1-12
      if (newHours > 12) newHours = 1;
      if (newHours < 1) newHours = 12;
    }

    setHours(newHours);
    setMinutes(newMinutes);
  };

  return (
    <div className="clock-set-container" style={{ padding: '20px', textAlign: 'center' }}>
      {/* Hand selector - choose which hand to move */}
      {!disabled && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          gap: '12px', 
          marginBottom: '16px'
        }}>
          <button
            onClick={() => setSelectedHand('hour')}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              border: selectedHand === 'hour' ? '2px solid #06b6d4' : '2px solid transparent',
              background: selectedHand === 'hour' ? 'rgba(6, 182, 212, 0.2)' : 'rgba(255,255,255,0.05)',
              color: selectedHand === 'hour' ? '#06b6d4' : '#8891a8',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            🕐 Hour Hand
          </button>
          <button
            onClick={() => setSelectedHand('minute')}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              border: selectedHand === 'minute' ? '2px solid #8b5cf6' : '2px solid transparent',
              background: selectedHand === 'minute' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.05)',
              color: selectedHand === 'minute' ? '#8b5cf6' : '#8891a8',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            🕐 Minute Hand
          </button>
        </div>
      )}

      {/* Legend - shows which hand is which */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        gap: '24px', 
        marginBottom: '16px',
        fontSize: '12px',
        fontWeight: 500,
        opacity: 0.7
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ 
            width: '40px', 
            height: '4px', 
            background: '#06b6d4',
            borderRadius: '2px'
          }} />
          <span style={{ color: '#06b6d4' }}>Hour (short)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ 
            width: '50px', 
            height: '3px', 
            background: '#8b5cf6',
            borderRadius: '2px'
          }} />
          <span style={{ color: '#8b5cf6' }}>Minute (long)</span>
        </div>
      </div>

      {/* Canvas clock */}
      <canvas
        ref={canvasRef}
        width={300}
        height={300}
        onClick={handleCanvasClick}
        style={{
          display: 'block',
          margin: '0 auto',
          cursor: disabled ? 'not-allowed' : 'pointer',
          borderRadius: '50%',
          boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
        }}
      />

      {/* Digital readout */}
      <div
        style={{
          marginTop: '20px',
          fontSize: '32px',
          fontWeight: 700,
          color: 'hsl(var(--text))',
          fontFamily: 'monospace',
        }}
      >
        {hours.toString().padStart(2, '0')}:{minutes.toString().padStart(2, '0')}
        {use_24_hour && (
          <span style={{ fontSize: '16px', marginLeft: '8px', opacity: 0.6 }}>
            (24h)
          </span>
        )}
        {!use_24_hour && (
          <span style={{ fontSize: '16px', marginLeft: '8px', opacity: 0.6 }}>
            {hours >= 12 ? 'PM' : 'AM'}
          </span>
        )}
      </div>

      {/* Button controls - 1 minute increments */}
      {!disabled && (
        <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'center', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#06b6d4' }}>HOURS</span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn-secondary"
                onClick={() => adjustTime(-1, 0)}
                style={{ padding: '8px 12px', minWidth: '40px' }}
                title="Decrease hours"
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                className="btn-secondary"
                onClick={() => adjustTime(1, 0)}
                style={{ padding: '8px 12px', minWidth: '40px' }}
                title="Increase hours"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: '#8b5cf6' }}>MINUTES</span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn-secondary"
                onClick={() => adjustTime(0, -1)}
                style={{ padding: '8px 12px', minWidth: '40px' }}
                title="Decrease 1 minute"
              >
                <Minus className="w-4 h-4" />
              </button>
              <button
                className="btn-secondary"
                onClick={() => adjustTime(0, 1)}
                style={{ padding: '8px 12px', minWidth: '40px' }}
                title="Increase 1 minute"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Hint */}
      {!disabled && (
        <div
          style={{
            marginTop: '12px',
            fontSize: '12px',
            color: 'hsl(var(--text-muted))',
            opacity: 0.7,
          }}
        >
          Choose a hand above, then click the clock to set time • Use +/- for precision
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  PESO MONEY PICKER
// ============================================================================
export function PesoMoneyPicker({ params, onAnswer, disabled }) {
  const isInteractive = params.is_interactive !== false;
  const target_amount = params.target_amount !== undefined ? params.target_amount : params.total;
  const { available_denominations, max_coins } = params;
  
  const [selectedBills, setSelectedBills] = useState({});
  const [selectedCoins, setSelectedCoins] = useState({});
  const hasInteractedRef = useRef(false);

  const denominations = available_denominations || [1000, 500, 200, 100, 50, 20, 10, 5, 1];
  const bills = denominations.filter(d => d >= 20);
  const coins = denominations.filter(d => d < 20);

  const currentTotal = () => {
    let total = 0;
    for (const [denom, count] of Object.entries(selectedBills)) {
      total += parseInt(denom) * count;
    }
    for (const [denom, count] of Object.entries(selectedCoins)) {
      total += parseInt(denom) * count;
    }
    return total;
  };

  useEffect(() => {
    if (isInteractive && onAnswer && hasInteractedRef.current) {
      onAnswer(currentTotal());
    }
  }, [selectedBills, selectedCoins, isInteractive]);

  const addDenomination = (denom, isBill) => {
    if (disabled) return;
    hasInteractedRef.current = true;
    if (isBill) {
      setSelectedBills(prev => ({ ...prev, [denom]: (prev[denom] || 0) + 1 }));
    } else {
      setSelectedCoins(prev => ({ ...prev, [denom]: (prev[denom] || 0) + 1 }));
    }
  };

  const removeDenomination = (denom, isBill) => {
    if (disabled) return;
    hasInteractedRef.current = true;
    if (isBill) {
      setSelectedBills(prev => {
        const count = prev[denom] || 0;
        if (count <= 1) {
          const { [denom]: _, ...rest } = prev;
          return rest;
        }
        return { ...prev, [denom]: count - 1 };
      });
    } else {
      setSelectedCoins(prev => {
        const count = prev[denom] || 0;
        if (count <= 1) {
          const { [denom]: _, ...rest } = prev;
          return rest;
        }
        return { ...prev, [denom]: count - 1 };
      });
    }
  };

  const resetSelection = () => {
    if (disabled) return;
    hasInteractedRef.current = true;
    setSelectedBills({});
    setSelectedCoins({});
  };

  if (!isInteractive) {
    const renderCoins = params.coins || [];
    const renderBills = params.bills || [];

    const flatBills = [];
    renderBills.forEach(b => {
      for (let i = 0; i < b.count; i++) {
        flatBills.push(b.denomination);
      }
    });

    const flatCoins = [];
    renderCoins.forEach(c => {
      for (let i = 0; i < c.count; i++) {
        flatCoins.push(c.denomination);
      }
    });

    const getBillGradient = (denom) => {
      switch (denom) {
        case 1000: return 'linear-gradient(135deg, #7dd3fc, #0284c7)';
        case 500:  return 'linear-gradient(135deg, #fef08a, #ca8a04)';
        case 200:  return 'linear-gradient(135deg, #86efac, #16a34a)';
        case 100:  return 'linear-gradient(135deg, #c084fc, #7c3aed)';
        case 50:   return 'linear-gradient(135deg, #fda4af, #dc2626)';
        case 20:   return 'linear-gradient(135deg, #ffedd5, #ea580c)';
        default:   return 'linear-gradient(135deg, #cbd5e1, #64748b)';
      }
    };

    const getCoinStyle = (denom) => {
      switch (denom) {
        case 10: return {
          background: 'radial-gradient(circle, #fef08a 60%, #cbd5e1 60%)',
          color: '#1e293b',
          border: '3px double #94a3b8',
          width: '56px',
          height: '56px',
          borderRadius: '50%'
        };
        case 5: return {
          background: 'linear-gradient(135deg, #e2e8f0, #cbd5e1)',
          color: '#1e293b',
          border: '2px solid #94a3b8',
          width: '50px',
          height: '50px',
          borderRadius: '50%'
        };
        case 1: return {
          background: 'linear-gradient(135deg, #cbd5e1, #94a3b8)',
          color: '#1e293b',
          border: '2px solid #64748b',
          width: '44px',
          height: '44px',
          borderRadius: '50%'
        };
        default: return {
          background: 'linear-gradient(135deg, #fed7aa, #c2410c)',
          color: '#fff',
          border: '2px solid #9a3412',
          width: '38px',
          height: '38px',
          borderRadius: '50%'
        };
      }
    };

    return (
      <div className="peso-money-display" style={{ padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '24px', width: '100%' }}>
        {flatBills.length > 0 && (
          <div style={{ width: '100%' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'hsl(var(--text-muted))', marginBottom: '12px', textAlign: 'center', letterSpacing: '0.05em' }}>BILLS</h4>
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {flatBills.map((denom, idx) => (
                <div
                  key={`bill-${denom}-${idx}`}
                  style={{
                    width: '140px',
                    height: '70px',
                    background: getBillGradient(denom),
                    borderRadius: '6px',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    padding: '8px',
                    color: '#fff',
                    fontWeight: 800,
                    fontSize: '14px',
                    border: '1px solid rgba(255,255,255,0.15)',
                    position: 'relative',
                    userSelect: 'none'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', fontSize: '11px' }}>
                    <span>₱{denom}</span>
                    <span>₱{denom}</span>
                  </div>
                  <div style={{ textAlign: 'center', fontSize: '18px', letterSpacing: '0.02em', textShadow: '0 1px 2px rgba(0,0,0,0.2)' }}>
                    ₱{denom}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', fontSize: '9px', opacity: 0.8 }}>
                    REPUBLIKA NG PILIPINAS
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {flatCoins.length > 0 && (
          <div style={{ width: '100%' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'hsl(var(--text-muted))', marginBottom: '12px', textAlign: 'center', letterSpacing: '0.05em' }}>COINS</h4>
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
              {flatCoins.map((denom, idx) => {
                const style = getCoinStyle(denom);
                return (
                  <div
                    key={`coin-${denom}-${idx}`}
                    style={{
                      ...style,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 800,
                      fontSize: denom === 10 ? '13px' : '12px',
                      boxShadow: '0 3px 5px rgba(0,0,0,0.15)',
                      userSelect: 'none'
                    }}
                  >
                    ₱{denom}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  const total = currentTotal();
  const isCorrectAmount = total === target_amount;

  return (
    <div className="peso-money-picker" style={{ padding: '20px' }}>
      {/* Target display */}
      <div
        style={{
          textAlign: 'center',
          fontSize: '18px',
          fontWeight: 600,
          color: 'hsl(var(--text))',
          marginBottom: '30px',
        }}
      >
        Make exactly: <span style={{ color: 'hsl(var(--primary))', fontSize: '24px' }}>₱{target_amount}</span>
      </div>

      {/* Bills */}
      <div style={{ marginBottom: '30px' }}>
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text-muted))', marginBottom: '12px' }}>BILLS</h4>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {bills.map(denom => (
            <button
              key={denom}
              className="btn-secondary"
              onClick={() => addDenomination(denom, true)}
              disabled={disabled}
              style={{
                padding: '12px 20px',
                fontSize: '16px',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #10b981, #059669)',
                color: '#fff',
                border: 'none',
              }}
            >
              ₱{denom}
            </button>
          ))}
        </div>
      </div>

      {/* Coins */}
      <div style={{ marginBottom: '30px' }}>
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text-muted))', marginBottom: '12px' }}>COINS</h4>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {coins.map(denom => (
            <button
              key={denom}
              className="btn-secondary"
              onClick={() => addDenomination(denom, false)}
              disabled={disabled}
              style={{
                padding: '10px 16px',
                fontSize: '14px',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #f59e0b, #d97706)',
                color: '#fff',
                border: 'none',
                borderRadius: '50%',
                width: '60px',
                height: '60px',
              }}
            >
              ₱{denom}
            </button>
          ))}
        </div>
      </div>

      {/* Selected items */}
      {(Object.keys(selectedBills).length > 0 || Object.keys(selectedCoins).length > 0) && (
        <div style={{ marginTop: '20px', padding: '16px', background: 'hsl(var(--card-bg))', borderRadius: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text))' }}>SELECTED</h4>
            {!disabled && (
              <button
                className="btn-secondary"
                onClick={resetSelection}
                style={{ padding: '4px 12px', fontSize: '12px' }}
              >
                <RotateCcw className="w-3 h-3" />
                Reset
              </button>
            )}
          </div>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {Object.entries({ ...selectedBills, ...selectedCoins }).map(([denom, count]) => (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 12px',
                  background: 'hsl(var(--border-color))',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: 600,
                }}
                key={denom}
              >
                <span>₱{denom} × {count}</span>
                {!disabled && (
                  <button
                    onClick={() => removeDenomination(denom, parseInt(denom) >= 20)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'hsl(var(--error))',
                      cursor: 'pointer',
                      padding: '0 4px',
                      fontSize: '16px',
                    }}
                  >
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  ESTIMATION GATE INTERACTIVE - SKIPPED
//  Reason: Estimation problems don't fit well into interactive visual format.
//  They are better suited for traditional numeric input with tolerance checking.
//  Keeping code commented for reference if needed in future.
// ============================================================================
/*
export function EstimationGateInteractive({ params, onAnswer, disabled }) {
  const { operation, exact_value, tolerance, lower_bound, upper_bound } = params;
  const [estimate, setEstimate] = useState('');

  useEffect(() => {
    if (onAnswer && estimate !== '') {
      const numValue = parseInt(estimate);
      if (!isNaN(numValue)) {
        onAnswer(numValue);
      }
    }
  }, [estimate, onAnswer]);

  const handleInputChange = (e) => {
    if (disabled) return;
    const value = e.target.value;
    // Allow only numbers
    if (value === '' || /^\d+$/.test(value)) {
      setEstimate(value);
    }
  };

  const estimateNum = estimate === '' ? null : parseInt(estimate);
  const isInRange = estimateNum !== null && estimateNum >= lower_bound && estimateNum <= upper_bound;

  return (
    <div style={{ padding: '20px' }}>
      <div style={{
        background: 'rgba(99, 102, 241, 0.1)',
        border: '2px solid rgba(99, 102, 241, 0.3)',
        borderRadius: '12px',
        padding: '32px',
        marginBottom: '24px',
        textAlign: 'center'
      }}>
        <div style={{
          fontSize: '48px',
          fontWeight: 700,
          color: 'hsl(var(--primary))',
          fontFamily: 'monospace',
          letterSpacing: '2px'
        }}>
          {operation}
        </div>
        <div style={{
          marginTop: '12px',
          fontSize: '14px',
          color: 'hsl(var(--text-muted))',
          fontWeight: 500
        }}>
          Estimate the answer (no calculator!)
        </div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <label style={{
          display: 'block',
          marginBottom: '12px',
          fontSize: '16px',
          fontWeight: 600,
          color: 'hsl(var(--text))'
        }}>
          Your Estimate:
        </label>
        <input
          type="text"
          inputMode="numeric"
          value={estimate}
          onChange={handleInputChange}
          disabled={disabled}
          placeholder="Enter your estimate..."
          style={{
            width: '100%',
            maxWidth: '300px',
            padding: '16px 20px',
            fontSize: '32px',
            fontWeight: 700,
            textAlign: 'center',
            border: `2px solid ${isInRange ? 'hsl(var(--success))' : 'hsl(var(--border-color))'}`,
            borderRadius: '12px',
            background: 'hsl(var(--input-bg))',
            color: 'hsl(var(--text))',
            transition: 'all 0.2s ease',
            fontFamily: 'monospace'
          }}
        />
        {estimateNum !== null && (
          <div style={{
            marginTop: '12px',
            fontSize: '13px',
            color: isInRange ? 'hsl(var(--success))' : 'hsl(var(--text-muted))'
          }}>
            {isInRange ? '✓ Within acceptable range' : 'Enter a number to estimate'}
          </div>
        )}
      </div>

      {!disabled && (
        <div style={{
          marginTop: '24px',
          padding: '16px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          fontSize: '13px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          💡 Tip: Round the numbers to make the math easier!
        </div>
      )}
    </div>
  );
}
*/

// ============================================================================
//  FILL-IN-TABLE INTERACTIVE
// ============================================================================
export function FillInTableInteractive({ params, onAnswer, disabled }) {
  const { columns, rows, rule_description } = params;
  const [inputs, setInputs] = useState({});
  const hasInteractedRef = useRef(false);

  // Find blank indices
  const blankIndices = rows
    .map((row, idx) => row[1] === null ? idx : null)
    .filter(idx => idx !== null);

  useEffect(() => {
    if (onAnswer && hasInteractedRef.current) {
      // Collect answers in order
      const answers = blankIndices.map(idx => {
        const val = inputs[idx];
        return val === '' || val === undefined ? null : parseInt(val);
      });
      onAnswer(answers);
    }
  }, [inputs]);

  const handleInputChange = (rowIdx, value) => {
    if (disabled) return;
    // Allow only numbers and minus sign
    if (value === '' || value === '-' || /^-?\d+$/.test(value)) {
      hasInteractedRef.current = true;
      setInputs(prev => ({ ...prev, [rowIdx]: value }));
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      {/* Rule hint */}
      {rule_description && (
        <div style={{
          marginBottom: '20px',
          padding: '12px',
          background: 'rgba(99, 102, 241, 0.1)',
          borderRadius: '8px',
          borderLeft: '3px solid hsl(var(--primary))',
          fontSize: '14px',
          color: 'hsl(var(--text))'
        }}>
          <strong>Rule:</strong> {rule_description}
        </div>
      )}

      {/* Table */}
      <table style={{
        width: '100%',
        maxWidth: '400px',
        margin: '0 auto',
        borderCollapse: 'collapse',
        fontSize: '16px'
      }}>
        <thead>
          <tr>
            {columns.map((col, idx) => (
              <th key={idx} style={{
                padding: '12px 16px',
                background: 'hsl(var(--card-bg))',
                border: '1px solid hsl(var(--border-color))',
                fontWeight: 700,
                color: 'hsl(var(--text))'
              }}>
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr key={rowIdx}>
              <td style={{
                padding: '12px 16px',
                border: '1px solid hsl(var(--border-color))',
                textAlign: 'center',
                fontWeight: 600,
                color: 'hsl(var(--primary))'
              }}>
                {row[0]}
              </td>
              <td style={{
                padding: '8px',
                border: '1px solid hsl(var(--border-color))',
                textAlign: 'center'
              }}>
                {row[1] !== null ? (
                  <span style={{ fontWeight: 600, color: 'hsl(var(--text))' }}>{row[1]}</span>
                ) : (
                  <input
                    type="text"
                    inputMode="numeric"
                    value={inputs[rowIdx] || ''}
                    onChange={(e) => handleInputChange(rowIdx, e.target.value)}
                    disabled={disabled}
                    placeholder="?"
                    style={{
                      width: '80px',
                      padding: '8px 12px',
                      fontSize: '16px',
                      fontWeight: 600,
                      textAlign: 'center',
                      border: '2px solid hsl(var(--primary))',
                      borderRadius: '6px',
                      background: disabled ? 'hsl(var(--card-bg))' : 'hsl(var(--input-bg))',
                      color: 'hsl(var(--text))'
                    }}
                  />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {!disabled && (
        <div style={{
          marginTop: '16px',
          fontSize: '12px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          Fill in the missing values in the table
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  RULE DISCOVERY INTERACTIVE
// ============================================================================
export function RuleDiscoveryInteractive({ params, onAnswer, disabled }) {
  const { table, variable_name } = params;
  const [expression, setExpression] = useState('');

  useEffect(() => {
    if (onAnswer) {
      onAnswer(expression);
    }
  }, [expression]);

  return (
    <div style={{ padding: '20px' }}>
      {/* Data table */}
      <table style={{
        width: '100%',
        maxWidth: '300px',
        margin: '0 auto 24px',
        borderCollapse: 'collapse',
        fontSize: '16px'
      }}>
        <thead>
          <tr>
            <th style={{
              padding: '12px 20px',
              background: 'hsl(var(--card-bg))',
              border: '1px solid hsl(var(--border-color))',
              fontWeight: 700,
              color: 'hsl(var(--primary))'
            }}>
              {variable_name || 'n'}
            </th>
            <th style={{
              padding: '12px 20px',
              background: 'hsl(var(--card-bg))',
              border: '1px solid hsl(var(--border-color))',
              fontWeight: 700,
              color: 'hsl(var(--secondary))'
            }}>
              output
            </th>
          </tr>
        </thead>
        <tbody>
          {table.map(([n, output], idx) => (
            <tr key={idx}>
              <td style={{
                padding: '12px 20px',
                border: '1px solid hsl(var(--border-color))',
                textAlign: 'center',
                fontWeight: 600,
                color: 'hsl(var(--primary))'
              }}>
                {n}
              </td>
              <td style={{
                padding: '12px 20px',
                border: '1px solid hsl(var(--border-color))',
                textAlign: 'center',
                fontWeight: 600,
                color: 'hsl(var(--secondary))'
              }}>
                {output}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* Expression input */}
      <div style={{ textAlign: 'center' }}>
        <label style={{
          display: 'block',
          marginBottom: '12px',
          fontSize: '16px',
          fontWeight: 600,
          color: 'hsl(var(--text))'
        }}>
          Write the rule in terms of <strong style={{ color: 'hsl(var(--primary))' }}>{variable_name || 'n'}</strong>:
        </label>
        <input
          type="text"
          value={expression}
          onChange={(e) => !disabled && setExpression(e.target.value)}
          disabled={disabled}
          placeholder={`e.g., 2*${variable_name || 'n'}+3`}
          style={{
            width: '100%',
            maxWidth: '300px',
            padding: '16px 20px',
            fontSize: '20px',
            fontWeight: 600,
            textAlign: 'center',
            border: '2px solid hsl(var(--border-color))',
            borderRadius: '12px',
            background: 'hsl(var(--input-bg))',
            color: 'hsl(var(--text))',
            fontFamily: 'monospace'
          }}
        />
      </div>

      {!disabled && (
        <div style={{
          marginTop: '16px',
          padding: '12px',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          fontSize: '13px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          💡 Use <code>*</code> for multiplication (e.g., <code>3*n</code>) and <code>**</code> for powers (e.g., <code>n**2</code>)
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  CONSTRAINT SATISFACTION INTERACTIVE
// ============================================================================
export function ConstraintSatisfactionInteractive({ params, onAnswer, disabled }) {
  const { constraint_descriptions, valid_answers } = params;
  const [answer, setAnswer] = useState('');

  useEffect(() => {
    if (onAnswer && answer !== '') {
      const numValue = parseInt(answer);
      if (!isNaN(numValue)) {
        onAnswer(numValue);
      }
    }
  }, [answer]);

  const handleInputChange = (value) => {
    if (disabled) return;
    if (value === '' || value === '-' || /^-?\d+$/.test(value)) {
      setAnswer(value);
    }
  };

  const numAnswer = answer === '' || answer === '-' ? null : parseInt(answer);
  const isValid = numAnswer !== null && valid_answers.includes(numAnswer);

  return (
    <div style={{ padding: '20px' }}>
      {/* Constraints display */}
      <div style={{
        marginBottom: '24px',
        padding: '20px',
        background: 'rgba(99, 102, 241, 0.1)',
        borderRadius: '12px',
        border: '2px solid rgba(99, 102, 241, 0.3)'
      }}>
        <div style={{
          fontSize: '14px',
          fontWeight: 600,
          color: 'hsl(var(--text-muted))',
          marginBottom: '12px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          Find a number that is:
        </div>
        <ul style={{
          margin: 0,
          padding: '0 0 0 20px',
          listStyle: 'none'
        }}>
          {constraint_descriptions.map((desc, idx) => (
            <li key={idx} style={{
              padding: '8px 0',
              fontSize: '18px',
              fontWeight: 600,
              color: 'hsl(var(--text))',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <span style={{
                color: 'hsl(var(--primary))',
                fontSize: '16px'
              }}>✓</span>
              {desc}
            </li>
          ))}
        </ul>
      </div>

      {/* Answer input */}
      <div style={{ textAlign: 'center' }}>
        <input
          type="text"
          inputMode="numeric"
          value={answer}
          onChange={(e) => handleInputChange(e.target.value)}
          disabled={disabled}
          placeholder="Enter a valid number..."
          style={{
            width: '100%',
            maxWidth: '250px',
            padding: '20px',
            fontSize: '32px',
            fontWeight: 700,
            textAlign: 'center',
            border: `3px solid ${isValid ? 'hsl(var(--success))' : 'hsl(var(--border-color))'}`,
            borderRadius: '16px',
            background: isValid ? 'rgba(16, 185, 129, 0.1)' : 'hsl(var(--input-bg))',
            color: 'hsl(var(--text))',
            fontFamily: 'monospace',
            transition: 'all 0.2s ease'
          }}
        />
        {numAnswer !== null && (
          <div style={{
            marginTop: '12px',
            fontSize: '14px',
            fontWeight: 600,
            color: isValid ? 'hsl(var(--success))' : 'hsl(var(--error))'
          }}>
            {isValid ? '✓ Satisfies all constraints!' : '✗ Does not satisfy all constraints'}
          </div>
        )}
      </div>

      {!disabled && (
        <div style={{
          marginTop: '20px',
          fontSize: '12px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          Multiple answers may be correct
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  BAR CHART INTERACTIVE
// ============================================================================
export function BarChartInteractive({ params, onAnswer, disabled }) {
  const { 
    labels, 
    categories,
    values, 
    counts,
    values2: targetValues2,  // For double bar charts
    series_labels,
    title, 
    max_y,
    scale = 1,
    is_pictograph = false,
    has_scale = true,
    is_read_mode = false,  // READ mode: chart pre-filled, student enters values
    ask_category = null,   // For read mode: specific category to ask about
    ask_series = null,     // For read mode: which series to ask about
    orientation = 'vertical'
  } = params;

  const actualLabels = labels || categories || [];
  const targetValues = values || counts || [];
  
  // CREATE mode: student builds chart from 0
  // READ mode: chart is pre-filled, student enters what they read
  const [barValues, setBarValues] = useState(() => 
    is_read_mode ? [...targetValues] : actualLabels.map(() => 0)
  );
  const [barValues2, setBarValues2] = useState(() => 
    targetValues2 ? (is_read_mode ? [...targetValues2] : actualLabels.map(() => 0)) : null
  );
  
  // For read mode: student's answers
  const [readAnswers, setReadAnswers] = useState(() => 
    is_read_mode 
      ? (ask_category 
          ? '' // Single value answer
          : actualLabels.map(() => '')) // Array of answers
      : null
  );

  useEffect(() => {
    if (onAnswer) {
      if (is_read_mode) {
        // Read mode: send the student's read answers
        if (ask_category) {
          // Single value question
          const numVal = parseInt(readAnswers, 10);
          onAnswer(isNaN(numVal) ? null : numVal);
        } else {
          // All values question
          const numVals = readAnswers.map(v => {
            const n = parseInt(v, 10);
            return isNaN(n) ? null : n;
          });
          onAnswer(numVals);
        }
      } else {
        // Create mode: send bar values
        if (barValues2) {
          onAnswer([barValues, barValues2]);
        } else {
          onAnswer(barValues);
        }
      }
    }
  }, [barValues, barValues2, readAnswers]);

  const handleBarChange = (idx, delta, isSecondSeries = false) => {
    if (disabled || is_read_mode) return;
    const setter = isSecondSeries ? setBarValues2 : setBarValues;
    setter(prev => {
      const newVals = [...prev];
      // Snap to scale increments
      const newVal = newVals[idx] + delta * scale;
      newVals[idx] = Math.max(0, Math.min(max_y, newVal));
      return newVals;
    });
  };

  const updateBarValue = (idx, clientX, clientY, rect, isSecondSeries) => {
    let rawValue;
    if (orientation === 'horizontal') {
      const x = clientX - rect.left;
      const width = rect.width;
      rawValue = (x / width) * max_y;
    } else {
      const y = clientY - rect.top;
      const height = rect.height;
      rawValue = (1 - y / height) * max_y;
    }
    const snappedValue = Math.round(rawValue / scale) * scale;
    const setter = isSecondSeries ? setBarValues2 : setBarValues;
    setter(prev => {
      const newVals = [...prev];
      newVals[idx] = Math.max(0, Math.min(max_y, snappedValue));
      return newVals;
    });
  };

  const handlePointerDown = (idx, e, isSecondSeries = false) => {
    if (disabled || is_read_mode) return;
    const element = e.currentTarget;
    element.setPointerCapture(e.pointerId);
    
    // Store rect on the element dataset so move events can use it without recalculating
    const rect = element.getBoundingClientRect();
    element.dataset.rectLeft = rect.left;
    element.dataset.rectWidth = rect.width;
    element.dataset.rectTop = rect.top;
    element.dataset.rectHeight = rect.height;
    
    updateBarValue(idx, e.clientX, e.clientY, rect, isSecondSeries);
  };

  const handlePointerMove = (idx, e, isSecondSeries = false) => {
    if (disabled || is_read_mode) return;
    const element = e.currentTarget;
    if (element.hasPointerCapture(e.pointerId)) {
      const rect = {
        left: parseFloat(element.dataset.rectLeft),
        width: parseFloat(element.dataset.rectWidth),
        top: parseFloat(element.dataset.rectTop),
        height: parseFloat(element.dataset.rectHeight)
      };
      updateBarValue(idx, e.clientX, e.clientY, rect, isSecondSeries);
    }
  };

  const handlePointerUp = (idx, e) => {
    if (disabled || is_read_mode) return;
    const element = e.currentTarget;
    if (element.hasPointerCapture(e.pointerId)) {
      element.releasePointerCapture(e.pointerId);
    }
  };
  
  const handleReadAnswerChange = (idx, value) => {
    if (disabled) return;
    if (ask_category) {
      // Single answer
      setReadAnswers(value);
    } else {
      // Array of answers
      setReadAnswers(prev => {
        const newAnswers = [...prev];
        newAnswers[idx] = value;
        return newAnswers;
      });
    }
  };

  const chartHeight = 220;
  const barWidth = targetValues2 ? 24 : 44;  // Narrower for double bars
  const barGap = targetValues2 ? 8 : 16;
  const groupGap = 24;
  
  // Calculate grid lines based on scale
  const numGridLines = Math.floor(max_y / scale) + 1;
  const gridLines = Array.from({ length: numGridLines }, (_, i) => i * scale);


  // For read mode with specific category, find the index
  const askIdx = ask_category ? actualLabels.indexOf(ask_category) : -1;
  const isSecondSeriesActive = !!(targetValues2 && ask_series && series_labels && ask_series === series_labels[1]);
  const guideVal = askIdx !== -1 
    ? (barValues2 && isSecondSeriesActive ? barValues2[askIdx] : barValues[askIdx])
    : null;
  const activeColor = isSecondSeriesActive ? 'hsl(var(--secondary))' : 'hsl(var(--primary))';
  const activeColorLight = isSecondSeriesActive ? 'hsl(var(--secondary) / 0.12)' : 'hsl(var(--primary) / 0.12)';
  const activeColorBorder = isSecondSeriesActive ? 'hsl(var(--secondary) / 0.3)' : 'hsl(var(--primary) / 0.3)';

  return (
    <div style={{ padding: '20px' }}>
      {/* Instructions */}
      <div style={{
        marginBottom: '16px',
        padding: '10px 14px',
        background: is_read_mode 
          ? 'rgba(34, 197, 94, 0.08)' // Green tint for read mode
          : 'rgba(99, 102, 241, 0.08)',
        borderRadius: '8px',
        textAlign: 'center',
        fontSize: '13px',
        color: 'hsl(var(--text-muted))'
      }}>
        {is_read_mode 
          ? (ask_category 
              ? `Read the value for "${ask_category}" from the graph and enter it below.`
              : 'Read each value from the graph and enter them below.')
          : (is_pictograph 
              ? (has_scale 
                  ? `Each symbol = ${scale}. Click to add/remove symbols.`
                  : 'Each symbol = 1. Click to add/remove symbols.')
              : (targetValues2 
                  ? 'Drag bars or use +/- to match both data sets'
                  : 'Drag bars or use +/- to match the data'))}
      </div>

      {/* Legend for double bar charts */}
      {targetValues2 && series_labels && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          gap: '24px',
          marginBottom: '12px',
          fontSize: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: 16, height: 16, background: 'hsl(var(--primary))', borderRadius: 3 }} />
            <span>{series_labels[0]}{ask_series === series_labels[0] ? ' ← (answer this)' : ''}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div style={{ width: 16, height: 16, background: 'hsl(var(--secondary))', borderRadius: 3 }} />
            <span>{series_labels[1]}{ask_series === series_labels[1] ? ' ← (answer this)' : ''}</span>
          </div>
        </div>
      )}

      {/* Chart area */}
      <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
        <div style={{
          position: 'relative',
          height: orientation === 'horizontal' ? 'auto' : chartHeight + 60,
          width: orientation === 'horizontal' ? chartHeight + 100 : 'auto',
          display: 'flex',
          flexDirection: orientation === 'horizontal' ? 'column' : 'row',
          alignItems: orientation === 'horizontal' ? 'flex-start' : 'flex-end',
        gap: targetValues2 ? groupGap : barGap,
        padding: orientation === 'horizontal' ? '20px 40px 30px 80px' : '20px 50px 40px',
        background: 'hsl(var(--card-bg))',
        borderRadius: '12px',
        border: '1px solid hsl(var(--border-color))'
      }}>
        {/* Grid lines */}
        {gridLines.map((value, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              ...(orientation === 'horizontal' ? {
                top: '20px',
                bottom: '30px',
                left: `${80 + (value / max_y) * chartHeight}px`,
                borderLeft: value === 0 
                  ? '2px solid hsl(var(--border-color))' 
                  : '1px solid hsla(var(--border-color), 0.35)',
              } : {
                left: '45px',
                right: '20px',
                bottom: `${40 + (value / max_y) * chartHeight}px`,
                borderTop: value === 0 
                  ? '2px solid hsl(var(--border-color))' 
                  : '1px solid hsla(var(--border-color), 0.35)',
              }),
              pointerEvents: 'none'
            }}
          />
        ))}

        {/* Grid value labels */}
        {gridLines.map((value, i) => {
          return (
            <span
              key={i}
              style={{
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                ...(orientation === 'horizontal' ? {
                  bottom: '4px',
                  left: `${80 + (value / max_y) * chartHeight}px`,
                  transform: 'translateX(-50%)',
                  justifyContent: 'center',
                } : {
                  left: '4px',
                  width: '36px',
                  justifyContent: 'flex-end',
                  bottom: `${40 + (value / max_y) * chartHeight}px`,
                  transform: 'translateY(50%)',
                }),
                fontSize: '11px',
                fontWeight: '600',
                color: 'hsl(var(--text-muted))',
                backgroundColor: 'transparent',
                border: 'none',
                borderRadius: '4px',
                paddingRight: '0',
                paddingLeft: '0',
                height: 'auto',
                boxSizing: 'border-box',
                zIndex: 12,
                transition: 'all 0.2s ease'
              }}
            >
              {value}
            </span>
          );
        })}

        {/* Bars */}
        {actualLabels.map((label, idx) => {
          // In read mode, highlight the category being asked about
          const isAskedCategory = is_read_mode && ask_category && label === ask_category;
          
          return (
          <div key={idx} style={{
            position: 'relative',
            display: 'flex',
            alignItems: orientation === 'horizontal' ? 'center' : 'flex-end'
          }}>
            {/* Bar group (single or double) */}
            <div style={{ display: 'flex', gap: barGap, flexDirection: orientation === 'horizontal' ? 'column' : 'row', alignItems: orientation === 'horizontal' ? 'flex-start' : 'flex-end' }}>
              {/* First bar */}
              <div
                style={{
                  position: 'relative',
                  ...(orientation === 'horizontal' ? {
                    width: chartHeight,
                    height: barWidth,
                  } : {
                    width: barWidth,
                    height: chartHeight,
                  }),
                  background: 'rgba(255,255,255,0.03)',
                  borderRadius: orientation === 'horizontal' ? '0 4px 4px 0' : '4px 4px 0 0',
                  cursor: (disabled || is_read_mode) ? 'default' : 'pointer',
                  outline: isAskedCategory ? '2px solid hsl(var(--primary))' : 'none',
                  outlineOffset: '2px',
                  touchAction: 'none'
                }}
                onPointerDown={(e) => !is_read_mode && handlePointerDown(idx, e, false)}
                onPointerMove={(e) => !is_read_mode && handlePointerMove(idx, e, false)}
                onPointerUp={(e) => !is_read_mode && handlePointerUp(idx, e)}
                onPointerCancel={(e) => !is_read_mode && handlePointerUp(idx, e)}
              >
                {/* Actual bar - no value label on top */}
                {is_pictograph ? (
                  <div style={{
                    position: 'absolute',
                    ...(orientation === 'horizontal' ? {
                      left: 0,
                      height: '100%',
                      width: `${(barValues[idx] / max_y) * 100}%`,
                      flexDirection: 'row',
                    } : {
                      bottom: 0,
                      width: '100%',
                      height: `${(barValues[idx] / max_y) * 100}%`,
                      flexDirection: 'column-reverse',
                    }),
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-start',
                    gap: '2px',
                    overflow: 'hidden'
                  }}>
                    {(() => {
                      const totalSymbols = Math.round(barValues[idx] / scale);
                      if (totalSymbols <= 50) {
                        return Array.from({ length: totalSymbols }).map((_, i) => (
                          <span key={i} style={{ fontSize: '24px', lineHeight: '1' }}>{params.symbol || '🍎'}</span>
                        ));
                      }
                      
                      // For > 50, do grouping to prevent DOM bloat and make it readable
                      const numThousands = Math.floor(totalSymbols / 1000);
                      const remThousands = totalSymbols % 1000;
                      const numHundreds = Math.floor(remThousands / 100);
                      const remHundreds = remThousands % 100;
                      const numTens = Math.floor(remHundreds / 10);
                      const numOnes = remHundreds % 10;
                      
                      const renderGroup = (count, label, color) => {
                        return Array.from({ length: count }).map((_, i) => (
                          <div key={`${label}-${i}`} style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
                            <span style={{ fontSize: '28px', lineHeight: '1', opacity: 0.9 }}>{params.symbol || '🍎'}</span>
                            <span style={{ position: 'absolute', fontSize: '11px', fontWeight: 900, color: 'white', background: color, borderRadius: '4px', padding: '1px 3px', zIndex: 2, boxShadow: '0 1px 2px rgba(0,0,0,0.5)' }}>{label}</span>
                          </div>
                        ));
                      };
                      
                      return (
                        <div style={{ display: 'flex', flexDirection: orientation === 'horizontal' ? 'row' : 'column-reverse', gap: '4px', alignItems: 'center' }}>
                          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '2px' }}>{renderGroup(numOnes, '1x', '#475569')}</div>
                          {numTens > 0 && <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '2px' }}>{renderGroup(numTens, '10x', '#2563eb')}</div>}
                          {numHundreds > 0 && <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '2px' }}>{renderGroup(numHundreds, '100x', '#16a34a')}</div>}
                          {numThousands > 0 && <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '2px' }}>{renderGroup(numThousands, '1k', '#dc2626')}</div>}
                        </div>
                      );
                    })()}
                  </div>
                ) : (
                  <div style={{
                    position: 'absolute',
                    ...(orientation === 'horizontal' ? {
                      left: 0,
                      height: '100%',
                      width: `${(barValues[idx] / max_y) * 100}%`,
                      background: 'linear-gradient(90deg, hsl(var(--primary)), hsl(var(--primary) / 0.7))',
                      borderRadius: '0 4px 4px 0',
                      transition: 'width 0.1s ease'
                    } : {
                      bottom: 0,
                      width: '100%',
                      height: `${(barValues[idx] / max_y) * 100}%`,
                      background: 'linear-gradient(180deg, hsl(var(--primary)), hsl(var(--primary) / 0.7))',
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.1s ease'
                    })
                  }} />
                )}
              </div>

              {/* Second bar (for double bar charts) */}
              {barValues2 && (
                <div
                  style={{
                    position: 'relative',
                    ...(orientation === 'horizontal' ? {
                      width: chartHeight,
                      height: barWidth,
                    } : {
                      width: barWidth,
                      height: chartHeight,
                    }),
                    background: 'rgba(255,255,255,0.03)',
                    borderRadius: orientation === 'horizontal' ? '0 4px 4px 0' : '4px 4px 0 0',
                    cursor: (disabled || is_read_mode) ? 'default' : 'pointer',
                    outline: (isAskedCategory && ask_series === series_labels?.[1]) ? '2px solid hsl(var(--secondary))' : 'none',
                    outlineOffset: '2px',
                    touchAction: 'none'
                  }}
                  onPointerDown={(e) => !is_read_mode && handlePointerDown(idx, e, true)}
                  onPointerMove={(e) => !is_read_mode && handlePointerMove(idx, e, true)}
                  onPointerUp={(e) => !is_read_mode && handlePointerUp(idx, e)}
                  onPointerCancel={(e) => !is_read_mode && handlePointerUp(idx, e)}
                >
                  <div style={{
                    position: 'absolute',
                    ...(orientation === 'horizontal' ? {
                      left: 0,
                      height: '100%',
                      width: `${(barValues2[idx] / max_y) * 100}%`,
                      background: 'linear-gradient(90deg, hsl(var(--secondary)), hsl(var(--secondary) / 0.7))',
                      borderRadius: '0 4px 4px 0',
                      transition: 'width 0.1s ease'
                    } : {
                      bottom: 0,
                      width: '100%',
                      height: `${(barValues2[idx] / max_y) * 100}%`,
                      background: 'linear-gradient(180deg, hsl(var(--secondary)), hsl(var(--secondary) / 0.7))',
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.1s ease'
                    })
                  }} />
                </div>
              )}
            </div>

            {/* Labels and Controls below the bar group */}
            <div style={{
              ...(orientation === 'horizontal' ? {
                position: 'absolute',
                right: '100%',
                top: '50%',
                transform: 'translateY(-50%)',
                paddingRight: '12px',
                display: 'flex',
                flexDirection: 'row-reverse',
                alignItems: 'center',
                gap: '8px',
              } : {
                position: 'absolute',
                top: '100%',
                left: '50%',
                transform: 'translateX(-50%)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px',
                marginTop: '8px'
              })
            }}>
            {/* Controls - only in CREATE mode */}
            {!disabled && !is_read_mode && (
              <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', justifyContent: 'center' }}>
                {/* First series controls */}
                <div style={{ display: 'flex', gap: '2px' }}>
                  <button
                    onClick={() => handleBarChange(idx, -1, false)}
                    style={{
                      padding: '3px 7px',
                      fontSize: '12px',
                      fontWeight: 700,
                      border: 'none',
                      borderRadius: '4px',
                      background: targetValues2 ? 'hsl(var(--primary) / 0.3)' : 'hsl(var(--border-color))',
                      color: 'hsl(var(--text))',
                      cursor: 'pointer'
                    }}
                  >−</button>
                  <button
                    onClick={() => handleBarChange(idx, 1, false)}
                    style={{
                      padding: '3px 7px',
                      fontSize: '12px',
                      fontWeight: 700,
                      border: 'none',
                      borderRadius: '4px',
                      background: targetValues2 ? 'hsl(var(--primary) / 0.3)' : 'hsl(var(--border-color))',
                      color: 'hsl(var(--text))',
                      cursor: 'pointer'
                    }}
                  >+</button>
                </div>
                {/* Second series controls */}
                {barValues2 && (
                  <div style={{ display: 'flex', gap: '2px' }}>
                    <button
                      onClick={() => handleBarChange(idx, -1, true)}
                      style={{
                        padding: '3px 7px',
                        fontSize: '12px',
                        fontWeight: 700,
                        border: 'none',
                        borderRadius: '4px',
                        background: 'hsl(var(--secondary) / 0.3)',
                        color: 'hsl(var(--text))',
                        cursor: 'pointer'
                      }}
                    >−</button>
                    <button
                      onClick={() => handleBarChange(idx, 1, true)}
                      style={{
                        padding: '3px 7px',
                        fontSize: '12px',
                        fontWeight: 700,
                        border: 'none',
                        borderRadius: '4px',
                        background: 'hsl(var(--secondary) / 0.3)',
                        color: 'hsl(var(--text))',
                        cursor: 'pointer'
                      }}
                    >+</button>
                  </div>
                )}
              </div>
            )}

            {/* Label */}
            <div style={{
              fontSize: '11px',
              fontWeight: isAskedCategory ? 700 : 600,
              color: isAskedCategory ? 'hsl(var(--primary))' : 'hsl(var(--text))',
              textAlign: 'center',
              maxWidth: targetValues2 ? barWidth * 2 + barGap + 20 : barWidth + 20,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap'
            }}>
              {label}
            </div>
            </div>
          </div>
        )})}
      </div>
      </div>

      {/* READ MODE: Input fields for answers */}
      {is_read_mode && !disabled && (
        <div style={{
          marginTop: '16px',
          padding: '12px 16px',
          background: 'hsl(var(--card-bg))',
          borderRadius: '8px',
          border: '1px solid hsl(var(--border-color))'
        }}>
          <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '10px', color: 'hsl(var(--text-muted))' }}>
            Your answer{ask_category ? '' : 's'}:
          </div>
          {ask_category ? (
            // Single value input
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '13px' }}>{ask_category}:</span>
              <input
                type="number"
                value={readAnswers}
                onChange={(e) => handleReadAnswerChange(null, e.target.value)}
                style={{
                  width: '80px',
                  padding: '6px 10px',
                  fontSize: '14px',
                  fontWeight: 600,
                  border: '2px solid hsl(var(--primary))',
                  borderRadius: '6px',
                  background: 'hsl(var(--card-bg))',
                  color: 'hsl(var(--text))',
                  textAlign: 'center'
                }}
                placeholder="?"
              />
            </div>
          ) : (
            // Multiple value inputs
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
              {actualLabels.map((label, idx) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '12px' }}>{label}:</span>
                  <input
                    type="number"
                    value={readAnswers[idx]}
                    onChange={(e) => handleReadAnswerChange(idx, e.target.value)}
                    style={{
                      width: '60px',
                      padding: '5px 8px',
                      fontSize: '13px',
                      fontWeight: 600,
                      border: '1px solid hsl(var(--border-color))',
                      borderRadius: '4px',
                      background: 'hsl(var(--card-bg))',
                      color: 'hsl(var(--text))',
                      textAlign: 'center'
                    }}
                    placeholder="?"
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* CREATE MODE: Instructions */}
      {!disabled && !is_read_mode && (
        <div style={{
          marginTop: '12px',
          fontSize: '11px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          {is_pictograph 
            ? 'Use +/- buttons to add or remove symbols'
            : 'Click on chart or use +/- buttons to adjust bar heights'}
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  SORT ORDER INTERACTIVE
// ============================================================================
export function SortOrderInteractive({ params, onAnswer, disabled }) {
  const { items: initialItems, direction } = params;
  const [items, setItems] = useState(() => [...initialItems]);
  const [draggedIdx, setDraggedIdx] = useState(null);

  useEffect(() => {
    if (onAnswer) {
      onAnswer(items);
    }
  }, [items]);

  const handleDragStart = (idx) => {
    if (disabled) return;
    setDraggedIdx(idx);
  };

  const handleDragOver = (e, idx) => {
    e.preventDefault();
    if (disabled || draggedIdx === null || draggedIdx === idx) return;
    
    const newItems = [...items];
    const draggedItem = newItems[draggedIdx];
    newItems.splice(draggedIdx, 1);
    newItems.splice(idx, 0, draggedItem);
    setItems(newItems);
    setDraggedIdx(idx);
  };

  const handleDragEnd = () => {
    setDraggedIdx(null);
  };

  const moveItem = (fromIdx, toIdx) => {
    if (disabled) return;
    if (toIdx < 0 || toIdx >= items.length) return;
    const newItems = [...items];
    const item = newItems[fromIdx];
    newItems.splice(fromIdx, 1);
    newItems.splice(toIdx, 0, item);
    setItems(newItems);
  };

  return (
    <div style={{ padding: '20px' }}>
      {/* Direction indicator - clear vertical layout */}
      <div style={{
        marginBottom: '20px',
        padding: '12px 16px',
        background: direction === 'ascending' 
          ? 'rgba(34, 197, 94, 0.1)' 
          : 'rgba(239, 68, 68, 0.1)',
        border: `1px solid ${direction === 'ascending' ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        <div style={{ 
          fontSize: '13px', 
          fontWeight: 700,
          color: direction === 'ascending' ? '#22c55e' : '#ef4444',
          marginBottom: '4px'
        }}>
          {direction === 'ascending' ? 'SMALLEST → LARGEST' : 'LARGEST → SMALLEST'}
        </div>
        <div style={{ 
          fontSize: '12px', 
          color: 'hsl(var(--text-muted))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}>
          <span style={{ opacity: 0.7 }}>Top</span>
          <span>= {direction === 'ascending' ? 'Smallest' : 'Largest'}</span>
          <span style={{ margin: '0 4px' }}>•</span>
          <span style={{ opacity: 0.7 }}>Bottom</span>
          <span>= {direction === 'ascending' ? 'Largest' : 'Smallest'}</span>
        </div>
      </div>

      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        maxWidth: '320px',
        margin: '0 auto'
      }}>
        {/* Top label */}
        <div style={{
          textAlign: 'center',
          fontSize: '11px',
          fontWeight: 600,
          color: direction === 'ascending' ? '#22c55e' : '#ef4444',
          padding: '4px 0',
          borderBottom: `1px dashed ${direction === 'ascending' ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`
        }}>
          ▲ {direction === 'ascending' ? 'SMALLEST' : 'LARGEST'}
        </div>
        
        {items.map((item, idx) => (
          <div
            key={`${item}-${idx}`}
            draggable={!disabled}
            onDragStart={() => handleDragStart(idx)}
            onDragOver={(e) => handleDragOver(e, idx)}
            onDragEnd={handleDragEnd}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '14px 16px',
              background: draggedIdx === idx ? 'rgba(99, 102, 241, 0.2)' : 'hsl(var(--card-bg))',
              border: `2px solid ${draggedIdx === idx ? 'hsl(var(--primary))' : 'hsl(var(--border-color))'}`,
              borderRadius: '10px',
              cursor: disabled ? 'not-allowed' : 'grab',
              transition: 'all 0.15s ease',
              userSelect: 'none'
            }}
          >
            {/* Position indicator (small, subtle) */}
            <div style={{
              width: '20px',
              height: '20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'hsl(var(--border-color))',
              borderRadius: '50%',
              fontSize: '10px',
              fontWeight: 600,
              color: 'hsl(var(--text-muted))',
              flexShrink: 0,
              opacity: 0.6
            }}>
              {idx + 1}
            </div>

            {/* Item value - THE ACTUAL NUMBER TO SORT */}
            <div style={{
              flex: 1,
              fontSize: '24px',
              fontWeight: 700,
              color: 'hsl(var(--text))',
              fontFamily: 'monospace',
              textAlign: 'center'
            }}>
              {item}
            </div>

            {/* Move buttons */}
            {!disabled && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <button
                  onClick={() => moveItem(idx, idx - 1)}
                  disabled={idx === 0}
                  style={{
                    padding: '4px 8px',
                    fontSize: '12px',
                    border: 'none',
                    borderRadius: '4px',
                    background: idx === 0 ? 'transparent' : 'hsl(var(--border-color))',
                    color: 'hsl(var(--text))',
                    cursor: idx === 0 ? 'default' : 'pointer',
                    opacity: idx === 0 ? 0.3 : 1
                  }}
                >▲</button>
                <button
                  onClick={() => moveItem(idx, idx + 1)}
                  disabled={idx === items.length - 1}
                  style={{
                    padding: '4px 8px',
                    fontSize: '12px',
                    border: 'none',
                    borderRadius: '4px',
                    background: idx === items.length - 1 ? 'transparent' : 'hsl(var(--border-color))',
                    color: 'hsl(var(--text))',
                    cursor: idx === items.length - 1 ? 'default' : 'pointer',
                    opacity: idx === items.length - 1 ? 0.3 : 1
                  }}
                >▼</button>
              </div>
            )}
          </div>
        ))}
        
        {/* Bottom label */}
        <div style={{
          textAlign: 'center',
          fontSize: '11px',
          fontWeight: 600,
          color: direction === 'ascending' ? '#ef4444' : '#22c55e',
          padding: '4px 0',
          borderTop: `1px dashed ${direction === 'ascending' ? 'rgba(239, 68, 68, 0.4)' : 'rgba(34, 197, 94, 0.4)'}`
        }}>
          ▼ {direction === 'ascending' ? 'LARGEST' : 'SMALLEST'}
        </div>
      </div>

      {!disabled && (
        <div style={{
          marginTop: '16px',
          fontSize: '12px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          Drag items or use arrow buttons to reorder
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  GRID AREA INTERACTIVE
// ============================================================================
export function GridAreaInteractive({ params, onAnswer, disabled }) {
  const { grid_size, correct_count, width, height, shape_type, cols, rows } = params || {};
  
  // Safely extract grid dimensions
  const gridWidth = cols || (Array.isArray(grid_size) ? grid_size[0] : 10);
  const gridHeight = rows || (Array.isArray(grid_size) ? grid_size[1] : 10);
  
  const [shaded, setShaded] = useState(() => {
    const initial = new Set();
    if (params?.shaded) {
      for (let r = 0; r < gridHeight; r++) {
        for (let c = 0; c < gridWidth; c++) {
          initial.add(`${r}-${c}`);
        }
      }
    }
    return initial;
  });
  const hasInteractedRef = useRef(false);

  useEffect(() => {
    if (onAnswer && hasInteractedRef.current) {
      onAnswer(shaded.size);
    }
  }, [shaded]);

  const toggleCell = (row, col) => {
    if (disabled) return;
    hasInteractedRef.current = true;
    const key = `${row}-${col}`;
    setShaded(prev => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const clearAll = () => {
    if (disabled) return;
    hasInteractedRef.current = true;
    setShaded(new Set());
  };

  const cellSize = Math.max(24, Math.min(36, 320 / Math.max(gridWidth, gridHeight)));

  return (
    <div style={{ padding: '20px' }}>
      {/* Instructions */}
      <div style={{
        marginBottom: '16px',
        padding: '12px 16px',
        background: 'rgba(99, 102, 241, 0.08)',
        borderRadius: '8px',
        textAlign: 'center',
        fontSize: '13px',
        color: 'hsl(var(--text-muted))'
      }}>
        {shape_type === 'rectangle' && (width || cols) && (height || rows) ? (
          <>Click squares to shade a <strong style={{ color: 'hsl(var(--primary))' }}>{width || cols} × {height || rows}</strong> rectangle</>
        ) : (
          <>Click squares to shade them. Count the area in square units.</>
        )}
      </div>

      {/* Counter */}
      <div style={{
        marginBottom: '16px',
        textAlign: 'center',
        fontSize: '28px',
        fontWeight: 700,
        color: 'hsl(var(--primary))'
      }}>
        {shaded.size} square unit{shaded.size !== 1 ? 's' : ''}
      </div>

      {/* Grid Container - centers the grid */}
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <div style={{
          display: 'inline-grid',
          gridTemplateColumns: `repeat(${gridWidth}, ${cellSize}px)`,
          gridTemplateRows: `repeat(${gridHeight}, ${cellSize}px)`,
          gap: '2px',
          background: '#4b5563',
          padding: '2px',
          borderRadius: '8px',
          boxShadow: 'inset 0 0 0 2px #374151'
        }}>
          {Array.from({ length: gridHeight * gridWidth }, (_, i) => {
            const row = Math.floor(i / gridWidth);
            const col = i % gridWidth;
            const key = `${row}-${col}`;
            const isShaded = shaded.has(key);
            return (
              <div
                key={key}
                onClick={() => toggleCell(row, col)}
                style={{
                  width: cellSize,
                  height: cellSize,
                  background: isShaded 
                    ? 'linear-gradient(135deg, hsl(var(--primary)), hsl(var(--primary) / 0.8))' 
                    : 'linear-gradient(135deg, #f8fafc, #e2e8f0)',
                  border: isShaded ? '1px solid hsl(var(--primary))' : '1px solid #cbd5e1',
                  borderRadius: '2px',
                  cursor: disabled ? 'not-allowed' : 'pointer',
                  transition: 'all 0.1s ease',
                  boxShadow: isShaded ? '0 2px 4px rgba(0,0,0,0.2)' : 'none'
                }}
                onMouseEnter={(e) => {
                  if (!disabled && !isShaded) {
                    e.currentTarget.style.background = 'linear-gradient(135deg, #dbeafe, #bfdbfe)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!disabled && !isShaded) {
                    e.currentTarget.style.background = 'linear-gradient(135deg, #f8fafc, #e2e8f0)';
                  }
                }}
              />
            );
          })}
        </div>
      </div>

      {/* Controls */}
      {!disabled && (
        <div style={{
          marginTop: '16px',
          display: 'flex',
          justifyContent: 'center',
          gap: '12px'
        }}>
          <button
            onClick={clearAll}
            style={{
              padding: '8px 16px',
              fontSize: '13px',
              fontWeight: 600,
              border: 'none',
              borderRadius: '6px',
              background: 'hsl(var(--border-color))',
              color: 'hsl(var(--text))',
              cursor: 'pointer'
            }}
          >
            <RotateCcw className="w-4 h-4" style={{ display: 'inline', marginRight: '6px' }} />
            Clear All
          </button>
        </div>
      )}

      {!disabled && (
        <div style={{
          marginTop: '12px',
          fontSize: '12px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          Click squares to shade/unshade
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  CATEGORIZE INTERACTIVE
// ============================================================================
export function CategorizeInteractive({ params, onAnswer, disabled }) {
  const { categories, items } = params;
  const [assignments, setAssignments] = useState({});

  useEffect(() => {
    if (onAnswer) {
      onAnswer(assignments);
    }
  }, [assignments]);

  const assignItem = (item, category) => {
    if (disabled) return;
    setAssignments(prev => ({ ...prev, [item]: category }));
  };

  const unassignItem = (item) => {
    if (disabled) return;
    setAssignments(prev => {
      const { [item]: _, ...rest } = prev;
      return rest;
    });
  };

  const unassignedItems = items.filter(item => !assignments[item]);
  const categoryColors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div style={{ padding: '20px' }}>
      {/* Unassigned items bank */}
      <div style={{
        marginBottom: '24px',
        padding: '16px',
        background: 'hsl(var(--card-bg))',
        borderRadius: '12px',
        border: '2px dashed hsl(var(--border-color))'
      }}>
        <div style={{
          fontSize: '12px',
          fontWeight: 600,
          color: 'hsl(var(--text-muted))',
          marginBottom: '12px',
          textTransform: 'uppercase'
        }}>
          Items to Sort ({unassignedItems.length} remaining)
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {unassignedItems.map((item, idx) => (
            <div
              key={idx}
              style={{
                padding: '10px 16px',
                background: 'rgba(255,255,255,0.05)',
                border: '2px solid hsl(var(--border-color))',
                borderRadius: '8px',
                fontSize: '16px',
                fontWeight: 600,
                color: 'hsl(var(--text))',
                cursor: disabled ? 'not-allowed' : 'default'
              }}
            >
              {String(item)}
            </div>
          ))}
          {unassignedItems.length === 0 && (
            <div style={{ color: 'hsl(var(--text-muted))', fontStyle: 'italic' }}>
              All items sorted!
            </div>
          )}
        </div>
      </div>

      {/* Category bins */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${Math.min(categories.length, 3)}, 1fr)`,
        gap: '16px'
      }}>
        {categories.map((category, catIdx) => {
          const assignedItems = items.filter(item => assignments[item] === category);
          const catColor = categoryColors[catIdx % categoryColors.length];
          
          return (
            <div key={catIdx} style={{
              padding: '16px',
              background: 'hsl(var(--card-bg))',
              borderRadius: '12px',
              border: `2px solid ${catColor}40`
            }}>
              <div style={{
                fontSize: '14px',
                fontWeight: 700,
                color: catColor,
                marginBottom: '12px',
                textAlign: 'center',
                padding: '8px',
                background: `${catColor}15`,
                borderRadius: '6px'
              }}>
                {category}
              </div>
              
              {/* Assigned items */}
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                minHeight: '60px'
              }}>
                {assignedItems.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px 12px',
                      background: `${catColor}20`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontWeight: 600,
                      color: 'hsl(var(--text))'
                    }}
                  >
                    <span>{String(item)}</span>
                    {!disabled && (
                      <button
                        onClick={() => unassignItem(item)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: 'hsl(var(--error))',
                          cursor: 'pointer',
                          fontSize: '16px',
                          padding: '0 4px'
                        }}
                      >×</button>
                    )}
                  </div>
                ))}
              </div>

              {/* Drop zone for unassigned items */}
              {!disabled && unassignedItems.length > 0 && (
                <div style={{ marginTop: '12px' }}>
                  <select
                    onChange={(e) => {
                      if (e.target.value) {
                        assignItem(e.target.value, category);
                        e.target.value = '';
                      }
                    }}
                    style={{
                      width: '100%',
                      padding: '8px',
                      borderRadius: '6px',
                      border: '1px solid hsl(var(--border-color))',
                      background: 'hsl(var(--input-bg))',
                      color: 'hsl(var(--text))',
                      fontSize: '13px'
                    }}
                  >
                    <option value="">+ Add item...</option>
                    {unassignedItems.map((item, idx) => (
                      <option key={idx} value={item}>{String(item)}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {!disabled && (
        <div style={{
          marginTop: '16px',
          fontSize: '12px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          Use the dropdowns to assign items to categories
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  CALENDAR INTERACTIVE
// ============================================================================
export function CalendarInteractive({ params, onAnswer, disabled }) {
  const { 
    task_type = 'select_date'
  } = params || {};
  const [selectedDate, setSelectedDate] = useState(null);
  const [rangeStart, setRangeStart] = useState(null);
  const [rangeEnd, setRangeEnd] = useState(null);
  const hasInteractedRef = useRef(false);
  const firstRenderRef = useRef(true);

  useEffect(() => {
    firstRenderRef.current = false;
  }, []);

  // Get calendar info
  const firstDay = new Date(params.year, params.month - 1, 1).getDay();
  const daysInMonth = new Date(params.year, params.month, 0).getDate();
  const monthName = new Date(params.year, params.month - 1).toLocaleString('default', { month: 'long' });
  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  useEffect(() => {
    if (onAnswer && !disabled && hasInteractedRef.current) {
      if (task_type === 'select_date') {
        onAnswer(selectedDate);
      } else {
        if (rangeStart && rangeEnd) {
          onAnswer(rangeEnd - rangeStart + 1);
        }
      }
    }
  }, [selectedDate, rangeStart, rangeEnd, onAnswer, task_type, disabled]);

  const handleDateClick = (day) => {
    if (disabled) return;
    hasInteractedRef.current = true;
    
    if (task_type === 'select_date') {
      setSelectedDate(day);
    } else {
      // Duration mode
      if (!rangeStart || (rangeStart && rangeEnd)) {
        setRangeStart(day);
        setRangeEnd(null);
      } else {
        if (day >= rangeStart) {
          setRangeEnd(day);
        } else {
          setRangeEnd(rangeStart);
          setRangeStart(day);
        }
      }
    }
  };

  const isInRange = (day) => {
    if (!rangeStart) return false;
    if (!rangeEnd) return day === rangeStart;
    return day >= rangeStart && day <= rangeEnd;
  };

  const computedDuration = rangeStart && rangeEnd ? rangeEnd - rangeStart + 1 : null;

  // Build calendar grid
  const cells = [];
  for (let i = 0; i < firstDay; i++) {
    cells.push(null);
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(d);
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Month/Year header */}
      <div style={{
        textAlign: 'center',
        marginBottom: '20px',
        fontSize: '20px',
        fontWeight: 700,
        color: 'hsl(var(--primary))'
      }}>
        {monthName} {params.year}
      </div>

      {/* Calendar grid */}
      <div style={{
        maxWidth: '350px',
        margin: '0 auto',
        background: 'hsl(var(--card-bg))',
        borderRadius: '12px',
        padding: '16px',
        border: '1px solid hsl(var(--border-color))'
      }}>
        {/* Weekday headers */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, 1fr)',
          gap: '4px',
          marginBottom: '8px'
        }}>
          {weekDays.map(day => (
            <div key={day} style={{
              textAlign: 'center',
              fontSize: '12px',
              fontWeight: 600,
              color: 'hsl(var(--text-muted))',
              padding: '8px 0'
            }}>
              {day}
            </div>
          ))}
        </div>

        {/* Date cells */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, 1fr)',
          gap: '4px'
        }}>
          {cells.map((day, idx) => (
            <div
              key={idx}
              onClick={() => day && handleDateClick(day)}
              style={{
                aspectRatio: '1',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '14px',
                fontWeight: day ? 600 : 400,
                color: day 
                  ? (selectedDate === day || isInRange(day)) 
                    ? '#fff' 
                    : 'hsl(var(--text))'
                  : 'transparent',
                background: day 
                  ? selectedDate === day
                    ? 'hsl(var(--primary))'
                    : isInRange(day)
                      ? 'hsl(var(--secondary))'
                      : 'transparent'
                  : 'transparent',
                borderRadius: '6px',
                cursor: day && !disabled ? 'pointer' : 'default',
                transition: 'all 0.1s ease'
              }}
            >
              {day}
            </div>
          ))}
        </div>
      </div>

      {/* Selection feedback */}
      <div style={{
        marginTop: '20px',
        textAlign: 'center',
        fontSize: '16px',
        fontWeight: 600,
        color: 'hsl(var(--text))'
      }}>
        {task_type === 'select_date' ? (
          selectedDate ? (
            <span>Selected: <strong style={{ color: 'hsl(var(--primary))' }}>{params.month}/{selectedDate}/{params.year}</strong></span>
          ) : (
            <span style={{ color: 'hsl(var(--text-muted))' }}>Click a date to select it</span>
          )
        ) : (
          <>
            {rangeStart && !rangeEnd && (
              <span style={{ color: 'hsl(var(--text-muted))' }}>Click another date to complete the range</span>
            )}
            {computedDuration && (
              <span>
                Range: {params.month}/{rangeStart} to {params.month}/{rangeEnd} = <strong style={{ color: 'hsl(var(--primary))' }}>{computedDuration} days</strong>
              </span>
            )}
            {!rangeStart && (
              <span style={{ color: 'hsl(var(--text-muted))' }}>Click a date to start the range</span>
            )}
          </>
        )}
      </div>

      {!disabled && task_type === 'measure_duration' && (
        <div style={{
          marginTop: '12px',
          fontSize: '12px',
          color: 'hsl(var(--text-muted))',
          textAlign: 'center'
        }}>
          Click two dates to measure the duration between them
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  EMOJI PICTORIAL INTERACTIVE
// ============================================================================
export function EmojiPictorialInteractive({ params, disabled }) {
  const {
    emoji,
    group_a,
    group_b,
    operation,
    layout,
    reveal_text
  } = params || {};

  const renderEmojiNumber = (count, emoji, isCrossedOut = false) => {
    if (count === 0) return null;
    
    // If count <= 20, just render them individually
    if (count <= 20) {
      return Array.from({ length: count }).map((_, i) => (
        <span key={`single-${i}`} style={{
          display: 'inline-block',
          position: 'relative',
          opacity: isCrossedOut ? 0.5 : 1
        }}>
          {emoji}
          {isCrossedOut && (
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              width: '100%',
              height: '4px',
              background: 'red',
              transform: 'translate(-50%, -50%) rotate(-45deg)',
              borderRadius: '2px'
            }} />
          )}
        </span>
      ));
    }
    
    // For large numbers, do grouping
    const thousands = Math.floor(count / 1000);
    const hundreds = Math.floor((count % 1000) / 100);
    const tens = Math.floor((count % 100) / 10);
    const ones = count % 10;
    
    const groups = [
      { value: 1000, count: thousands, icon: '🚚', label: '1000x' },
      { value: 100, count: hundreds, icon: '📦', label: '100x' },
      { value: 10, count: tens, icon: '🛍️', label: '10x' },
      { value: 1, count: ones, icon: emoji, label: '' }
    ];
    
    const elements = [];
    groups.forEach(({ value, count: grpCount, icon, label }) => {
      for (let i = 0; i < grpCount; i++) {
        if (value === 1) {
          elements.push(
            <div key={`grp-1-${i}`} style={{
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'hsl(var(--card-bg))',
              border: '2px solid hsl(var(--border-color))',
              borderRadius: '8px',
              padding: '8px',
              minWidth: '70px',
              position: 'relative',
              opacity: isCrossedOut ? 0.5 : 1
            }}>
              <span style={{ fontSize: '36px' }}>{emoji}</span>
              <span style={{ fontSize: '14px', fontWeight: 'bold' }}>1x {emoji}</span>
              {isCrossedOut && (
                <div style={{
                  position: 'absolute', top: '50%', left: '50%',
                  width: '120%', height: '4px', background: 'red',
                  transform: 'translate(-50%, -50%) rotate(-45deg)',
                  borderRadius: '2px'
                }} />
              )}
            </div>
          );
        } else {
          elements.push(
            <div key={`grp-${value}-${i}`} style={{
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'hsl(var(--card-bg))',
              border: '2px solid hsl(var(--border-color))',
              borderRadius: '8px',
              padding: '8px',
              minWidth: '70px',
              position: 'relative',
              opacity: isCrossedOut ? 0.5 : 1
            }}>
              <span style={{ fontSize: '36px' }}>{icon}</span>
              <span style={{ fontSize: '14px', fontWeight: 'bold' }}>{label} {emoji}</span>
              {isCrossedOut && (
                <div style={{
                  position: 'absolute', top: '50%', left: '50%',
                  width: '120%', height: '4px', background: 'red',
                  transform: 'translate(-50%, -50%) rotate(-45deg)',
                  borderRadius: '2px'
                }} />
              )}
            </div>
          );
        }
      }
    });
    
    return elements;
  };

  if (operation === 'subtraction') {
    const remaining = Math.max(0, group_a - group_b);
    const crossedOut = Math.min(group_a, group_b);

    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '8px',
          justifyContent: 'center',
          fontSize: '48px',
          lineHeight: '1.2'
        }}>
          {renderEmojiNumber(remaining, emoji, false)}
          {renderEmojiNumber(crossedOut, emoji, true)}
        </div>
        {disabled && reveal_text && (
          <div style={{ marginTop: '20px', fontSize: '18px', fontWeight: 600, color: 'hsl(var(--primary))' }}>
            {reveal_text}
          </div>
        )}
      </div>
    );
  }

  if (operation === 'counting') {
    const displayA = renderEmojiNumber(group_a, emoji) || <span style={{ opacity: 0.3 }}>Empty</span>;
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', letterSpacing: '4px', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>
          {displayA}
        </div>
      </div>
    );
  }

  // Addition layouts
  const displayA = renderEmojiNumber(group_a, emoji) || <span style={{ opacity: 0.3 }}>Empty</span>;
  const displayB = renderEmojiNumber(group_b, emoji) || <span style={{ opacity: 0.3 }}>Empty</span>;

  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      {layout === 'stacked' ? (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontSize: '48px', letterSpacing: '4px', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>{displayA}</div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'hsl(var(--text-muted))' }}>+</div>
          <div style={{ fontSize: '48px', letterSpacing: '4px', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>{displayB}</div>
        </div>
      ) : layout === 'separated' ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '30px' }}>
          <div style={{
            padding: '20px',
            background: 'hsl(var(--card-bg))',
            borderRadius: '16px',
            border: '2px dashed hsl(var(--border-color))',
            fontSize: '40px',
            display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px'
          }}>
            {displayA}
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'hsl(var(--text-muted))' }}>+</div>
          <div style={{
            padding: '20px',
            background: 'hsl(var(--card-bg))',
            borderRadius: '16px',
            border: '2px dashed hsl(var(--border-color))',
            fontSize: '40px',
            display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px'
          }}>
            {displayB}
          </div>
        </div>
      ) : (
        // Inline (default)
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <div style={{ fontSize: '48px', letterSpacing: '4px', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>{displayA}</div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: 'hsl(var(--text-muted))' }}>and</div>
          <div style={{ fontSize: '48px', letterSpacing: '4px', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px' }}>{displayB}</div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  PLACE VALUE BLOCKS INTERACTIVE
// ============================================================================
export function PlaceValueBlocksInteractive({ params, onAnswer, disabled }) {
  const { 
    thousands: targetT = 0, 
    hundreds: targetH = 0, 
    tens: targetTen = 0, 
    ones: targetO = 0, 
    is_interactive = true
  } = params || {};

  // Track the student's selected counts in interactive/set mode
  const [thousands, setThousands] = useState(0);
  const [hundreds, setHundreds] = useState(0);
  const [tens, setTens] = useState(0);
  const [ones, setOnes] = useState(0);
  const hasInteractedRef = useRef(false);

  const handleThChange = (fn) => {
    hasInteractedRef.current = true;
    setThousands(fn);
  };
  const handleHChange = (fn) => {
    hasInteractedRef.current = true;
    setHundreds(fn);
  };
  const handleTenChange = (fn) => {
    hasInteractedRef.current = true;
    setTens(fn);
  };
  const handleOChange = (fn) => {
    hasInteractedRef.current = true;
    setOnes(fn);
  };

  useEffect(() => {
    if (is_interactive) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setThousands(0);
      setHundreds(0);
      setTens(0);
      setOnes(0);
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setThousands(targetT);
      setHundreds(targetH);
      setTens(targetTen);
      setOnes(targetO);
    }
  }, [is_interactive, targetT, targetH, targetTen, targetO]);

  useEffect(() => {
    if (is_interactive && onAnswer && hasInteractedRef.current) {
      const currentTotal = thousands * 1000 + hundreds * 100 + tens * 10 + ones;
      onAnswer(currentTotal);
    }
  }, [thousands, hundreds, tens, ones, is_interactive, onAnswer]);

  const unitSize = 14;
  const colorT = '#a78bfa'; // thousands - purple
  const colorH = '#10b981'; // hundreds - green
  const colorTen = '#3b82f6'; // tens - blue
  const colorO = '#b91c5c'; // ones - maroon

  const blockStyle = (color, w, h) => ({
    width: `${w}px`, height: `${h}px`,
    borderRadius: '3px', background: `${color}30`, border: `2px solid ${color}`,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: Math.min(10, h / 3) + 'px', color, fontWeight: 700, flexShrink: 0,
  });

  const showT = is_interactive ? (targetT > 0) : (thousands > 0);
  const showH = is_interactive ? (targetH > 0 || targetT > 0) : (hundreds > 0);
  const showTen = is_interactive ? true : (tens > 0);
  const showO = is_interactive ? true : (ones > 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
      <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', width: '100%', maxWidth: '500px' }}>
        {/* Legend */}
        <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginBottom: '14px', flexWrap: 'wrap', fontSize: '11px' }}>
          {showT && <span style={{ color: colorT }}>■ = 1000</span>}
          {showH && <span style={{ color: colorH }}>■ = 100</span>}
          {showTen && <span style={{ color: colorTen }}>▮ = 10</span>}
          {showO && <span style={{ color: colorO }}>• = 1</span>}
        </div>
        
        {/* Render blocks */}
        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', alignItems: 'flex-end', flexWrap: 'wrap', minHeight: `${unitSize * 10 + 10}px` }}>
          {thousands > 0 && Array.from({ length: Math.min(thousands, 9) }).map((_, i) => (
            <div key={`th-${i}`} style={blockStyle(colorT, unitSize * 4, unitSize * 10)}>{unitSize * 10 > 40 ? '1000' : 'K'}</div>
          ))}
          {hundreds > 0 && Array.from({ length: Math.min(hundreds, 9) }).map((_, i) => (
            <div key={`h-${i}`} style={blockStyle(colorH, unitSize * 3, unitSize * 8)}>100</div>
          ))}
          {tens > 0 && Array.from({ length: Math.min(tens, 9) }).map((_, i) => (
            <div key={`t-${i}`} style={blockStyle(colorTen, unitSize * 2, unitSize * 10)}>10</div>
          ))}
          {ones > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px', maxWidth: `${unitSize * 5}px`, alignContent: 'flex-end' }}>
              {Array.from({ length: Math.min(ones, 9) }).map((_, i) => (
                <div key={`o-${i}`} style={blockStyle(colorO, unitSize, unitSize)}>1</div>
              ))}
            </div>
          )}
        </div>

        {/* Counter Summary for interactive mode */}
        {is_interactive && (
          <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '13px', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>
            Your blocks: {[thousands > 0 && `${thousands}×1000`, hundreds > 0 && `${hundreds}×100`, tens > 0 && `${tens}×10`, ones > 0 && `${ones}×1`].filter(Boolean).join(' + ') || 'None'} = {thousands * 1000 + hundreds * 100 + tens * 10 + ones}
          </div>
        )}
      </div>

      {/* Control panel for incrementing/decrementing blocks */}
      {is_interactive && !disabled && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))', gap: '10px', width: '100%', maxWidth: '500px' }}>
          {showT && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: `1px solid ${colorT}20` }}>
              <span style={{ fontSize: '11px', color: colorT, fontWeight: 600 }}>1000s</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleThChange(prev => Math.max(0, prev - 1))}>-</button>
                <span style={{ fontSize: '14px', fontWeight: 700 }}>{thousands}</span>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleThChange(prev => Math.min(9, prev + 1))}>+</button>
              </div>
            </div>
          )}

          {showH && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: `1px solid ${colorH}20` }}>
              <span style={{ fontSize: '11px', color: colorH, fontWeight: 600 }}>100s</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleHChange(prev => Math.max(0, prev - 1))}>-</button>
                <span style={{ fontSize: '14px', fontWeight: 700 }}>{hundreds}</span>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleHChange(prev => Math.min(9, prev + 1))}>+</button>
              </div>
            </div>
          )}

          {showTen && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: `1px solid ${colorTen}20` }}>
              <span style={{ fontSize: '11px', color: colorTen, fontWeight: 600 }}>10s</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleTenChange(prev => Math.max(0, prev - 1))}>-</button>
                <span style={{ fontSize: '14px', fontWeight: 700 }}>{tens}</span>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleTenChange(prev => Math.min(9, prev + 1))}>+</button>
              </div>
            </div>
          )}

          {showO && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: `1px solid ${colorO}20` }}>
              <span style={{ fontSize: '11px', color: colorO, fontWeight: 600 }}>1s</span>
              <div style={{ display: 'flex', gap: '6px' }}>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleOChange(prev => Math.max(0, prev - 1))}>-</button>
                <span style={{ fontSize: '14px', fontWeight: 700 }}>{ones}</span>
                <button type="button" className="btn-secondary" style={{ padding: '2px 8px', fontSize: '12px', minWidth: '24px' }} onClick={() => handleOChange(prev => Math.min(9, prev + 1))}>+</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================================
//  EXPORTS
// ============================================================================

// ============================================================================
//  PATTERN SEQUENCE (READ MODE)
// ============================================================================
export function PatternSequenceInteractive({ params, onAnswer, disabled }) {
  const sequence = params.sequence || [];
  const missingIndices = params.missing_indices || [];
  const isInteractive = params.is_interactive !== false && onAnswer !== undefined;
  
  const [inputs, setInputs] = useState({});
  const hasInteractedRef = useRef(false);

  useEffect(() => {
    if (isInteractive && onAnswer) {
      if (hasInteractedRef.current) {
        if (missingIndices.length === 1) {
          const val = inputs[missingIndices[0]] ?? '';
          const isNumber = typeof sequence[missingIndices[0]] === 'number';
          onAnswer(isNumber ? (parseInt(val) || 0) : val);
        } else {
          const arr = missingIndices.map(idx => {
            const val = inputs[idx] ?? '';
            const isNumber = typeof sequence[idx] === 'number';
            return isNumber ? (parseInt(val) || 0) : val;
          });
          onAnswer(arr);
        }
      }
    }
  }, [inputs, isInteractive]);

  const handleChange = (idx, val) => {
    hasInteractedRef.current = true;
    setInputs(prev => ({ ...prev, [idx]: val }));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', padding: '20px', width: '100%' }}>
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', justifyContent: 'center' }}>
        {sequence.map((item, idx) => {
          const isMissing = missingIndices.includes(idx);
          return isMissing && isInteractive ? (
            <input
              key={idx}
              type="text"
              value={inputs[idx] ?? ''}
              onChange={e => handleChange(idx, e.target.value)}
              disabled={disabled}
              style={{
                width: '60px',
                height: '60px',
                borderRadius: '12px',
                border: '2px solid hsl(var(--primary))',
                background: 'rgba(255,255,255,0.05)',
                color: '#fff',
                textAlign: 'center',
                fontSize: '18px',
                fontWeight: 700,
                outline: 'none'
              }}
            />
          ) : (
            <div 
              key={idx}
              style={{
                width: '60px',
                height: '60px',
                borderRadius: '12px',
                background: isMissing ? 'rgba(255,255,255,0.05)' : 'rgba(99,102,241,0.15)',
                border: isMissing ? '2px dashed rgba(255,255,255,0.2)' : '2px solid rgba(99,102,241,0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px',
                fontWeight: 700,
                color: isMissing ? 'hsl(var(--text-muted))' : '#f1f5f9',
                boxShadow: isMissing ? 'none' : '0 4px 12px rgba(0,0,0,0.1)'
              }}
            >
              {isMissing ? '?' : item}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
//  FRACTION MODEL & SHADE
// ============================================================================
export function FractionModelInteractive({ params, onAnswer, disabled }) {
  const isReadOnly = params.interaction_mode === 'read' || params.is_read_only || !onAnswer;
  const den = params.denominator || params.total_parts || params.parts || 1;
  const num = params.numerator !== undefined ? params.numerator : (params.shaded_parts || 0);
  const modelType = params.model_type || 'area';
  // Use total_wholes if the formatter provided it (handles improper
  // fractions in set mode where shaded_parts is stripped for answer-leak
  // protection — without this, wholeUnits would collapse to 1).
  const wholeUnits = Math.max(1, Math.ceil(
    (params.total_wholes !== undefined ? params.total_wholes * den : num) / den
  ));

  const [clickedParts, setClickedParts] = React.useState(() => {
    if (isReadOnly) {
      return num;
    }
    return 0; // Interactive mode starts with 0 shaded parts
  });
  const hasInteractedRef = React.useRef(false);
  const firstRenderRef = React.useRef(true);

  React.useEffect(() => {
    firstRenderRef.current = false;
  }, []);

  React.useEffect(() => {
    if (onAnswer && !disabled && hasInteractedRef.current) {
      onAnswer(`${clickedParts}/${den}`);
    }
  }, [clickedParts, onAnswer, disabled, den]);

  if (params.operation === 'add' || params.operation === 'subtract' || params.operation === 'add_subtract') {
    const opSign = params.operation === 'subtract' ? '-' : '+';

    // Render 3 models: A {opSign} B = Result. Operands are always read-only —
    // only the result model is interactive (that's what the student answers).
    const aParams = { ...params, operation: undefined, numerator: params.a_numerator, denominator: params.a_denominator, interaction_mode: 'read' };
    const bParams = { ...params, operation: undefined, numerator: params.b_numerator, denominator: params.b_denominator, interaction_mode: 'read' };
    const resParams = { ...params, operation: undefined }; // inherits interaction_mode

    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '20px', width: '100%', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 auto', minWidth: '150px' }}>
          <FractionModelInteractive params={aParams} disabled={true} />
        </div>
        <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'white' }}>{opSign}</div>
        <div style={{ flex: '1 1 auto', minWidth: '150px' }}>
          <FractionModelInteractive params={bParams} disabled={true} />
        </div>
        <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'white' }}>=</div>
        <div style={{ flex: '1 1 auto', minWidth: '150px' }}>
          <FractionModelInteractive params={resParams} onAnswer={onAnswer} disabled={disabled} />
        </div>
      </div>
    );
  }

  const isClickable = onAnswer && !disabled;

  if (modelType === 'number_line') {
    return (
      <div style={{ padding: '20px', width: '100%', maxWidth: '400px', margin: '0 auto' }}>
        <NumberLineInteractive 
          params={{
            start: 0,
            end: wholeUnits,
            minor_interval: 1 / den,
            major_interval: 1,
            dot_value: isReadOnly ? (num / den) : 0,
            is_interactive: !isReadOnly
          }} 
          onAnswer={(val) => {
            hasInteractedRef.current = true;
            setClickedParts(Math.round(val * den));
          }}
          disabled={disabled}
        />
      </div>
    );
  }

  if (modelType === 'set' || modelType === 'set_model') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', width: '100%' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center' }}>
          {Array.from({ length: wholeUnits }).map((_, unitIdx) => (
            <div key={unitIdx} style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', maxWidth: '200px', justifyContent: 'center', border: '2px dashed rgba(255,255,255,0.2)', padding: '10px', borderRadius: '8px' }}>
              {Array.from({ length: den }).map((_, i) => {
                const globalIdx = unitIdx * den + i;
                return (
                  <div 
                    key={i} 
                    onClick={() => {
                      if (isClickable) {
                        hasInteractedRef.current = true;
                        setClickedParts(globalIdx + 1);
                      }
                    }}
                    style={{
                      width: '35px',
                      height: '35px',
                      borderRadius: '50%',
                      border: '3px solid hsl(var(--primary))',
                      cursor: isClickable ? "pointer" : "default",
                      background: globalIdx < clickedParts ? 'rgba(99,102,241,0.5)' : 'transparent',
                    }} 
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Default 'area'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', width: '100%', gap: '15px' }}>
      {Array.from({ length: wholeUnits }).map((_, unitIdx) => (
        <div key={unitIdx} style={{ 
          display: 'flex', 
          width: '100%', 
          maxWidth: '400px', 
          height: '60px', 
          border: '3px solid hsl(var(--primary))',
          cursor: isClickable ? "pointer" : "default", 
          borderRadius: '8px', 
          overflow: 'hidden' 
        }}>
          {Array.from({ length: den }).map((_, i) => {
            const globalIdx = unitIdx * den + i;
            return (
              <div 
                key={i} 
                onClick={() => {
                  if (isClickable) {
                    hasInteractedRef.current = true;
                    setClickedParts(globalIdx + 1);
                  }
                }}
                style={{
                  flex: 1,
                  background: globalIdx < clickedParts ? 'rgba(99,102,241,0.5)' : 'transparent',
                  cursor: isClickable ? "pointer" : "default",
                  borderRight: i < den - 1 ? '2px solid hsl(var(--primary))' : 'none'
                }} 
              />
            );
          })}
        </div>
      ))}
    </div>
  );
}

export function FractionShadeInteractive({ params, onAnswer, disabled }) {
  return <FractionModelInteractive params={params} onAnswer={onAnswer} disabled={disabled} />;
}

// ============================================================================
//  TEN FRAME
// ============================================================================
export function TenFrameInteractive({ params, onAnswer, disabled }) {
  const targetFilled = params.filled || 0;
  const total = params.total || 10;
  const isInteractive = params.query_type === 'show_number' || params.is_interactive || (onAnswer !== undefined && !disabled);

  const [filledCount, setFilledCount] = useState(() => {
    if (isInteractive) return 0;
    return targetFilled;
  });
  const hasInteractedRef = useRef(false);

  useEffect(() => {
    if (isInteractive && onAnswer && hasInteractedRef.current) {
      onAnswer(filledCount);
    }
  }, [filledCount, isInteractive]);

  const handleCellClick = (index) => {
    if (disabled || !isInteractive) return;
    hasInteractedRef.current = true;
    if (filledCount === index + 1) {
      setFilledCount(index);
    } else {
      setFilledCount(index + 1);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', width: '100%' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(5, 1fr)',
        gap: '4px',
        padding: '8px',
        background: 'rgba(255,255,255,0.05)',
        border: '3px solid hsl(var(--secondary))',
        borderRadius: '12px'
      }}>
        {Array.from({ length: total }).map((_, i) => (
          <div 
            key={i} 
            onClick={() => handleCellClick(i)}
            style={{
              width: '50px',
              height: '50px',
              border: '2px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: (isInteractive && !disabled) ? 'pointer' : 'default'
            }}
          >
            {i < filledCount && (
              <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: '#ef4444' }} />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
//  RULER MEASURE
// ============================================================================
export function RulerMeasureInteractive({ params, onAnswer, disabled }) {
  const isSetMode = onAnswer && !disabled;
  const length = params.length || 0;
  const startOffset = params.object_start || 0;
  const unit = params.unit || 'cm';
  const max = params.max_val || Math.max(10, Math.ceil(length + startOffset + 2));
  
  const [val, setVal] = React.useState(0);
  const hasInteractedRef = React.useRef(false);

  React.useEffect(() => {
    if (isSetMode && hasInteractedRef.current) {
      onAnswer(`${val} ${unit}`);
    }
  }, [val, isSetMode]);

  return (
    <div style={{ padding: '40px 20px', display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
      {/* Object being measured */}
      {!isSetMode ? (
        <div style={{ 
          width: `${(length / max) * 100}%`, 
          marginLeft: `${(startOffset / max) * 100}%`,
          height: '40px', 
          background: 'linear-gradient(90deg, #f59e0b, #fbbf24)',
          borderRadius: '4px',
          marginBottom: '10px',
          alignSelf: 'flex-start'
        }} />
      ) : (
        <div style={{ width: '100%', marginBottom: '10px', display: 'flex', alignItems: 'center' }}>
          <input 
            type="range" 
            min={0} 
            max={max} 
            step={1} 
            value={val} 
            onChange={(e) => {
              hasInteractedRef.current = true;
              setVal(parseInt(e.target.value));
            }}
            style={{ width: '100%' }}
          />
          <span style={{ marginLeft: '10px', fontWeight: 'bold' }}>{val} {unit}</span>
        </div>
      )}
      
      {/* Ruler */}
      <div style={{ 
        width: '100%', 
        height: '60px', 
        background: '#f8fafc', 
        borderRadius: '4px',
        display: 'flex',
        position: 'relative',
        border: '2px solid #cbd5e1'
      }}>
        {Array.from({ length: max + 1 }).map((_, i) => (
          <div key={i} style={{
            position: 'absolute',
            left: `${(i / max) * 100}%`,
            top: 0,
            bottom: i % 5 === 0 ? 0 : '50%',
            width: '2px',
            background: '#475569',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'flex-end'
          }}>
            {i % 5 === 0 && (
              <span style={{ color: '#0f172a', fontSize: '12px', fontWeight: 700, position: 'absolute', bottom: '5px' }}>
                {i}
              </span>
            )}
          </div>
        ))}
        <span style={{ position: 'absolute', right: '10px', bottom: '5px', color: '#0f172a', fontSize: '14px', fontWeight: 700 }}>
          {unit}
        </span>
      </div>
    </div>
  );
}

// ============================================================================
//  BALANCE SCALE
// ============================================================================
export function BalanceScaleInteractive({ params }) {
  const left = Array.isArray(params.left_side) ? params.left_side.join(' + ') : params.left_side;
  const right = Array.isArray(params.right_side) ? params.right_side.join(' + ') : params.right_side;
  const rotate = params.is_balanced ? 0 : (params.left_weight > params.right_weight ? -10 : 10);
  
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '40px 20px', height: '200px', width: '100%' }}>
      <div style={{
        width: '100%',
        maxWidth: '300px',
        height: '10px',
        background: '#94a3b8',
        position: 'relative',
        transform: `rotate(${rotate}deg)`,
        transition: 'transform 0.5s ease',
        borderRadius: '5px'
      }}>
        <div style={{
          position: 'absolute', left: '-20px', top: '-40px', width: '60px', height: '40px',
          background: 'rgba(59,130,246,0.2)', border: '2px solid #3b82f6', borderRadius: '8px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700
        }}>
          {left}
        </div>
        <div style={{
          position: 'absolute', right: '-20px', top: '-40px', width: '60px', height: '40px',
          background: 'rgba(59,130,246,0.2)', border: '2px solid #3b82f6', borderRadius: '8px',
          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 700
        }}>
          {right}
        </div>
      </div>
      <div style={{
        width: 0, height: 0,
        borderLeft: '20px solid transparent',
        borderRight: '20px solid transparent',
        borderBottom: '40px solid #64748b',
        marginTop: '-5px'
      }} />
    </div>
  );
}

// ============================================================================
//  SHAPE BOARD
// ============================================================================
export function ShapeBoardInteractive({ params, onAnswer, disabled }) {
  const shapes = params.shapes || [];
  const isSetMode = onAnswer && !disabled;
  const [order, setOrder] = React.useState([]);
  const hasInteractedRef = React.useRef(false);

  React.useEffect(() => {
    if (isSetMode && hasInteractedRef.current) {
      // Return array of selected shape indices in order
      onAnswer(order);
    }
  }, [order, isSetMode]);

  const handleShapeClick = (idx) => {
    if (!isSetMode) return;
    hasInteractedRef.current = true;
    setOrder(prev => {
      if (prev.includes(idx)) {
        return prev.filter(x => x !== idx);
      } else {
        return [...prev, idx];
      }
    });
  };
  
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '25px', justifyContent: 'center', padding: '20px', width: '100%' }}>
      {shapes.map((s, i) => {
        let borderRadius = '0';
        if (s.type.includes('circle')) borderRadius = '50%';
        else if (s.type.includes('oval')) borderRadius = '50% / 30%';
        
        const isHighlighted = params.highlighted_shape && (
          s.id ? s.id === params.highlighted_shape.id : JSON.stringify(s) === JSON.stringify(params.highlighted_shape)
        );
        const rank = order.indexOf(i) + 1;
        
        return (
          <div 
            key={i} 
            onClick={() => handleShapeClick(i)}
            style={{ 
              display: 'flex', 
              flexDirection: 'column', 
              alignItems: 'center', 
              gap: '8px', 
              opacity: (params.highlighted_shape && !isHighlighted) ? 0.3 : 1,
              cursor: isSetMode ? "pointer" : "default",
              outline: order.includes(i) ? "2px solid #3b82f6" : "none",
              padding: "5px",
              borderRadius: "8px",
              position: "relative"
            }}>
            {isSetMode && rank > 0 && (
              <span style={{ 
                position: 'absolute', 
                top: '-10px', 
                right: '-10px', 
                background: '#3b82f6', 
                color: '#fff', 
                borderRadius: '50%', 
                width: '20px', 
                height: '20px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '12px',
                fontWeight: 'bold',
                zIndex: 20
              }}>
                {rank}
              </span>
            )}
            <div style={{
              filter: isHighlighted ? 'drop-shadow(0 0 15px #f59e0b) drop-shadow(0 0 5px #f59e0b)' : 'drop-shadow(0 4px 6px rgba(0,0,0,0.1))',
              transform: `rotate(${s.orientation_deg || 0}deg) ${isHighlighted ? 'scale(1.3)' : 'scale(1)'}`,
              transition: 'all 0.3s ease',
              zIndex: isHighlighted ? 10 : 1,
              width: '50px', height: '50px',
              border: isHighlighted && !s.type.includes('triangle') ? '4px solid #f59e0b' : 'none',
              borderRadius: borderRadius,
              boxSizing: 'border-box'
            }}>
              <div style={{
                width: '100%', height: '100%',
                background: 'hsl(var(--primary))',
                borderRadius: borderRadius,
                clipPath: s.type.includes('triangle') ? 'polygon(50% 0%, 0% 100%, 100% 100%)' : 'none',
              }} />
            </div>
            {params.question_type === 'compare' && i < 2 && (
              <span style={{ fontWeight: 700, fontSize: '18px', color: 'hsl(var(--text))' }}>
                {i === 0 ? 'A' : 'B'}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}


export function NumberBondInteractive({ params, onAnswer, disabled }) {
  const { whole, part1, part2, blank_position } = params;
  
  const [val, setVal] = React.useState('');
  const hasInteractedRef = React.useRef(false);

  React.useEffect(() => {
    if (onAnswer && !disabled && hasInteractedRef.current) {
      if (val !== '') {
        onAnswer(parseInt(val, 10));
      } else {
        onAnswer(null);
      }
    }
  }, [val, onAnswer, disabled]);

  const renderCircle = (num, isBlank) => (
    <div style={{
      width: '80px', height: '80px', borderRadius: '50%',
      border: '3px solid hsl(var(--primary))',
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      fontSize: '24px', fontWeight: 600, background: 'rgba(255,255,255,0.05)',
      color: 'hsl(var(--text))'
    }}>
      {isBlank && !disabled ? (
        <input 
          type="number"
          value={val}
          onChange={(e) => {
            hasInteractedRef.current = true;
            setVal(e.target.value);
          }}
          style={{ width: '80%', height: '80%', textAlign: 'center', background: 'transparent', border: 'none', color: 'inherit', fontSize: '24px', outline: 'none' }}
        />
      ) : (
        isBlank ? "?" : num
      )}
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px', gap: '20px' }}>
      {renderCircle(whole, blank_position === 'whole')}
      <div style={{ display: 'flex', gap: '40px' }}>
        {renderCircle(part1, blank_position === 'part1')}
        {renderCircle(part2, blank_position === 'part2')}
      </div>
    </div>
  );
}
