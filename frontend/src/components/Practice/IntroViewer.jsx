import React from 'react';
import { Play, ChevronLeft, ChevronRight, Check, X, Maximize2, Minimize2, Shield, User, RefreshCw, Zap, AlertTriangle } from 'lucide-react';
import { API_BASE } from '../../api/apiClient';

export default function IntroViewer({
  introContent,
  introMiniLessonIndex, setIntroMiniLessonIndex,
  introSlideIndex, setIntroSlideIndex,
  introStepIndex, setIntroStepIndex,
  socraticActive, setSocraticActive,
  chatMessages, setChatMessages,
  sendingChat, setSendingChat,
  socraticAbortControllerRef,
  selectedStudent,
  selectedSubdomain
}) {
  return (
      <>
        {introContent && (() => {
                        const ml = introContent.mini_lessons[introMiniLessonIndex];
                        if (!ml) return null;
                        const slide = ml.slides[introSlideIndex];
                        if (!slide) return null;
  
                        const totalSlides = ml.slides.length;
                        const totalMiniLessons = introContent.mini_lessons.length;
  
                        // For worked examples, handle step-by-step
                        const isWorkedExample = slide.type === 'worked_example';
                        const totalSteps = isWorkedExample ? slide.steps.length : 0;
                        const currentStep = isWorkedExample ? slide.steps[Math.min(introStepIndex, totalSteps - 1)] : null;
  
                        return (
                          <div className="glass-card" style={{ padding: '24px' }}>
                            {/* Header: Mini-lesson navigation */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '14px' }}>
                              <div>
                                <span style={{ fontSize: '11px', fontWeight: 700, color: '#06b6d4', letterSpacing: '0.1em' }}>
                                  MINI-LESSON {introMiniLessonIndex + 1} OF {totalMiniLessons}
                                </span>
                                <h3 style={{ fontSize: '20px', margin: '4px 0 0 0' }}>{ml.title}</h3>
                              </div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                {/* Mini-lesson dot indicators */}
                                <div style={{ display: 'flex', gap: '6px' }}>
                                  {introContent.mini_lessons.map((_, idx) => (
                                    <div
                                      key={idx}
                                      onClick={() => { setIntroMiniLessonIndex(idx); setIntroSlideIndex(0); setIntroStepIndex(0); }}
                                      style={{
                                        width: '10px', height: '10px', borderRadius: '50%', cursor: 'pointer',
                                        background: idx === introMiniLessonIndex ? '#06b6d4' : 'rgba(255,255,255,0.15)',
                                      }}
                                    />
                                  ))}
                                </div>
                                {/* Ask Tutor toggle */}
                                <button
                                  onClick={() => {
                                    setSocraticActive(prev => !prev);
                                    if (chatMessages.length === 0 && !sendingChat) {
                                      setSendingChat(true);
                                      if (socraticAbortControllerRef.current) {
                                        socraticAbortControllerRef.current.abort();
                                      }
                                      socraticAbortControllerRef.current = new AbortController();
                                      fetch(`${API_BASE}/socratic/chat`, {
                                        method: 'POST',
                                        signal: socraticAbortControllerRef.current.signal,
                                        headers: { 'Content-Type': 'application/json' },
                                        body: JSON.stringify({
                                          student_id:     selectedStudent.id,
                                          skill_id:       introContent?.node_key || selectedSubdomain || '',
                                          question_text:  introContent?.mini_lessons?.[introMiniLessonIndex]?.slides?.[introSlideIndex]?.content || '',
                                          student_answer: '',
                                          is_intro:       true,
                                          message: '',
                                          history: []
                                        })
                                      })
                                      .then(res => res.json())
                                      .then(chatData => {
                                        if (!socraticAbortControllerRef.current?.signal.aborted) {
                                          setChatMessages([{ role: 'assistant', content: chatData.reply }]);
                                        }
                                      })
                                      .catch(e => {
                                        if (e.name !== 'AbortError') console.error(e);
                                      })
                                      .finally(() => {
                                        if (!socraticAbortControllerRef.current?.signal.aborted) {
                                          setSendingChat(false);
                                        }
                                      });
                                    }
                                  }}
                                  style={{
                                    display: 'flex', alignItems: 'center', gap: '6px',
                                    padding: '6px 14px', fontSize: '12px', fontWeight: 600,
                                    borderRadius: '20px', cursor: 'pointer',
                                    background: socraticActive ? 'rgba(139,92,246,0.25)' : 'rgba(139,92,246,0.1)',
                                    border: `1px solid ${socraticActive ? 'rgba(139,92,246,0.6)' : 'rgba(139,92,246,0.3)'}`,
                                    color: '#c084fc', transition: 'all 0.2s',
                                  }}
                                >
                                  <span>💡</span>
                                  <span>{socraticActive ? 'Close Tutor' : 'Ask Tutor'}</span>
                                </button>
                              </div>
                            </div>
  
                            {/* Slide type indicator */}
                            <div style={{ marginBottom: '16px' }}>
                              <span style={{
                                fontSize: '11px', fontWeight: 700, padding: '3px 10px', borderRadius: '6px',
                                background: (slide.type === 'introduction' || slide.type === 'explanation') ? 'rgba(139,92,246,0.15)' :
                                            slide.type === 'definitions' ? 'rgba(16,185,129,0.15)' :
                                            'rgba(245,158,11,0.15)',
                                color: (slide.type === 'introduction' || slide.type === 'explanation') ? '#a78bfa' :
                                       slide.type === 'definitions' ? '#34d399' : '#fbbf24',
                              }}>
                                {(slide.type === 'introduction' || slide.type === 'explanation') ? 'INTRODUCTION' :
                                 slide.type === 'definitions' ? 'DEFINITIONS' :
                                 `WORKED EXAMPLE: ${slide.title}`}
                              </span>
                            </div>
  
                            {/* Slide content */}
                            <div style={{ minHeight: '200px', marginBottom: '20px' }}>
                              {(slide.type === 'introduction' || slide.type === 'explanation') && (
                                <div style={{ fontSize: '16px', lineHeight: '1.8', whiteSpace: 'pre-line' }}>
                                  {slide.content}
                                </div>
                              )}
  
                              {slide.type === 'definitions' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  {slide.terms.map((t, i) => (
                                    <div key={i} style={{ padding: '12px 16px', borderRadius: '10px', background: 'rgba(16,185,129,0.06)', border: '1px solid rgba(16,185,129,0.15)' }}>
                                      <span style={{ fontWeight: 700, color: '#34d399' }}>{t.term}</span>
                                      <span style={{ color: 'hsl(var(--text-muted))', margin: '0 8px' }}>—</span>
                                      <span>{t.definition}</span>
                                      {t.example && <span style={{ color: 'hsl(var(--text-muted))', marginLeft: '12px', fontStyle: 'italic' }}>e.g., {t.example}</span>}
                                    </div>
                                  ))}
                                </div>
                              )}
  
                              {isWorkedExample && currentStep && (
                                <div>
                                  {/* Step text with colored math rendering */}
                                  <div style={{ fontSize: '16px', lineHeight: '1.8', whiteSpace: 'pre-line', marginBottom: '16px' }}>
                                    {(() => {
                                      // Parse LaTeX color commands into React elements
                                      const colorMap = {
                                        'blueE': '#3b82f6',
                                        'maroonD': '#b91c5c',
                                        'goldE': '#d97706',
                                        'redD': '#ef4444',
                                        'greenD': '#10b981',
                                      };
                                      const text = currentStep.text;
                                      // Split on $...$ math segments
                                      const parts = text.split(/(\$[^$]+\$)/g);
                                      return parts.map((part, i) => {
                                        if (!part.startsWith('$')) return <span key={i}>{part}</span>;
                                        // Strip $ delimiters
                                        let inner = part.slice(1, -1);
                                        // Process \frac FIRST so nested braces don't break color commands
                                        inner = inner.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '$1/$2');
                                        // Replace color commands with styled spans
                                        let hasColor = false;
                                        for (const [cmd, color] of Object.entries(colorMap)) {
                                          const regex = new RegExp(`\\\\${cmd}\\{([^}]+)\\}`, 'g');
                                          if (regex.test(inner)) {
                                            hasColor = true;
                                            inner = inner.replace(new RegExp(`\\\\${cmd}\\{([^}]+)\\}`, 'g'), `<c:${color}>$1</c>`);
                                          }
                                        }
                                        // Remove remaining LaTeX commands
                                        inner = inner.replace(/\\Large/g, '')
                                                     .replace(/\\\w+\{([^}]+)\}/g, '$1')
                                                     .replace(/\{|\}/g, '')
                                                     .trim();
                                        if (hasColor) {
                                          // Parse our color markers into spans
                                          const colorParts = inner.split(/(<c:[^>]+>[^<]*<\/c>)/g);
                                          return <span key={i} style={{ fontWeight: 700, fontFamily: 'monospace', fontSize: '18px' }}>
                                            {colorParts.map((cp, j) => {
                                              const match = cp.match(/<c:([^>]+)>([^<]*)<\/c>/);
                                              if (match) return <span key={j} style={{ color: match[1], fontWeight: 800 }}>{match[2]}</span>;
                                              return <span key={j}>{cp}</span>;
                                            })}
                                          </span>;
                                        }
                                        return <span key={i} style={{ fontWeight: 700, fontFamily: 'monospace', fontSize: '18px' }}>{inner}</span>;
                                      });
                                    })()}
                                  </div>
  
                                  {/* Visual rendering */}
                                  {currentStep.visual_type && currentStep.visual_params && (() => {
                                    const vt = currentStep.visual_type;
                                    const vp = currentStep.visual_params;
  
                                    // NumberLine renderer
                                    if (vt === 'NumberLine') {
                                      const start = vp.start || 0;
                                      const end = vp.end || 20;
                                      const range = end - start;
                                      const ticks = [];
                                      const step = range <= 20 ? 1 : Math.ceil(range / 20);
                                      for (let n = start; n <= end; n += step) ticks.push(n);
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ position: 'relative', height: '60px', margin: '10px 20px' }}>
                                            {/* Main line */}
                                            <div style={{ position: 'absolute', top: '30px', left: 0, right: 0, height: '3px', background: 'rgba(255,255,255,0.3)', borderRadius: '2px' }} />
                                            {/* Ticks and labels */}
                                            {ticks.map(n => {
                                              const pct = ((n - start) / range) * 100;
                                              const isMarker = (vp.markers || []).includes(n);
                                              const isHighlight = vp.highlight === n;
                                              const isHopTo = vp.hop_to === n;
                                              const isHopEnd = vp.hop_from !== undefined && vp.hop_by !== undefined && n === vp.hop_from + vp.hop_by;
                                              return (
                                                <div key={n} style={{ position: 'absolute', left: `${pct}%`, transform: 'translateX(-50%)' }}>
                                                  <div style={{ width: '2px', height: isHighlight || isHopTo || isMarker || isHopEnd ? '16px' : '10px', background: isHighlight ? '#d97706' : isHopEnd ? '#d97706' : isHopTo ? '#3b82f6' : isMarker ? '#3b82f6' : 'rgba(255,255,255,0.3)', margin: '0 auto', marginTop: isHighlight || isHopTo || isMarker || isHopEnd ? '22px' : '25px' }} />
                                                  <div style={{ fontSize: isHighlight || isHopTo || isMarker || isHopEnd ? '13px' : '10px', fontWeight: isHighlight || isHopTo || isMarker || isHopEnd ? 800 : 400, color: isHighlight ? '#d97706' : isHopEnd ? '#d97706' : isHopTo ? '#3b82f6' : isMarker ? '#3b82f6' : 'hsl(var(--text-muted))', textAlign: 'center', marginTop: '4px' }}>{n}</div>
                                                </div>
                                              );
                                            })}
                                     // Hop arc — handles both hop_from+hop_by and hop_to (jump from 0)
                                             {(vp.hop_from !== undefined && vp.hop_by !== undefined || vp.hop_to !== undefined) && (() => {
                                               const hopFrom = vp.hop_from !== undefined ? vp.hop_from : 0;
                                               const hopBy = vp.hop_by !== undefined ? vp.hop_by : vp.hop_to;
                                               const fromPct = ((hopFrom - start) / range) * 100;
                                               const toPct = (((hopFrom + hopBy) - start) / range) * 100;
                                              const left = Math.min(fromPct, toPct);
                                              const width = Math.abs(toPct - fromPct);
                                              return (
                                                <div style={{ position: 'absolute', left: `${left}%`, width: `${width}%`, top: '5px', height: '20px', borderBottom: '3px solid #b91c5c', borderLeft: '3px solid #b91c5c', borderRight: '3px solid #b91c5c', borderRadius: '0 0 50% 50%' }}>
                                                  <div style={{ position: 'absolute', right: vp.hop_by > 0 ? '-6px' : 'auto', left: vp.hop_by < 0 ? '-6px' : 'auto', bottom: '-3px', fontSize: '10px', color: '#b91c5c' }}>+{Math.abs(vp.hop_by)}</div>
                                                </div>
                                              );
                                            })()}
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // TenFrame renderer
                                    if (vt === 'TenFrame') {
                                      const filled = vp.filled || 0;
                                      const total = vp.total || 10;
                                      const colorSplit = vp.color_split || filled;
                                      const highlightEmpty = vp.highlight_empty;
                                      const cells = [];
                                      for (let i = 0; i < total; i++) {
                                        const isFilled = i < filled;
                                        const isFirstColor = i < colorSplit;
                                        const isEmpty = !isFilled && highlightEmpty;
                                        cells.push(
                                          <div key={i} style={{
                                            width: '36px', height: '36px', borderRadius: '50%',
                                            border: `2px solid ${isFilled ? (isFirstColor ? '#3b82f6' : '#b91c5c') : isEmpty ? '#ef4444' : 'rgba(255,255,255,0.15)'}`,
                                            background: isFilled ? (isFirstColor ? 'rgba(59,130,246,0.3)' : 'rgba(185,28,92,0.3)') : isEmpty ? 'rgba(239,68,68,0.1)' : 'transparent',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '10px', color: 'hsl(var(--text-muted))',
                                          }}>
                                            {isFilled ? '\u25CF' : isEmpty ? '?' : ''}
                                          </div>
                                        );
                                      }
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 36px)', gap: '6px', justifyContent: 'center' }}>
                                            {cells}
                                          </div>
                                          {vp.empty_count !== undefined && <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '13px', color: '#ef4444', fontWeight: 700 }}>{vp.empty_count} empty</div>}
                                        </div>
                                      );
                                    }
  
                                    // NumberBond renderer
                                    if (vt === 'NumberBond') {
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <svg width="180" height="120" viewBox="0 0 180 120" style={{ overflow: 'visible' }}>
                                            {/* Lines edge-to-edge (not center-to-center) */}
                                            <line x1="78.3" y1="43.7" x2="55.6" y2="80" stroke="#6366f1" strokeWidth="2" />
                                            <line x1="101.7" y1="43.7" x2="124.4" y2="80" stroke="#6366f1" strokeWidth="2" />
                                            {/* Whole (top) */}
                                            <circle cx="90" cy="25" r="22" fill="transparent" stroke="#3b82f6" strokeWidth="2.5" />
                                            <text x="90" y="31" textAnchor="middle" fill="#3b82f6" fontSize="20" fontWeight="800">{vp.whole}</text>
                                            {/* Part1 (bottom-left) */}
                                            <circle cx="45" cy="97" r="20" fill="transparent" stroke="#10b981" strokeWidth="2.5" />
                                            <text x="45" y="103" textAnchor="middle" fill={vp.parts[0] !== null ? '#10b981' : 'rgba(255,255,255,0.3)'} fontSize="18" fontWeight="700">{vp.parts[0] !== null ? vp.parts[0] : '?'}</text>
                                            {/* Part2 (bottom-right) */}
                                            <circle cx="135" cy="97" r="20" fill="transparent" stroke="#b91c5c" strokeWidth="2.5" />
                                            <text x="135" y="103" textAnchor="middle" fill={vp.parts[1] !== null ? '#b91c5c' : 'rgba(255,255,255,0.3)'} fontSize="18" fontWeight="700">{vp.parts[1] !== null ? vp.parts[1] : '?'}</text>
                                          </svg>
                                        </div>
                                      );
                                    }
  
                                    // ObjectGroup / ObjectGrid renderer
  if (vt === 'ObjectGroup' || vt === 'ObjectGrid') {
                                        // Handle 'groups' array format (used for commutative property)
                                        if (vp.groups && Array.isArray(vp.groups)) {
                                          return (
                                            <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                              <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', alignItems: 'center', flexWrap: 'wrap' }}>
                                                {vp.groups.map((group, gIdx) => {
                                                  const gColor = group.color === 'maroon' ? '#b91c5c' : group.color === 'blue' ? '#3b82f6' : '#06b6d4';
                                                  const gBg = group.color === 'maroon' ? 'rgba(185,28,92,0.25)' : group.color === 'blue' ? 'rgba(59,130,246,0.25)' : 'rgba(6,182,212,0.25)';
                                                  return (
                                                    <div key={gIdx} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                                                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', justifyContent: 'center', maxWidth: '150px' }}>
                                                        {Array.from({ length: Math.min(group.count, 20) }).map((_, i) => (
                                                          <div key={i} style={{
                                                            width: '24px', height: '24px', borderRadius: '4px',
                                                            background: gBg, border: `2px solid ${gColor}`,
                                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                            fontSize: '12px',
                                                          }}>
                                                            🔹
                                                          </div>
                                                        ))}
                                                      </div>
                                                      <div style={{ fontSize: '16px', fontWeight: 700, color: gColor }}>{group.count}</div>
                                                    </div>
                                                  );
                                                })}
                                                {vp.groups.length > 1 && (
                                                  <div style={{ fontSize: '18px', fontWeight: 700, color: '#d97706' }}>
                                                    = {vp.groups.reduce((sum, g) => sum + g.count, 0)}
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          );
                                        }
                                        
                                        const count = vp.count || 0;
                                        const adding = vp.adding;
                                        const obj = vp.object || 'item';
                                        const numbered = vp.numbered;
                                        const totalCount = adding !== undefined ? count + adding : count;
                                        const displayCount = adding !== undefined ? totalCount : count;
                                        
                                        // If no items to display, don't render anything
                                        if (displayCount <= 0) return null;
                                        
                                        // Comprehensive emoji mapping for objects by theme
                                        const emojiMap = {
                                          // Bible/Christianity
                                          'loaves of bread': '🍞', 'loaf': '🍞', 'bread': '🍞',
                                          'fish': '🐟', 'sheep': '🐑', 'coin': '🪙', 'coins': '🪙',
                                          'scroll': '📜', 'scrolls': '📜', 'lamp': '🪔', 'lamps': '🪔',
                                          'jar': '🏺', 'jars': '🏺', 'basket': '🧺', 'baskets': '🧺',
                                          'stone': '🪨', 'stones': '🪨', 'seed': '🌱', 'seeds': '🌱',
                                          // Gaming
                                          'headset': '🎧', 'headsets': '🎧',
                                          'controller': '🎮', 'controllers': '🎮',
                                          'trophy': '🏆', 'trophies': '🏆',
                                          'gem': '💎', 'gems': '💎', 'primogem': '💎', 'primogems': '💎',
                                          // Music/K-pop
                                          'album': '💿', 'albums': '💿',
                                          'photocard': '🖼️', 'photocards': '🖼️',
                                          'lightstick': '🔦', 'lightsticks': '🔦',
                                          'ticket': '🎫', 'tickets': '🎫', 'concert ticket': '🎫', 'concert tickets': '🎫',
                                          // Sports
                                          'basketball': '🏀', 'basketballs': '🏀',
                                          'volleyball': '🏐', 'volleyballs': '🏐',
                                          'ball': '⚽', 'balls': '⚽',
                                          'medal': '🥇', 'medals': '🥇',
                                          'jersey': '👕', 'jerseys': '👕',
                                          'sneaker': '👟', 'sneakers': '👟',
                                          'helmet': '⛑️', 'helmets': '⛑️',
                                          'bicycle': '🚲', 'bicycles': '🚲', 'bike': '🚲', 'bikes': '🚲',
                                          // Food/Baking
                                          'cupcake': '🧁', 'cupcakes': '🧁',
                                          'cookie': '🍪', 'cookies': '🍪',
                                          'egg': '🥚', 'eggs': '🥚',
                                          'milk tea': '🧋', 'milk tea cup': '🧋', 'milk tea cups': '🧋',
                                          // Pets
                                          'dog treat': '🦴', 'dog treats': '🦴',
                                          'cat toy': '🧶', 'cat toys': '🧶',
                                          'fish food': '🐠', 'fish food packet': '🐠', 'fish food packets': '🐠',
                                          // Arts/Crafts
                                          'crayon': '🖍️', 'crayons': '🖍️',
                                          'paintbrush': '🖌️', 'paintbrushes': '🖌️',
                                          'sketchpad': '📒', 'sketchpads': '📒',
                                          'yarn ball': '🧶', 'yarn balls': '🧶',
                                          'sticker': '⭐', 'stickers': '⭐', 'sticker sheet': '⭐', 'sticker sheets': '⭐',
                                          // Generic countables
                                          'star': '⭐', 'stars': '⭐',
                                          'heart': '❤️', 'hearts': '❤️',
                                          'apple': '🍎', 'apples': '🍎',
                                          'banana': '🍌', 'bananas': '🍌',
                                          'orange': '🍊', 'oranges': '🍊',
                                          'candy': '🍬', 'candies': '🍬',
                                          'flower': '🌸', 'flowers': '🌸',
                                          'book': '📚', 'books': '📚',
                                          'pencil': '✏️', 'pencils': '✏️',
                                          'pen': '🖊️', 'pens': '🖊️',
                                          'notebook': '📓', 'notebooks': '📓',
                                          'toy': '🧸', 'toys': '🧸',
                                          'car': '🚗', 'cars': '🚗',
                                          'block': '🧱', 'blocks': '🧱',
                                          'marble': '🔮', 'marbles': '🔮',
                                          'peso': '🪙', 'pesos': '🪙',
                                          'resin': '💧', // Genshin term
                                          'item': '📦', 'items': '📦',
                                        };
                                        // Try exact match, then try lowercase, then check for partial match
                                        let emoji = emojiMap[obj] || emojiMap[obj.toLowerCase()];
                                        if (!emoji) {
                                          // Try partial matching for compound objects
                                          const objLower = obj.toLowerCase();
                                          for (const [key, val] of Object.entries(emojiMap)) {
                                            if (objLower.includes(key) || key.includes(objLower)) {
                                              emoji = val;
                                              break;
                                            }
                                          }
                                        }
                                        // Fallback: use interest theme emoji if passed, otherwise default
                                        const themeEmoji = vp.theme_emoji || null;
                                        const displayEmoji = emoji || themeEmoji || '🔹';
                                        return (
                                          <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginBottom: '8px' }}>
                                              {Array.from({ length: Math.min(displayCount, 30) }).map((_, i) => (
                                                <div key={i} style={{
                                                  width: '32px', height: '32px', borderRadius: '6px',
                                                  background: adding !== undefined && i >= count ? 'rgba(185,28,92,0.3)' : 'rgba(59,130,246,0.25)',
                                                  border: `2px solid ${adding !== undefined && i >= count ? '#b91c5c' : '#3b82f6'}`,
                                                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                  fontSize: '18px',
                                                }}>
                                                  {numbered ? <span style={{ fontSize: '12px', fontWeight: 700 }}>{i + 1}</span> : displayEmoji}
                                                </div>
                                              ))}
                                            </div>
                                            <div style={{ textAlign: 'center', fontSize: '12px', color: 'hsl(var(--text-muted))' }}>
                                                {adding !== undefined ? (
                                                  <span>{count} <span style={{ color: '#3b82f6' }}>+</span> {adding} <span style={{ color: '#b91c5c' }}>=</span> {totalCount} {obj}</span>
                                                ) : (
                                                  <span>{displayCount} {obj}</span>
                                                )}
                                              </div>
                                          </div>
                                        );
                                      }
  
                                    // OrderedLine renderer
                                    if (vt === 'OrderedLine') {
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
                                            {(vp.items || []).map((item, i) => (
                                              <div key={i} style={{
                                                padding: '8px 14px', borderRadius: '8px',
                                                background: (vp.highlighted || []).includes(i) ? 'rgba(59,130,246,0.2)' : 'rgba(255,255,255,0.05)',
                                                border: `2px solid ${(vp.highlighted || []).includes(i) ? '#3b82f6' : 'rgba(255,255,255,0.1)'}`,
                                                fontSize: '13px', fontWeight: 600,
                                              }}>
                                                <span style={{ fontSize: '10px', color: '#d97706', marginRight: '6px' }}>{i + 1}.</span>{item}
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // NumberCards renderer
                                    if (vt === 'NumberCards') {
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                                            {(vp.numbers || []).map((n, i) => (
                                              <div key={i} style={{
                                                width: '48px', height: '48px', borderRadius: '10px',
                                                background: vp.ordered ? 'rgba(16,185,129,0.15)' : 'rgba(255,255,255,0.05)',
                                                border: `2px solid ${vp.ordered ? '#10b981' : 'rgba(255,255,255,0.15)'}`,
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontSize: '18px', fontWeight: 700,
                                              }}>
                                                {n}
                                              </div>
                                            ))}
                                          </div>
                                          {vp.ordered && <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '11px', color: '#10b981' }}>smallest to largest</div>}
                                        </div>
                                      );
                                    }
  
                                    // PlaceValueBlocks renderer — supports 1-4 digit numbers
                                    if (vt === 'PlaceValueBlocks') {
                                      const num = vp.number || vp.number_a || 0;
                                      const unitSize = 14;
                                      const thousands = Math.floor(num / 1000);
                                      const hundreds = Math.floor((num % 1000) / 100);
                                      const tens = Math.floor((num % 100) / 10);
                                      const ones = num % 10;
                                      const colorT = '#a78bfa'; // thousands - purple
                                      const colorH = '#10b981'; // hundreds - green
                                      const colorTen = '#3b82f6'; // tens - blue
                                      const colorO = '#b91c5c'; // ones - maroon
                                      const blockStyle = (color, w, h, label) => ({
                                        width: `${w}px`, height: `${h}px`,
                                        borderRadius: '3px', background: `${color}30`, border: `2px solid ${color}`,
                                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        fontSize: Math.min(10, h / 3) + 'px', color, fontWeight: 700, flexShrink: 0,
                                      });
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          {/* Legend */}
                                          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginBottom: '14px', flexWrap: 'wrap', fontSize: '11px' }}>
                                            {thousands > 0 && <span style={{ color: colorT }}>■ = 1000</span>}
                                            {hundreds > 0 && <span style={{ color: colorH }}>■ = 100</span>}
                                            <span style={{ color: colorTen }}>▮ = 10</span>
                                            <span style={{ color: colorO }}>• = 1</span>
                                          </div>
                                          {/* Blocks */}
                                          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', alignItems: 'flex-end', flexWrap: 'wrap', minHeight: `${unitSize * 10 + 10}px` }}>
                                            {thousands > 0 && Array.from({ length: Math.min(thousands, 9) }).map((_, i) => (
                                              <div key={`th${i}`} style={blockStyle(colorT, unitSize * 4, unitSize * 10, '1000')}>{unitSize * 10 > 40 ? '1000' : 'K'}</div>
                                            ))}
                                            {hundreds > 0 && Array.from({ length: Math.min(hundreds, 9) }).map((_, i) => (
                                              <div key={`h${i}`} style={blockStyle(colorH, unitSize * 3, unitSize * 8, '100')}>100</div>
                                            ))}
                                            {tens > 0 && Array.from({ length: Math.min(tens, 9) }).map((_, i) => (
                                              <div key={`t${i}`} style={blockStyle(colorTen, unitSize * 2, unitSize * 10, '10')}>10</div>
                                            ))}
                                            {ones > 0 && (
                                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px', maxWidth: `${unitSize * 5}px`, alignContent: 'flex-end' }}>
                                                {Array.from({ length: Math.min(ones, 9) }).map((_, i) => (
                                                  <div key={`o${i}`} style={blockStyle(colorO, unitSize, unitSize, '1')}>1</div>
                                                ))}
                                              </div>
                                            )}
                                          </div>
                                          <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '13px', fontWeight: 600, color: '#d97706' }}>
                                            {[thousands > 0 && `${thousands}×1000`, hundreds > 0 && `${hundreds}×100`, tens > 0 && `${tens}×10`, ones > 0 && `${ones}×1`].filter(Boolean).join(' + ')} = {num}
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // Comparison renderer — handles raw values OR nested visual objects
                                    if (vt === 'Comparison') {
                                      const renderSide = (side, color) => {
                                        if (typeof side === 'object' && side !== null && side.visual === 'FractionBar') {
                                          const parts = side.parts || 2;
                                          const shaded = side.shaded || 1;
                                          const barColor = color;
                                          return (
                                            <div style={{ textAlign: 'center' }}>
                                              <div style={{ display: 'flex', gap: '2px', marginBottom: '4px', width: '128px' }}>
                                                {Array.from({ length: parts }).map((_, i) => (
                                                  <div key={i} style={{
                                                    flex: 1, height: '28px', borderRadius: '3px',
                                                    background: i < shaded ? `${barColor}50` : 'rgba(255,255,255,0.05)',
                                                    border: `2px solid ${i < shaded ? barColor : 'rgba(255,255,255,0.15)'}`,
                                                  }} />
                                                ))}
                                              </div>
                                              <div style={{ fontSize: '14px', fontWeight: 700, color: barColor }}>{side.label || `${shaded}/${parts}`}</div>
                                            </div>
                                          );
                                        }
                                        return <div style={{ fontSize: '32px', fontWeight: 800, color }}>{typeof side === 'number' ? side.toLocaleString() : String(side)}</div>;
                                      };
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '24px' }}>
                                            {renderSide(vp.left, '#3b82f6')}
                                            <div style={{ fontSize: '18px', color: 'hsl(var(--text-muted))' }}>vs</div>
                                            {renderSide(vp.right, '#b91c5c')}
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // SkipCountLine renderer
                                    if (vt === 'SkipCountLine') {
                                      const slStart = vp.start || 0;
                                      const slEnd = vp.end || 100;
                                      const slStep = vp.step || 1;
                                      const slHighlight = vp.highlight || [];
                                      const slFrom = vp.from || slStart;
                                      const slRange = slEnd - slStart;
                                      // Show every step-th number, max ~12 labels
                                      const allStepTicks = [];
                                      for (let n = Math.ceil(slStart / slStep) * slStep; n <= slEnd; n += slStep) allStepTicks.push(n);
                                      const labelEvery = Math.ceil(allStepTicks.length / 12);
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ position: 'relative', height: '60px', margin: '10px 20px' }}>
                                            <div style={{ position: 'absolute', top: '30px', left: 0, right: 0, height: '3px', background: 'rgba(255,255,255,0.2)', borderRadius: '2px' }} />
                                            {allStepTicks.map((n, idx) => {
                                              const pct = ((n - slStart) / slRange) * 100;
                                              const isHl = slHighlight.includes(n);
                                              const showLabel = idx % labelEvery === 0 || isHl;
                                              return (
                                                <div key={n} style={{ position: 'absolute', left: `${pct}%`, transform: 'translateX(-50%)' }}>
                                                  <div style={{ width: '2px', height: isHl ? '18px' : '10px', background: isHl ? '#d97706' : 'rgba(255,255,255,0.3)', margin: '0 auto', marginTop: isHl ? '21px' : '25px' }} />
                                                  {showLabel && <div style={{ fontSize: isHl ? '12px' : '10px', fontWeight: isHl ? 800 : 400, color: isHl ? '#d97706' : 'hsl(var(--text-muted))', textAlign: 'center', marginTop: '4px', whiteSpace: 'nowrap' }}>{n}</div>}
                                                </div>
                                              );
                                            })}
                                          </div>
                                          <div style={{ textAlign: 'center', fontSize: '12px', color: 'hsl(var(--text-muted))', marginTop: '4px' }}>
                                            Counting by {slStep}s
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // FractionBar renderer
                                    if (vt === 'FractionBar') {
                                      const fbParts = vp.parts || 2;
                                      const fbShaded = vp.shaded || 0;
                                      const fbLabel = vp.label || '';
                                      const allowOverflow = vp.allow_overflow;
                                      // Handle improper fractions — show multiple full bars + remainder
                                      const fullBars = allowOverflow ? Math.floor(fbShaded / fbParts) : 0;
                                      const remainder = fbShaded % fbParts;
                                      const renderBar = (shaded, key, isPartial = false) => (
                                        <div key={key} style={{ marginBottom: '8px' }}>
                                          <div style={{ display: 'flex', gap: '3px' }}>
                                            {Array.from({ length: fbParts }).map((_, i) => (
                                              <div key={i} style={{
                                                flex: 1, height: '36px', borderRadius: '4px',
                                                background: i < shaded ? 'rgba(217,119,6,0.4)' : 'rgba(255,255,255,0.05)',
                                                border: `2px solid ${i < shaded ? '#d97706' : 'rgba(255,255,255,0.15)'}`,
                                              }} />
                                            ))}
                                          </div>
                                          {isPartial && <div style={{ fontSize: '10px', color: '#d97706', textAlign: 'right', marginTop: '2px' }}>partial</div>}
                                        </div>
                                      );
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', maxWidth: '320px', margin: '0 auto' }}>
                                          {Array.from({ length: fullBars }).map((_, i) => renderBar(fbParts, `full${i}`))}
                                          {(remainder > 0 || fullBars === 0) && renderBar(remainder || fbShaded, 'rem', fullBars > 0 && remainder > 0)}
                                          <div style={{ textAlign: 'center', marginTop: '8px', fontSize: '16px', fontWeight: 700, color: '#d97706' }}>{fbLabel || `${fbShaded}/${fbParts}`}</div>
                                        </div>
                                      );
                                    }
  
                                    // PatternRow renderer
                                    if (vt === 'PatternRow') {
                                      const prItems = vp.items || [];
                                      const prUnitLen = vp.highlight_unit;
                                      const patternColors = ['#3b82f6', '#b91c5c', '#10b981', '#d97706', '#a78bfa'];
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', flexWrap: 'wrap' }}>
                                            {prItems.map((item, i) => {
                                              const colorIdx = prUnitLen ? i % prUnitLen : i % patternColors.length;
                                              const isUnit = prUnitLen && i < prUnitLen;
                                              const c = patternColors[colorIdx];
                                              return (
                                                <div key={i} style={{
                                                  padding: '8px 14px', borderRadius: '8px', minWidth: '36px', textAlign: 'center',
                                                  background: `${c}20`, border: `2px solid ${isUnit ? c : `${c}60`}`,
                                                  fontSize: '15px', fontWeight: 700, color: c,
                                                }}>{item}</div>
                                              );
                                            })}
                                          </div>
                                          {prUnitLen && <div style={{ textAlign: 'center', fontSize: '11px', color: 'hsl(var(--text-muted))', marginTop: '8px' }}>unit: first {prUnitLen} items repeat</div>}
                                        </div>
                                      );
                                    }
  
                                    // ShapeDisplay renderer — draws 2D shapes using SVG
                                    if (vt === 'ShapeDisplay') {
                                      const shapeList = vp.shapes || [];
                                      const showLabels = vp.show_labels;
                                      const shapeColors = { triangle: '#3b82f6', rectangle: '#10b981', square: '#d97706', circle: '#b91c5c', half_circle: '#b91c5c', quarter_circle: '#a78bfa', cube: '#06b6d4', cylinder: '#f97316' };
                                      const renderShape = (shape, idx) => {
                                        const c = shapeColors[shape] || '#06b6d4';
                                        const s = 60;
                                        let svgContent;
                                        if (shape === 'triangle') svgContent = <polygon points={`${s/2},4 4,${s-4} ${s-4},${s-4}`} fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        else if (shape === 'square') svgContent = <rect x="4" y="4" width={s-8} height={s-8} rx="3" fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        else if (shape === 'rectangle') svgContent = <rect x="2" y="14" width={s-4} height={s-28} rx="3" fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        else if (shape === 'circle') svgContent = <circle cx={s/2} cy={s/2} r={s/2-4} fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        else if (shape === 'half_circle') svgContent = <path d={`M 4 ${s/2} A ${s/2-4} ${s/2-4} 0 0 1 ${s-4} ${s/2} Z`} fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        else if (shape === 'quarter_circle') svgContent = <path d={`M 4 ${s-4} A ${s-8} ${s-8} 0 0 1 ${s-4} 4 L 4 4 Z`} fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        else svgContent = <rect x="4" y="4" width={s-8} height={s-8} rx="3" fill={`${c}30`} stroke={c} strokeWidth="2.5"/>;
                                        return (
                                          <div key={idx} style={{ textAlign: 'center' }}>
                                            <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`}>{svgContent}</svg>
                                            {showLabels && <div style={{ fontSize: '11px', color: c, fontWeight: 600, marginTop: '4px', textTransform: 'capitalize' }}>{shape.replace('_', ' ')}</div>}
                                          </div>

  );
}
