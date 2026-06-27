import QuestionRenderer from '../components/QuestionRenderer';
import React from 'react';
import { Play, BookOpen, Shield, RefreshCw, Zap, Maximize2, Minimize2, Check, ExternalLink, ChevronRight, Share2, Upload, Terminal, BookMarked, User, Cpu, Award, MessageSquare, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import ReactFlow, { Background, Controls } from 'reactflow';
import 'reactflow/dist/style.css';
import { DndContext, closestCenter } from '@dnd-kit/core';
import { SortableContext, horizontalListSortingStrategy } from '@dnd-kit/sortable';

import { renderMath } from '../utils/mathUtils';
import { renderVisualInner } from '../utils/renderUtils';
import { SortOrderInteractive } from '../components/VisualSkeletons';

export default function PracticeView(props) {

  const {
    practiceViewType, setPracticeViewType, setSubject, setCurrentView,
    activeQuestion, isSubmitting, practiceVisualAnswer, setPracticeVisualAnswer,
    handleAnswerSubmit, showFeedback,
    isCorrect, isGenerating, activeFeedback, socraticActive,
    chatMessages, setChatMessages, sendingChat, setSendingChat,
    selectedStudent, socraticAbortControllerRef, API_BASE,
    renderMapOverlay,
    handleGeneratePractice, showSolution, isSolutionVisible, 
    handleNodeClick, handleNextQuestion, handleParentLogin,
    setSelectedStudent, setSocraticActive, renderIntroViewer, setShowFlagModal,
    studentInterestInput, setStudentInterestInput, interestSaveStatus, setInterestSaveStatus, handleSaveInterests, setSelectedSubject, fetchMatatagTracks, fetchMatatagNodes, matatagNodes, loadingMathTracks, mathTracks, setSelectedSubdomain, setQuestionQueue, fetchNextQuestion, selectedSubject, loadingVerbalTracks, verbalTracks, loadingMatatagTracks, selectedRoadmapNode, setSelectedRoadmapNode, fetchIntroForStudent, writingCoachActive, introContent, handleLogout, loadingQuestion, aiBackend, opencodeModel, handleSkipPlacement, tabSwitchCount, idleSeconds, guessCount, answerResult, handleOptionClick, chatEndRef, handleSendMessage, chatInput, setChatInput, selectedSubdomain
  } = props;

  return (
    <>
      {
          practiceViewType === 'subject_selection' ? (
            <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '40px 20px' }}>
              {/* Header block */}
              <div style={{ textAlign: 'center', marginBottom: '50px' }}>
                <h1 style={{ fontSize: '38px', fontWeight: 800, color: '#f8fafc', marginBottom: '12px', background: 'linear-gradient(135deg, #fff 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  Choose Your Learning Track
                </h1>
                <p style={{ fontSize: '18px', color: 'hsl(var(--text-muted))', maxWidth: '600px', margin: '0 auto' }}>
                  Hello, <strong style={{ color: '#a78bfa' }}>{selectedStudent.name}</strong>! Which domain would you like to explore and master today?
                </p>
                <div style={{ marginTop: '20px', display: 'flex', gap: '15px', justifyContent: 'center' }}>
                  <span className="badge-status active" style={{ fontSize: '14px', padding: '6px 16px' }}>Grade Level: {selectedStudent.grade}</span>
                  <span className="badge-status mastered" style={{ fontSize: '14px', padding: '6px 16px', background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>Active ELO: {selectedStudent.elo_rating}</span>
                </div>
              </div>

              {/* Student interests panel */}
              <div style={{ maxWidth: '600px', margin: '0 auto 40px', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '16px', padding: '18px 20px' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: 'hsl(var(--text-muted))', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '12px' }}>
                  ✏️ Your Interests
                </div>

                {/* Input row */}
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '14px' }}>
                  <input
                    type="text"
                    value={studentInterestInput}
                    onChange={e => { setStudentInterestInput(e.target.value); setInterestSaveStatus(''); }}
                    onKeyDown={e => e.key === 'Enter' && handleSaveInterests()}
                    placeholder="e.g. Minecraft, dinosaurs, soccer..."
                    style={{ flex: 1, background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '8px 12px', color: '#f1f5f9', fontSize: '14px', outline: 'none' }}
                  />
                  <button
                    onClick={handleSaveInterests}
                    disabled={interestSaveStatus === 'saving'}
                    style={{
                      flexShrink: 0, padding: '8px 18px', borderRadius: '10px', border: 'none', cursor: 'pointer', fontSize: '13px', fontWeight: 700,
                      background: interestSaveStatus === 'saved' ? 'rgba(16,185,129,0.25)' : interestSaveStatus === 'error' ? 'rgba(239,68,68,0.2)' : 'rgba(139,92,246,0.3)',
                      color: interestSaveStatus === 'saved' ? '#34d399' : interestSaveStatus === 'error' ? '#f87171' : '#c084fc',
                      transition: 'all 0.2s'
                    }}
                  >
                    {interestSaveStatus === 'saved' ? '✓ Saved' : interestSaveStatus === 'saving' ? '...' : interestSaveStatus === 'error' ? '✗ Error' : 'Save'}
                  </button>
                </div>

                {/* Saved student interests as tags */}
                {selectedStudent.student_interest_tags && selectedStudent.student_interest_tags.trim() ? (
                  <div style={{ marginBottom: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', marginBottom: '6px' }}>Your saved topics:</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {selectedStudent.student_interest_tags.split(',').map(t => t.trim()).filter(Boolean).map((tag, i) => (
                        <span key={i} style={{ padding: '3px 10px', borderRadius: '20px', background: 'rgba(139,92,246,0.18)', color: '#c084fc', fontSize: '12px', fontWeight: 600, border: '1px solid rgba(139,92,246,0.25)' }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', marginBottom: '12px', fontStyle: 'italic' }}>
                    No extra interests saved yet — type above and press Save!
                  </div>
                )}

                {/* Parent-set interests (read-only) */}
                {selectedStudent.interest_tags && selectedStudent.interest_tags.trim() && (
                  <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', marginBottom: '6px' }}>Also included (set by parent):</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {selectedStudent.interest_tags.split(',').map(t => t.trim()).filter(Boolean).map((tag, i) => (
                        <span key={i} style={{ padding: '3px 10px', borderRadius: '20px', background: 'rgba(255,255,255,0.06)', color: 'hsl(var(--text-muted))', fontSize: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Subject Track Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '30px', marginBottom: '50px' }}>
                
                {/* 3. MATATAG (Philippine K-10 Math) CARD */}
                <div 
                  className="glass-card hover-glow"
                  onClick={() => {
                    setSelectedSubject('Matatag');
                    setPracticeViewType('matatag_track_selection');
                    fetchMatatagTracks(selectedStudent.id);
                    fetchMatatagNodes();
                  }}
                  style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '20px', padding: '30px', transition: 'all 0.3s ease', border: '1px solid rgba(245, 158, 11, 0.2)' }}
                >
                  <div style={{ width: '60px', height: '60px', borderRadius: '15px', background: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '30px', boxShadow: '0 8px 20px rgba(245, 158, 11, 0.3)' }}>
                    🇵🇭
                  </div>
                  <div>
                    <h3 style={{ fontSize: '22px', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>MATATAG Math</h3>
                    <p style={{ color: 'hsl(var(--text-muted))', fontSize: '14px', lineHeight: '1.5' }}>
                      Philippine K-10 curriculum with Number & Algebra, Measurement & Geometry, and Data & Probability.
                    </p>
                  </div>
                  <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '6px', color: '#fbbf24', fontWeight: 600, fontSize: '15px' }}>
                    <span>Launch Track 🚀</span>
                  </div>
                </div>

              </div>

              {/* Utility actions */}
              <div style={{ textAlign: 'center' }}>
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    setSelectedStudent(null);
                    setCurrentView('login');
                  }}
                  style={{ padding: '12px 30px', fontSize: '16px', borderRadius: '15px' }}
                >
                  🚪 Exit Profile & Logout
                </button>
              </div>
            </div>
          ) : practiceViewType === 'math_track_selection' ? (
            <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '40px 20px' }}>
              {/* Header block */}
              <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                <h1 style={{ fontSize: '38px', fontWeight: 800, color: '#f8fafc', marginBottom: '12px', background: 'linear-gradient(135deg, #fff 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  Select Math Study Domain
                </h1>
                <p style={{ fontSize: '18px', color: 'hsl(var(--text-muted))', maxWidth: '600px', margin: '0 auto' }}>
                  Hello, <strong style={{ color: '#a78bfa' }}>{selectedStudent.name}</strong>! Which of your active math pathways would you like to master today?
                </p>
              </div>

              {loadingMathTracks ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '100px', gap: '20px' }}>
                  <RefreshCw className="w-12 h-12 animate-spin" style={{ animation: 'spin 2s linear infinite', color: '#8b5cf6' }} />
                  <p style={{ color: 'hsl(var(--text-muted))' }}>Discovering parallel learning tracks for Grade {selectedStudent.grade === 0 ? 'Kindergarten' : selectedStudent.grade === 13 ? '13' : selectedStudent.grade}...</p>
                </div>
              ) : (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '25px', marginBottom: '40px' }}>
                    {mathTracks.map(track => {
                      const totalNodes = track.nodes.length;
                      const masteredNodes = track.nodes.filter(n => n.status === 'mastered').length;
                      const activeNodes = track.nodes.filter(n => n.status === 'active').length;
                      const completionPct = totalNodes > 0 ? Math.round((masteredNodes / totalNodes) * 100) : 0;
                      
                      return (
                        <div 
                          key={track.key}
                          className="glass-card hover-glow"
                          onClick={() => {
                            setSelectedSubdomain(track.key);
                            setPracticeViewType('workspace');
                            setQuestionQueue([]); // Clear queue when switching subdomains
                            fetchNextQuestion(selectedStudent.id, selectedSubject, track.key, true);
                          }}
                          style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '15px', padding: '25px', transition: 'all 0.3s ease', border: `1px solid ${track.color}44` }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ width: '45px', height: '45px', borderRadius: '10px', background: `linear-gradient(135deg, ${track.color} 0%, #1e1b4b 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                              🧮
                            </div>
                            <span className="badge-status active" style={{ background: `${track.color}22`, color: track.color, border: `1px solid ${track.color}44` }}>
                              {track.key}
                            </span>
                          </div>
                          <div>
                            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                              {track.title.replace('🧮 Math: ', '')}
                            </h3>
                            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '13px', lineHeight: '1.4' }}>
                              Track contains {totalNodes} dynamic standards tailored for your level.
                            </p>
                          </div>
                          
                          {/* Mini progress bar */}
                          <div style={{ marginTop: 'auto', paddingTop: '10px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>
                              <span>Mastery progress</span>
                              <strong>{completionPct}%</strong>
                            </div>
                            <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${completionPct}%`, background: track.color, transition: 'width 0.5s ease' }} />
                            </div>
                            <div style={{ display: 'flex', gap: '10px', marginTop: '8px', fontSize: '11px' }}>
                              <span style={{ color: '#10b981' }}>● {masteredNodes} Mastered</span>
                              <span style={{ color: '#60a5fa' }}>● {activeNodes} Active</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div style={{ textAlign: 'center' }}>
                    <button 
                      className="btn-secondary" 
                      onClick={() => {
                        setPracticeViewType('subject_selection');
                        setSelectedSubdomain(null);
                      }}
                      style={{ padding: '12px 30px', fontSize: '16px', borderRadius: '15px' }}
                    >
                      ← Back to Subjects
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : practiceViewType === 'verbal_track_selection' ? (
            <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '40px 20px' }}>
              {/* Header block */}
              <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                <h1 style={{ fontSize: '38px', fontWeight: 800, color: '#f8fafc', marginBottom: '12px', background: 'linear-gradient(135deg, #fff 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  Select Verbal Study Domain
                </h1>
                <p style={{ fontSize: '18px', color: 'hsl(var(--text-muted))', maxWidth: '600px', margin: '0 auto' }}>
                  Hello, <strong style={{ color: '#34d399' }}>{selectedStudent.name}</strong>! Which of your active ELA pathways would you like to master today?
                </p>
              </div>

              {loadingVerbalTracks ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '100px', gap: '20px' }}>
                  <RefreshCw className="w-12 h-12 animate-spin" style={{ animation: 'spin 2s linear infinite', color: '#34d399' }} />
                  <p style={{ color: 'hsl(var(--text-muted))' }}>Discovering parallel learning tracks for Grade {selectedStudent.grade === 0 ? 'Kindergarten' : selectedStudent.grade === 13 ? '13' : selectedStudent.grade}...</p>
                </div>
              ) : (
                <>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '25px', marginBottom: '40px' }}>
                    {verbalTracks.map(track => {
                      const totalNodes = track.nodes.length;
                      const masteredNodes = track.nodes.filter(n => n.status === 'mastered').length;
                      const activeNodes = track.nodes.filter(n => n.status === 'active').length;
                      const completionPct = totalNodes > 0 ? Math.round((masteredNodes / totalNodes) * 100) : 0;
                      
                      // Map emoji/icon based on the track key/subject
                      let emoji = '📚';
                      if (track.key.includes('RL')) emoji = '📖';
                      else if (track.key.includes('RI')) emoji = '📰';
                      else if (track.key.includes('RF')) emoji = '🧩';
                      else if (track.key.includes('SL')) emoji = '🗣️';
                      else if (track.key.includes('W')) emoji = '✍️';
                      else if (track.key.includes('L')) emoji = '✨';

                      // Overwrite titles and descriptions with child-friendly, high-precision educational names and distinct definitions
                      let displayTitle = '';
                      let displayKey = '';
                      let description = '';
                      
                      if (track.key.includes('RL')) {
                        displayTitle = 'Reading Stories & Literature';
                        displayKey = 'Fiction Analysis';
                        description = 'Analyze plot, setting, character perspectives, themes, and metaphors in stories, plays, and poetry.';
                      } else if (track.key.includes('RI')) {
                        displayTitle = 'Reading Articles & Non-Fiction';
                        displayKey = 'Non-Fiction Analysis';
                        description = 'Evaluate articles, historical documents, scientific texts, structural layouts, and support evidence.';
                      } else if (track.key.includes('RF')) {
                        displayTitle = 'Phonics & Reading Mechanics';
                        displayKey = 'Phonics & Fluency';
                        description = 'Master alphabet blends, sight-word decoding, syllable divisions, and pronunciation rules.';
                      } else if (track.key.includes('SL')) {
                        displayTitle = 'Listening & Speech Comprehension';
                        displayKey = 'Oral Communication';
                        description = 'Develop audio comprehension, collaborative conversation, and presentation structure mastery.';
                      } else if (track.key.includes('W')) {
                        displayTitle = 'Creative Writing & Essays';
                        displayKey = 'Writing & Essays';
                        description = 'Build clear writing habits for thesis arguments, multi-paragraph essays, narrative tales, and research papers.';
                      } else if (track.key.includes('L')) {
                        displayTitle = 'Grammar, Vocab & Conventions';
                        displayKey = 'Grammar & Conventions';
                        description = 'Master vocabulary contextual clues, spelling guidelines, punctuation, capitalization, and standard grammar rules.';
                      } else {
                        displayTitle = track.title.replace(/.*ELA: /, '');
                        displayKey = track.key.replace('ELA_', '');
                        description = `Targeted academic curriculum covering ${displayTitle} level mastery.`;
                      }

                      return (
                        <div 
                          key={track.key}
                          className="glass-card hover-glow"
                          onClick={() => {
                            setSelectedSubject('Verbal');
                            setSelectedSubdomain(track.key);
                            setPracticeViewType('workspace');
                            setQuestionQueue([]); // Clear queue when switching subdomains
                            fetchNextQuestion(selectedStudent.id, 'Verbal', null, true);
                          }}
                          style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '15px', padding: '25px', transition: 'all 0.3s ease', border: `1px solid ${track.color}44` }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ width: '45px', height: '45px', borderRadius: '10px', background: `linear-gradient(135deg, ${track.color} 0%, #1e1b4b 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                              {emoji}
                            </div>
                            <span className="badge-status active" style={{ background: `${track.color}22`, color: track.color, border: `1px solid ${track.color}44`, fontSize: '11px' }}>
                              {displayKey}
                            </span>
                          </div>
                          <div>
                            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                              {displayTitle}
                            </h3>
                            <p style={{ color: 'hsl(var(--text-muted))', fontSize: '13px', lineHeight: '1.4' }}>
                              {description}
                            </p>
                          </div>
                          
                          {/* Mini progress bar */}
                          <div style={{ marginTop: 'auto', paddingTop: '10px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>
                              <span>Mastery progress</span>
                              <strong>{completionPct}%</strong>
                            </div>
                            <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${completionPct}%`, background: track.color, transition: 'width 0.5s ease' }} />
                            </div>
                            <div style={{ display: 'flex', gap: '10px', marginTop: '8px', fontSize: '11px' }}>
                              <span style={{ color: '#10b981' }}>● {masteredNodes} Mastered</span>
                              <span style={{ color: '#60a5fa' }}>● {activeNodes} Active</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div style={{ textAlign: 'center' }}>
                    <button 
                      className="btn-secondary" 
                      onClick={() => {
                        setPracticeViewType('subject_selection');
                        setSelectedSubdomain(null);
                      }}
                      style={{ padding: '12px 30px', fontSize: '16px', borderRadius: '15px' }}
                    >
                      ← Back to Subjects
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : practiceViewType === 'matatag_track_selection' ? (
            <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '40px 20px' }}>
              {/* Header block */}
              <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                <h1 style={{ fontSize: '38px', fontWeight: 800, color: '#f8fafc', marginBottom: '12px', background: 'linear-gradient(135deg, #fff 0%, #cbd5e1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                  Select MATATAG Content Area
                </h1>
                <p style={{ fontSize: '18px', color: 'hsl(var(--text-muted))', maxWidth: '600px', margin: '0 auto' }}>
                  Hello, <strong style={{ color: '#fbbf24' }}>{selectedStudent.name}</strong>! Choose a MATATAG content area to practice.
                </p>
              </div>

              {loadingMatatagTracks ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '100px', gap: '20px' }}>
                  <RefreshCw className="w-12 h-12 animate-spin" style={{ animation: 'spin 2s linear infinite', color: '#f59e0b' }} />
                  <p style={{ color: 'hsl(var(--text-muted))' }}>Loading MATATAG content areas for Grade {selectedStudent.grade === 0 ? 'Kindergarten' : selectedStudent.grade}...</p>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '40px', marginBottom: '40px' }}>
                    {[
                      { key: 'NA', title: 'Number and Algebra', emoji: '🔢', color: '#8b5cf6' },
                      { key: 'MG', title: 'Measurement and Geometry', emoji: '📐', color: '#f59e0b' },
                      { key: 'DP', title: 'Data and Probability', emoji: '📊', color: '#10b981' }
                    ].map(domain => {
                      // Filter nodes for this subdomain (show all grades)
                      const nodesInDomain = matatagNodes.filter(n => n.branch && n.branch.toUpperCase() === domain.key);
                      if (nodesInDomain.length === 0) return null;

                      return (
                        <div key={domain.key} className="glass-card" style={{ padding: '24px', border: `1px solid ${domain.color}44` }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `linear-gradient(135deg, ${domain.color} 0%, #1e1b4b 100%)`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
                              {domain.emoji}
                            </div>
                            <h3 style={{ fontSize: '22px', fontWeight: 700, color: '#f8fafc', margin: 0 }}>{domain.title}</h3>
                          </div>

                          {/* Horizontal scroll container for the roadmap nodes */}
                          <div style={{ display: 'flex', gap: '16px', overflowX: 'auto', paddingBottom: '16px', scrollbarWidth: 'thin' }}>
                            {nodesInDomain.map(node => (
                              <div
                                key={node.node_id}
                                onClick={() => setSelectedRoadmapNode(node)}
                                className="hover-glow"
                                style={{ 
                                  minWidth: '220px', 
                                  maxWidth: '220px', 
                                  padding: '16px', 
                                  background: 'rgba(0,0,0,0.3)', 
                                  borderRadius: '12px', 
                                  cursor: 'pointer',
                                  border: `1px solid ${domain.color}33`,
                                  transition: 'all 0.2s'
                                }}
                              >
                                <div style={{ fontSize: '11px', color: domain.color, fontWeight: 700, marginBottom: '6px' }}>
                                  GRADE {node.grade} • Q{node.quarter}
                                </div>
                                <div style={{ fontSize: '14px', fontWeight: 600, color: '#fff', marginBottom: '8px', lineHeight: '1.3' }}>
                                  {node.primary_concept}
                                </div>
                                <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                                  {node.competency}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Modal for dual options when a roadmap node is clicked */}
                  {selectedRoadmapNode && (
                    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', backdropFilter: 'blur(4px)' }}>
                      <div className="glass-card animate-fade-in" style={{ width: '400px', padding: '30px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.1)' }}>
                        <div style={{ fontSize: '30px', marginBottom: '16px' }}>🎯</div>
                        <h2 style={{ fontSize: '20px', color: '#fff', marginBottom: '8px', fontWeight: 700 }}>{selectedRoadmapNode.primary_concept}</h2>
                        <p style={{ color: 'hsl(var(--text-muted))', fontSize: '13px', marginBottom: '24px', lineHeight: '1.4' }}>{selectedRoadmapNode.competency}</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                          <button 
                            className="btn-primary"
                            onClick={() => {
                                fetchIntroForStudent(selectedRoadmapNode.node_id);
                                setSelectedRoadmapNode(null);
                            }}
                            style={{ padding: '12px', background: '#3b82f6', border: 'none', fontSize: '15px' }}
                          >
                            📖 Read Intro
                          </button>
                          <button 
                            className="btn-primary"
                            onClick={() => {
                                setSelectedSubject('Matatag');
                                setSelectedSubdomain(selectedRoadmapNode.node_id);
                                setPracticeViewType('workspace');
                                setQuestionQueue([]);
                                fetchNextQuestion(selectedStudent.id, 'Matatag', selectedRoadmapNode.node_id, true);
                                setSelectedRoadmapNode(null);
                            }}
                            style={{ padding: '12px', background: '#10b981', border: 'none', fontSize: '15px' }}
                          >
                            ✏️ Start Practice
                          </button>
                          <button 
                            className="btn-secondary"
                            onClick={() => setSelectedRoadmapNode(null)}
                            style={{ padding: '12px', marginTop: '8px', fontSize: '14px' }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  <div style={{ textAlign: 'center' }}>
                    <button 
                      className="btn-secondary" 
                      onClick={() => {
                        setPracticeViewType('subject_selection');
                        setSelectedSubdomain(null);
                      }}
                      style={{ padding: '12px 30px', fontSize: '16px', borderRadius: '15px' }}
                    >
                      ← Back to Subjects
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: (socraticActive || writingCoachActive) ? '1.1fr 0.9fr' : '1fr', gap: '40px', transition: 'all 0.4s ease' }}>


            
            {/* Left side: Problem panel */}
            <div className="glass-card" style={{ border: practiceViewType === 'intro_viewer' ? 'none' : undefined, background: practiceViewType === 'intro_viewer' ? 'transparent' : undefined, boxShadow: practiceViewType === 'intro_viewer' ? 'none' : undefined, padding: practiceViewType === 'intro_viewer' ? 0 : undefined }}>
              {practiceViewType === 'intro_viewer' ? (
                <div>
                  {/* Status header for Intro Viewer */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px', background: 'rgba(255,255,255,0.03)', padding: '16px 24px', borderRadius: '15px', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className="badge-status mastered" style={{ 
                        background: 'rgba(6, 182, 212, 0.15)',
                        color: '#06b6d4',
                        border: '1px solid #0891b2',
                        padding: '8px 16px',
                        fontSize: '14px',
                        fontWeight: 700
                      }}>
                        📖 Intro Lesson: {selectedSubdomain || (introContent?.node_key) || 'Node Intro'}
                      </span>

                      <button 
                        className="btn-secondary" 
                        onClick={() => {
                          setPracticeViewType('subject_selection');
                          setSelectedSubdomain(null);
                        }}
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}
                      >
                        <span>🎒 Switch Subject / Back</span>
                      </button>
                      
                      {/* Manual Socratic Tutor toggle button */}
                      <button 
                        className="btn-secondary" 
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
                                skill_id:       activeQuestion?.skill_id || '',
                                question_text:  activeQuestion?.stem || '',
                                student_answer: '',
                                is_intro:       false,
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
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: socraticActive ? 'rgba(139,92,246,0.25)' : 'rgba(139,92,246,0.1)', border: `1px solid ${socraticActive ? 'rgba(139,92,246,0.6)' : 'rgba(139,92,246,0.3)'}` }}
                      >
                        <MessageSquare className="w-4 h-4 text-purple-400" style={{ color: '#c084fc' }} />
                        <span>💡 {socraticActive ? 'Close Tutor' : 'Ask Tutor'}</span>
                      </button>

                      {/* Exit to Home button */}
                      <button 
                        className="btn-secondary" 
                        onClick={handleLogout}
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: 'rgba(107, 114, 128, 0.15)', color: '#9ca3af', border: '1px solid rgba(107, 114, 128, 0.3)' }}
                      >
                        <span>🚪 Exit to Home</span>
                      </button>
                    </div>
                  </div>
                  {renderIntroViewer()}
                </div>
              ) : loadingQuestion ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '80px', gap: '20px' }}>
                  <RefreshCw className="w-12 h-12 animate-spin" style={{ animation: 'spin 2s linear infinite', color: 'hsl(var(--secondary))' }} />
                  <p style={{ color: 'hsl(var(--text-muted))' }}>
                    Gemini is generating your personalized learning experience...
                  </p>
                </div>
              ) : activeQuestion ? (
                <div>
                  {/* Status header */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                      <span className={`badge-status ${activeQuestion.is_placement ? 'active' : 'mastered'}`} style={{ 
                        background: activeQuestion.is_placement ? 'rgba(59, 130, 246, 0.2)' : 'rgba(16, 185, 129, 0.15)',
                        color: activeQuestion.is_placement ? '#60a5fa' : '#10b981',
                        border: activeQuestion.is_placement ? '1px solid #3b82f6' : '1px solid #059669',
                        padding: '8px 16px',
                        fontSize: '14px',
                        fontWeight: 700
                      }}>
                        {activeQuestion.is_placement ? `📍 PLACEMENT MODE: Question ${activeQuestion.placement_progress}/~10` : `🎯 Mastery Mode: ${activeQuestion.skill_id}`}
                      </span>

                      {activeQuestion.is_placement && (
                        <button 
                          className="btn-secondary" 
                          onClick={handleSkipPlacement}
                          style={{ padding: '6px 12px', fontSize: '12px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                        >
                          ⏩ Skip Placement
                        </button>
                      )}

                      {!activeQuestion.is_placement && (
                        <span className="badge-status mastered" style={{ background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc' }}>
                          Student ELO: {selectedStudent.elo_rating}
                        </span>
                      )}
                      
                      <button 
                        className="btn-secondary" 
                        onClick={() => {
                          setPracticeViewType('subject_selection');
                          setSelectedSubdomain(null);
                        }}
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}
                      >
                        <span>🎒 Switch Subject: {selectedSubject === 'Math' ? `Math (${selectedSubdomain})` : (selectedSubject === 'Verbal' ? 'Verbal Competency' : selectedSubject.replace('Reading: Literature', 'Stories & Literature').replace('Reading: Informational Text', 'Articles & Non-Fiction').replace('Reading Foundations', 'Phonics & Reading Basics').replace('Speaking & Listening', 'Listening & Speech').replace('Writing', 'Creative Writing & Essays').replace('Language', 'Grammar & Conventions'))}</span>
                      </button>
                      
                      {/* Manual Socratic Tutor toggle button */}
                      <button 
                        className="btn-secondary" 
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
                                skill_id:       activeQuestion?.skill_id || '',
                                question_text:  activeQuestion?.stem || '',
                                student_answer: '',
                                is_intro:       false,
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
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px' }}
                      >
                        <MessageSquare className="w-4 h-4 text-purple-400" style={{ color: '#c084fc' }} />
                        <span>💡 Ask Tutor</span>
                      </button>

                      {/* Flag Question button */}
                      <button 
                        className="btn-secondary" 
                        onClick={() => setShowFlagModal(true)}
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                      >
                        <AlertTriangle className="w-4 h-4" />
                        <span>🚩 Flag</span>
                      </button>

                      {/* Exit to Home button */}
                      <button 
                        className="btn-secondary" 
                        onClick={handleLogout}
                        style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: 'rgba(107, 114, 128, 0.15)', color: '#9ca3af', border: '1px solid rgba(107, 114, 128, 0.3)' }}
                      >
                        <span>🚪 Exit to Home</span>
                      </button>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', fontSize: '13px', color: 'hsl(var(--text-muted))' }}>
                      <span>Focus: {tabSwitchCount} tab-outs</span>
                      <span>Idle: {idleSeconds}s</span>
                      <span>Guesses: {guessCount}</span>
                    </div>
                  </div>

                  {/* Learning Competency Badge */}
                  {activeQuestion.standard_description && (
                    <div style={{ 
                      marginBottom: '20px',
                      padding: '12px 16px',
                      background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.1))',
                      borderRadius: '12px',
                      border: '1px solid rgba(139, 92, 246, 0.3)',
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '10px'
                    }}>
                      <span style={{ fontSize: '18px', flexShrink: 0 }}>📚</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: '#a78bfa', marginBottom: '4px', fontWeight: 600 }}>
                          Learning Competency
                        </div>
                        <div style={{ fontSize: '14px', color: '#e0e7ff', lineHeight: '1.5' }}>
                          {activeQuestion.standard_description}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Question Stem narrative */}
                  <h1 style={{ fontSize: '24px', fontWeight: 600, lineHeight: '1.6', marginBottom: '30px', color: '#f1f5f9', whiteSpace: 'pre-wrap' }}>
                    {activeQuestion.stem}
                  </h1>

                  <QuestionRenderer 
                      question={activeQuestion}
                      answer={practiceVisualAnswer}
                      setAnswer={setPracticeVisualAnswer}
                      answerResult={answerResult}
                    />



                  {/* MCQ/Visual Submit/Result — only for non-writing mode */}
                  {activeQuestion.question_mode !== 'writing_prompt' && (<div>
                  {!answerResult ? (
                    <button
                      className="btn-primary"
                      onClick={handleAnswerSubmit}
                      disabled={practiceVisualAnswer === null || practiceVisualAnswer === undefined || practiceVisualAnswer === ''}
                      style={{ width: '100%', padding: '16px' }}
                    >
                      <Check className="w-6 h-6" />
                      <span>Submit Answer</span>
                    </button>
                  ) : (
                    <div className="glass-card" style={{ background: 'rgba(255,255,255,0.02)', padding: '20px', borderLeft: answerResult.is_correct ? '4px solid #10b981' : '4px solid #ef4444' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                        {answerResult.is_correct ? (
                          <CheckCircle className="w-6 h-6" style={{ color: '#10b981' }} />
                        ) : (
                          <XCircle className="w-6 h-6" style={{ color: '#ef4444' }} />
                        )}
                        <span style={{ fontSize: '18px', fontWeight: 700 }}>
                          {answerResult.is_correct ? 'Correct! Awesome job!' : 'Incorrect answer.'}
                        </span>
                      </div>
                      <p style={{ fontSize: '15px', color: 'hsl(var(--text-muted))', marginBottom: '20px' }}>
                        {answerResult.explanation}
                      </p>
                      <button
                        className="btn-primary"
                        onClick={() => fetchNextQuestion(selectedStudent.id)}
                        style={{ width: '100%' }}
                      >
                        <span>Next Question</span>
                      </button>
                    </div>
                  )}
                  </div>)}
                </div>
              ) : (
                <div style={{ padding: '40px', textAlign: 'center' }}>No question loaded.</div>
              )}
            </div>

            {/* Right side: Socratic split dialog tutor */}
            {socraticActive && (
              <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '650px', borderLeft: '4px solid hsl(var(--primary))', animation: 'slide-up 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '15px', marginBottom: '15px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <MessageSquare className="w-6 h-6 text-purple-400" style={{ color: '#c084fc' }} />
                    <h3 style={{ fontSize: '20px' }}>Socratic Tutoring</h3>
                  </div>
                  <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => setSocraticActive(false)}>
                    Close Split
                  </button>
                </div>

                {/* Socratic chat bubbles */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                  <div className="chat-container" style={{ flex: 1, marginBottom: '15px' }}>
                    {chatMessages.map((msg, idx) => (
                      <div key={idx} className={`chat-bubble ${msg.role === 'user' ? 'student' : 'tutor'}`}>
                        {msg.content}
                      </div>
                    ))}
                    {sendingChat && (
                      <div className="chat-bubble tutor" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '10px 16px' }}>
                        <span className="dot-pulse" style={{ width: '6px', height: '6px', backgroundColor: '#c084fc', borderRadius: '50%', display: 'inline-block' }}></span>
                        <span className="dot-pulse" style={{ width: '6px', height: '6px', backgroundColor: '#c084fc', borderRadius: '50%', display: 'inline-block', animationDelay: '0.2s' }}></span>
                        <span className="dot-pulse" style={{ width: '6px', height: '6px', backgroundColor: '#c084fc', borderRadius: '50%', display: 'inline-block', animationDelay: '0.4s' }}></span>
                        <span style={{ fontSize: '13px', color: 'rgba(192, 132, 252, 0.7)', marginLeft: '6px' }}>Tutor is thinking...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px' }}>
                    <input 
                      type="text" 
                      className="premium-input" 
                      placeholder="Type your explanation or question..."
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      disabled={sendingChat}
                    />
                    <button type="submit" className="btn-primary" disabled={sendingChat}>
                      {sendingChat ? '...' : 'Send'}
                    </button>
                  </form>
                </div>
              </div>
            )}

          </div>
        )
      }
    </>
  );
}
