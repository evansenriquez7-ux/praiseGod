import React from 'react';
import { CheckCircle, XCircle, BookOpen, Unlock, Trash2, Save, Layout } from 'lucide-react';
import { SortOrderInteractive } from '../components/VisualSkeletons';
import { renderMath } from '../utils/mathUtils';
import { renderVisualInner } from '../utils/renderUtils';
import { AlertTriangle, Check, Play, Zap, Shield, User, RefreshCw } from 'lucide-react';
import { API_BASE } from '../api/apiClient';
import QuestionRenderer from '../components/QuestionRenderer';
export default function ParentDashboard(props) {
  const {
    parentLoggedIn, handleParentLogin, parentPassword, setParentPassword, parentError,
    parentActiveTab, setParentActiveTab, students,
    editName, setEditName, editElo, setEditElo, editAge, setEditAge, editGrade, setEditGrade, editInterests, setEditInterests,
    handleDeleteStudent, handleSaveStudentEdit,
    telemetryStats, adminLogs, setAdminLogs,
    matatagRawSkeletons, matatagCount, syncMatatagSkeletons,
    adminGenTopic, setAdminGenTopic, adminGenCount, setAdminGenCount, adminGenLoading, setAdminGenLoading, generateAdminProblems,
    adminCustomTarget, setAdminCustomTarget, adminCustomContext, setAdminCustomContext, adminCustomTheme, setAdminCustomTheme,
    adminCustomSkeletons, setAdminCustomSkeletons, injectCustomKnowledge,
    socraticActive, setSocraticActive, chatMessages, setChatMessages, sendingChat, setSendingChat,
    selectedStudent, setCurrentView, socraticAbortControllerRef,
    renderIntroViewer, introNodes, introInterests, introSelectedNode, setIntroSelectedNode, introSelectedInterest, setIntroSelectedInterest, generateIntroContent, introLoading,
    setSelectedStudent, setTelemetrySessionId, setParentLoggedIn, setParentError,
    matatagNodeId, matatagNodes, handleRunMatatagTest, matatagTestResults, testLoading, clearMatatagTests,
    activeSubject, activeDomain, activeSubdomain, renderMapOverlay, fetchMatatagNodes, fetchIntroNodes, fetchIntroInterests, modelsLoading, modelFilter, setModelFilter, setAnalyticsData, _resetMatatagState, labAllowedDifficulties, labVariantValues, labSelectedFormatter, setLabSelectedInterest, fetchParentGraph, opencodeModel, parentAuthRequired, matatagNodeSearch, setLabAllowedContexts, fetchParentAnalytics, labDifficultyScalars, setEditTelemetryEnabled, fetchProfiles, fetchMatatagQuestion, opencodeModels, fetchMatatagAxes, labAllowedFormatters, saveLabConfig, labInterests, handleUpdateSettings, setLabAllowedFormatters, matatagAxisValues, activeQuestion, parentSelectedGrade, setMatatagNodeId, setParentSubjectFilter, setParentSelectedGrade, setLabAllowedDifficulties, matatagQuestion, handleToggleParentAuth, matatagResult, parentSubjectFilter, labSelectedInterest, setMatatagNodeSearch, analyticsData, matatagLoading, labConfig, labConfigLoading, labConfigError, setLabConfigError, setMatatagAnswer, matatagAnswer, editTelemetryEnabled, labAllowedContexts, submitMatatagAnswer, handleOpencodeModelChange, parentGraphData, fetchLabConfig, setShowFlagModal
  } = props;

  return (
    <>
        {(() => {
          if (!parentLoggedIn) {
            return (
              <div className="glass-card animate-fade-in" style={{ maxWidth: '480px', margin: '60px auto', padding: '40px', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
                <div style={{ textAlign: 'center', marginBottom: '30px' }}>
                  <div style={{ width: '60px', height: '60px', borderRadius: '15px', background: 'linear-gradient(135deg, #a78bfa 0%, #7c3aed 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '28px', margin: '0 auto 15px', boxShadow: '0 8px 20px rgba(124, 58, 237, 0.3)' }}>
                    🔒
                  </div>
                  <h2 style={{ fontSize: '26px', fontWeight: 800, color: '#f8fafc', marginBottom: '8px' }}>Parent Access Control</h2>
                  <p style={{ color: 'hsl(var(--text-muted))', fontSize: '14px' }}>
                    Enter your parental dashboard password to manage student profiles, view telemetry logs, and track standards.
                  </p>
                </div>
                
                <form onSubmit={handleParentLogin} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <label style={{ fontSize: '13px', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Parent Password</label>
                    <input 
                      type="password" 
                      className="premium-input" 
                      placeholder="••••••••"
                      value={parentPassword}
                      onChange={(e) => setParentPassword(e.target.value)}
                      style={{ fontSize: '16px', letterSpacing: '4px' }}
                    />
                  </div>
                  
                  {parentError && (
                    <p style={{ color: '#fca5a5', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <AlertTriangle className="w-4 h-4" />
                      <span>{parentError}</span>
                    </p>
                  )}
                  
                  <button type="submit" className="btn-primary" style={{ padding: '14px', marginTop: '10px' }}>
                    <Unlock className="w-5 h-5" />
                    <span>Verify Credentials</span>
                  </button>
                  
                  <button 
                    type="button" 
                    className="btn-secondary" 
                    onClick={() => {
                      setCurrentView('login');
                      setParentError('');
                      setParentPassword('');
                    }}
                    style={{ padding: '12px' }}
                  >
                    <span>Cancel</span>
                  </button>
                </form>
              </div>
            );
          }

          return (
            <div className="glass-card" style={{ maxWidth: parentActiveTab === 'graph_auditor' ? '100%' : '950px', margin: '0 auto', transition: 'max-width 0.4s ease' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '20px', marginBottom: '30px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                    <h2 style={{ fontSize: '28px', margin: 0 }}>Parent Dashboard</h2>
                    
                    {/* Internal Tab Navigation */}
                    <div style={{ display: 'flex', background: 'rgba(255,255,255,0.04)', borderRadius: '12px', padding: '4px' }}>
                      <button 
                        onClick={() => setParentActiveTab('analytics')}
                        style={{ 
                          padding: '8px 16px', 
                          borderRadius: '8px', 
                          fontSize: '13.5px', 
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          background: parentActiveTab === 'analytics' ? 'hsl(var(--primary))' : 'transparent',
                          color: parentActiveTab === 'analytics' ? '#fff' : 'hsl(var(--text-muted))',
                          border: 'none'
                        }}
                      >
                        Analytics & Profiles
                      </button>
                      <button
                        onClick={() => {
                          setParentActiveTab('matatag_lab');
                          fetchMatatagNodes();
                        }}
                        style={{
                          padding: '8px 16px',
                          borderRadius: '8px',
                          fontSize: '13.5px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          background: parentActiveTab === 'matatag_lab' ? '#10b981' : 'transparent',
                          color: parentActiveTab === 'matatag_lab' ? '#fff' : 'hsl(var(--text-muted))',
                          border: 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <Layout className="w-4 h-4" />
                        MATATAG Lab
                      </button>
                      <button
                        onClick={() => {
                          setParentActiveTab('intro_lab');
                          fetchIntroNodes();
                          fetchIntroInterests(1);
                        }}
                        style={{
                          padding: '8px 16px',
                          borderRadius: '8px',
                          fontSize: '13.5px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s ease',
                          background: parentActiveTab === 'intro_lab' ? '#06b6d4' : 'transparent',
                          color: parentActiveTab === 'intro_lab' ? '#fff' : 'hsl(var(--text-muted))',
                          border: 'none',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        <BookOpen className="w-4 h-4" />
                        Intro Lab
                      </button>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <button className="btn-secondary" style={{ padding: '8px 16px', fontSize: '13px' }} onClick={() => {
                      setSelectedStudent(null);
                      setAnalyticsData(null);
                      setEditName('');
                      setEditElo(1200);
                      setEditAge(10);
                      setEditGrade(5);
                      setEditInterests('');
                    }}>
                      Switch Student
                    </button>
                    <button className="btn-secondary" style={{ padding: '8px 16px', fontSize: '13px' }} onClick={() => setCurrentView('login')}>
                      Back to Home
                    </button>
                  </div>
                </div>

                {parentActiveTab === 'analytics' ? (
                  <>
                    {/* AI Generator Backend — always visible, global setting */}
                    <div className="glass-card" style={{ marginBottom: '8px' }}>
                      <h3 style={{ fontSize: '20px', marginBottom: '6px' }}>AI Generator Backend</h3>
                      <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginBottom: '16px' }}>
                        Choose which AI engine powers question generation and student chat.
                      </p>

                      {/* Backend selector tile (Gemini only) */}
                      <div style={{ display: 'flex', gap: '12px' }}>
                        <div
                          style={{
                            flex: 1,
                            padding: '14px 16px',
                            borderRadius: '12px',
                            border: `2px solid #10b981`,
                            background: 'rgba(16,185,129,0.08)',
                            boxShadow: '0 0 14px rgba(16,185,129,0.25)',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <div style={{
                              width: '14px', height: '14px', borderRadius: '50%',
                              border: `2px solid #10b981`,
                              background: '#10b981',
                              flexShrink: 0,
                            }} />
                            <span style={{ fontWeight: 600, fontSize: '15px', color: 'hsl(var(--text-main))' }}>Gemini Free Tier</span>
                          </div>
                          <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', paddingLeft: '22px' }}>
                            Select the model below to power the Socratic Tutor
                          </span>
                        </div>
                      </div>

                      {/* Model selector */}
                      <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {modelsLoading ? (
                          <div style={{ fontSize: '13px', color: 'hsl(var(--text-muted))' }}>
                            Loading available models…
                          </div>
                        ) : (
                          <>
                            <input
                              type="text"
                              className="premium-input"
                              placeholder="Filter models…"
                              value={modelFilter}
                              onChange={(e) => setModelFilter(e.target.value)}
                              style={{ fontSize: '13px', padding: '8px 12px' }}
                            />
                            <select
                              className="premium-input"
                              value={opencodeModel}
                              onChange={(e) => handleOpencodeModelChange(e.target.value)}
                              style={{ fontSize: '13px', padding: '8px 12px', cursor: 'pointer' }}
                            >
                              {(opencodeModels.length === 0 ? [opencodeModel] : opencodeModels)
                                .filter(m => m.toLowerCase().includes(modelFilter.toLowerCase()))
                                .map(m => (
                                  <option key={m} value={m}>{m}</option>
                                ))
                              }
                            </select>
                            <span style={{ fontSize: '11px', color: 'hsl(var(--text-muted))' }}>
                              Active: <strong style={{ color: '#10b981' }}>{opencodeModel}</strong>
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {!analyticsData ? (
                      <div style={{ textAlign: 'center', padding: '40px' }}>
                        <h3 style={{ fontSize: '22px', marginBottom: '20px' }}>Select a Student Profile to View Analytics</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '20px', maxWidth: '600px', margin: '0 auto' }}>
                          {students.map(p => (
                            <div 
                              key={p.id} 
                              className="glass-card" 
                              style={{ cursor: 'pointer', transition: 'var(--transition-smooth)' }}
                              onClick={() => {
                                setSelectedStudent(p);
                                fetchParentAnalytics(p.id);
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <h4 style={{ fontSize: '18px', color: 'hsl(var(--secondary))' }}>{p.name}</h4>
                                <button
                                  onClick={async (e) => {
                                    e.stopPropagation();
                                    if (window.confirm(`Are you sure you want to delete ${p.name}?`)) {
                                      try {
                                        await fetch(`${API_BASE}/students/${p.id}`, { method: 'DELETE' });
                                        fetchProfiles();
                                      } catch (err) {
                                        console.error("Failed to delete", err);
                                      }
                                    }
                                  }}
                                  style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                                  title="Delete profile"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              </div>
                              <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '6px' }}>Grade {p.grade} • {p.age} yrs</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div>
                        {/* Analytical overview grids */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '30px' }}>
                      <div className="glass-card" style={{ textAlign: 'center', padding: '20px' }}>
                        <span style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Active ELO Rating</span>
                        <h1 style={{ fontSize: '36px', color: 'hsl(var(--secondary))', marginTop: '10px' }}>{analyticsData.elo_rating}</h1>
                      </div>
                      <div className="glass-card" style={{ textAlign: 'center', padding: '20px' }}>
                        <span style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Mastery Ratio</span>
                        <h1 style={{ fontSize: '36px', color: '#10b981', marginTop: '10px' }}>{Math.round(analyticsData.mastery_ratio * 100)}%</h1>
                      </div>
                      <div className="glass-card" style={{ textAlign: 'center', padding: '20px' }}>
                        <span style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', textTransform: 'uppercase' }}>Accuracy Rate</span>
                        <h1 style={{ fontSize: '36px', color: '#fbbf24', marginTop: '10px' }}>
                          {analyticsData.total_attempts > 0 ? Math.round((analyticsData.correct_attempts / analyticsData.total_attempts) * 100) : 0}%
                        </h1>
                      </div>
                    </div>

                    {/* Interactive visual knowledge graph */}
                    <div className="glass-card" style={{ marginBottom: '30px', padding: '30px 20px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '15px' }}>
                        <div>
                          <h3 style={{ fontSize: '22px', fontWeight: 700, color: '#f8fafc', marginBottom: '4px' }}>
                            Granular Academic Knowledge Graph
                          </h3>
                          <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))' }}>
                            Seeded with {parentGraphData ? parentGraphData.tracks.reduce((acc, t) => acc + t.nodes.length, 0) : 0} distinct parallel standards for the active grade.
                          </p>
                        </div>
                        
                        {/* Grade Navigation Bar */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', background: 'rgba(255,255,255,0.03)', padding: '6px 12px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                          <button 
                            className="btn-secondary" 
                            disabled={!parentSelectedGrade || parentSelectedGrade === 'K'} 
                            onClick={() => {
                              const AVAILABLE_GRADES = ['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'HS'];
                              const idx = AVAILABLE_GRADES.indexOf(parentSelectedGrade);
                              if (idx > 0) {
                                const prevG = AVAILABLE_GRADES[idx - 1];
                                setParentSelectedGrade(prevG);
                                fetchParentGraph(selectedStudent.id, prevG);
                              }
                            }}
                            style={{ padding: '6px 12px', fontSize: '12px', borderRadius: '8px' }}
                          >
                            ← Prev Grade
                          </button>
                          
                          <select 
                            className="premium-input" 
                            value={parentSelectedGrade || '5'} 
                            onChange={(e) => {
                              const g = e.target.value;
                              setParentSelectedGrade(g);
                              fetchParentGraph(selectedStudent.id, g);
                            }}
                            style={{ padding: '4px 10px', fontSize: '13px', borderRadius: '8px', border: 'none', background: 'rgba(0,0,0,0.3)', color: '#f8fafc', width: '130px', height: '32px' }}
                          >
                            {['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'HS'].map(g => (
                              <option key={g} value={g} style={{ background: '#0f172a' }}>
                                {g === 'K' ? 'Kindergarten' : g === 'HS' ? 'Grade 13' : `Grade ${g}`}
                              </option>
                            ))}
                          </select>
                          
                          <button 
                            className="btn-secondary" 
                            disabled={!parentSelectedGrade || parentSelectedGrade === 'HS'} 
                            onClick={() => {
                              const AVAILABLE_GRADES = ['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'HS'];
                              const idx = AVAILABLE_GRADES.indexOf(parentSelectedGrade);
                              if (idx < AVAILABLE_GRADES.length - 1 && idx !== -1) {
                                const nextG = AVAILABLE_GRADES[idx + 1];
                                setParentSelectedGrade(nextG);
                                fetchParentGraph(selectedStudent.id, nextG);
                              }
                            }}
                            style={{ padding: '6px 12px', fontSize: '12px', borderRadius: '8px' }}
                          >
                            Next Grade →
                          </button>
                        </div>
                      </div>

                      {/* Subject Filter Row */}
                      <div style={{ display: 'flex', gap: '10px', marginBottom: '25px', flexWrap: 'wrap' }}>
                        <button 
                          className="btn-secondary"
                          onClick={() => setParentSubjectFilter('all')}
                          style={{
                            padding: '8px 16px',
                            fontSize: '13px',
                            borderRadius: '10px',
                            background: parentSubjectFilter === 'all' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                            borderColor: parentSubjectFilter === 'all' ? '#a78bfa' : 'rgba(255,255,255,0.08)',
                            color: parentSubjectFilter === 'all' ? '#c084fc' : '#f8fafc'
                          }}
                        >
                          🌐 All Pathways
                        </button>
                        <button 
                          className="btn-secondary"
                          onClick={() => setParentSubjectFilter('math')}
                          style={{
                            padding: '8px 16px',
                            fontSize: '13px',
                            borderRadius: '10px',
                            background: parentSubjectFilter === 'math' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                            borderColor: parentSubjectFilter === 'math' ? '#a78bfa' : 'rgba(255,255,255,0.08)',
                            color: parentSubjectFilter === 'math' ? '#c084fc' : '#f8fafc'
                          }}
                        >
                          🧮 Mathematics
                        </button>
                        <button 
                          className="btn-secondary"
                          onClick={() => setParentSubjectFilter('ela')}
                          style={{
                            padding: '8px 16px',
                            fontSize: '13px',
                            borderRadius: '10px',
                            background: parentSubjectFilter === 'ela' ? 'rgba(139, 92, 246, 0.2)' : 'rgba(255,255,255,0.03)',
                            borderColor: parentSubjectFilter === 'ela' ? '#a78bfa' : 'rgba(255,255,255,0.08)',
                            color: parentSubjectFilter === 'ela' ? '#c084fc' : '#f8fafc'
                          }}
                        >
                          📚 English Language Arts
                        </button>
                      </div>

                      {!parentGraphData ? (
                        <div style={{ padding: '40px', textAlign: 'center', color: 'hsl(var(--text-muted))' }}>
                          Loading granular parallel knowledge graphs...
                        </div>
                      ) : parentGraphData.tracks.filter(lane => {
                        if (parentSubjectFilter === 'math') return lane.title.toLowerCase().includes('math');
                        if (parentSubjectFilter === 'ela') return lane.title.toLowerCase().includes('ela');
                        return true;
                      }).length === 0 ? (
                        <div style={{ padding: '40px', textAlign: 'center', color: 'hsl(var(--text-muted))' }}>
                          No standards registered under this domain for this grade level in the database.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
                          {parentGraphData.tracks.filter(lane => {
                            if (parentSubjectFilter === 'math') return lane.title.toLowerCase().includes('math');
                            if (parentSubjectFilter === 'ela') return lane.title.toLowerCase().includes('ela');
                            return true;
                          }).map((lane, lIdx) => (
                            <div key={lIdx} style={{ background: 'rgba(0,0,0,0.15)', borderRadius: '16px', padding: '20px', border: '1px solid rgba(255,255,255,0.03)' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                                <div style={{ width: '4px', height: '18px', borderRadius: '2px', backgroundColor: lane.color }} />
                                <h4 style={{ fontSize: '16px', fontWeight: 700, color: lane.color }}>{lane.title}</h4>
                              </div>
                              
                              <div style={{ display: 'flex', gap: '20px', overflowX: 'auto', paddingBottom: '10px', position: 'relative' }}>
                                {/* Connectivity Line */}
                                <div style={{
                                  position: 'absolute',
                                  top: '18px',
                                  left: '30px',
                                  right: '30px',
                                  height: '4px',
                                  background: `linear-gradient(90deg, #10b981 0%, ${lane.color} 60%, rgba(255,255,255,0.05) 100%)`,
                                  zIndex: 1,
                                  borderRadius: '2px'
                                }} />
                                
                                {lane.nodes.map((node) => {
                                  // Visual properties based on status
                                  let borderStyle = '2px solid rgba(255,255,255,0.1)';
                                  let bgStyle = 'rgba(13, 20, 38, 0.9)';
                                  let shadowStyle = 'none';
                                  let textGlow = 'rgba(255,255,255,0.4)';
                                  let badgeLabel = '🔒 Locked';
                                  let badgeColor = 'rgba(255,255,255,0.4)';
                                  
                                  const isActiveQuestion = activeQuestion && activeQuestion.skill_id === node.id;
                                  
                                  if (isActiveQuestion) {
                                    borderStyle = `3px solid ${lane.color}`;
                                    bgStyle = 'rgba(139, 92, 246, 0.25)';
                                    shadowStyle = `0 0 20px ${lane.color}`;
                                    textGlow = lane.color;
                                    badgeLabel = '📍 Practice';
                                    badgeColor = '#c084fc';
                                  } else if (node.status === 'mastered') {
                                    borderStyle = '3px solid #10b981';
                                    bgStyle = 'rgba(16, 185, 129, 0.15)';
                                    shadowStyle = '0 0 15px rgba(16, 185, 129, 0.3)';
                                    textGlow = '#10b981';
                                    badgeLabel = '✓ Mastered';
                                    badgeColor = '#10b981';
                                  } else if (node.status === 'active') {
                                    borderStyle = `3px solid ${lane.color}`;
                                    bgStyle = 'rgba(139, 92, 246, 0.15)';
                                    shadowStyle = `0 0 15px ${lane.color}`;
                                    textGlow = lane.color;
                                    badgeLabel = '⚡ Active';
                                    badgeColor = lane.color;
                                  } else if (node.status === 'review') {
                                    borderStyle = '3px solid #f59e0b';
                                    bgStyle = 'rgba(245, 158, 11, 0.15)';
                                    shadowStyle = '0 0 15px rgba(245, 158, 11, 0.3)';
                                    textGlow = '#f59e0b';
                                    badgeLabel = '⚠️ Review';
                                    badgeColor = '#f59e0b';
                                  }
                                  
                                  // Extract domain shorthand for visual sticker inside node
                                  let shorthand = node.id.includes('.') ? node.id.split('.')[1] : node.id.split('-')[0];
                                  if (shorthand.length > 3) shorthand = shorthand.substring(0, 3);
                                  
                                  return (
                                    <div key={node.id} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100px', zIndex: 2, position: 'relative', flexShrink: 0 }} title={`${node.id}: ${node.title}\n\n${node.description || ''}`}>
                                      
                                      {/* Circle Node */}
                                      <div style={{
                                        width: '40px',
                                        height: '40px',
                                        borderRadius: '50%',
                                        background: bgStyle,
                                        border: borderStyle,
                                        boxShadow: shadowStyle,
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        fontSize: '11px',
                                        fontWeight: 800,
                                        color: textGlow,
                                        marginBottom: '10px',
                                        cursor: 'pointer',
                                        transition: 'all 0.3s ease',
                                        position: 'relative'
                                      }}>
                                        {shorthand}
                                      </div>
                                      
                                      {/* Node details */}
                                      <span style={{ fontSize: '11px', fontWeight: 700, textAlign: 'center', color: textGlow, whiteSpace: 'nowrap' }}>
                                        {node.id}
                                      </span>
                                      <span style={{ fontSize: '9px', color: 'hsl(var(--text-muted))', textAlign: 'center', display: 'block', marginTop: '2px', height: '24px', overflow: 'hidden', textOverflow: 'ellipsis', width: '90px' }}>
                                        {node.title}
                                      </span>
                                      
                                      {/* Status Banner */}
                                      <span style={{ 
                                        marginTop: '6px', 
                                        fontSize: '8px', 
                                        fontWeight: 800, 
                                        padding: '2px 6px', 
                                        borderRadius: '4px', 
                                        background: 'rgba(255,255,255,0.03)',
                                        color: badgeColor,
                                        whiteSpace: 'nowrap'
                                      }}>
                                        {badgeLabel}
                                      </span>
                                      
                                      <span style={{ fontSize: '8px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                                        ELO: {Math.round(node.elo_rating)}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Telemetry Shield Audit log */}
                    <div className="glass-card" style={{ marginBottom: '30px' }}>
                      <h3 style={{ fontSize: '20px', marginBottom: '15px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <Shield className="w-5 h-5 text-green-400" style={{ color: '#10b981' }} />
                        <span>Telemetry Focus & Shield Audit Logs</span>
                      </h3>
                      
                      {analyticsData.sessions.length === 0 ? (
                        <p style={{ color: 'hsl(var(--text-muted))' }}>No active telemetry sessions tracked yet.</p>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {analyticsData.sessions.map(sess => (
                            <div key={sess.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', fontSize: '14px' }}>
                              <span>Session #{sess.id} duration: {sess.duration_minutes}m</span>
                              <div style={{ display: 'flex', gap: '20px' }}>
                                <span style={{ color: sess.tab_switch_count > 0 ? '#ef4444' : '#10b981' }}>{sess.tab_switch_count} Tab Switches</span>
                                <span>{sess.idle_seconds}s Idled</span>
                                <span>{sess.spam_click_count} Click Spams</span>
                                <span>{sess.guess_count} Rapid Guesses</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Quick setting editor override */}
                    <div className="glass-card">
                      <h3 style={{ fontSize: '20px', marginBottom: '15px' }}>Override Student Settings</h3>
                      <form onSubmit={handleUpdateSettings} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                          <input 
                            type="text" 
                            className="premium-input" 
                            placeholder="Student Name"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                          />
                          <input 
                            type="number" 
                            className="premium-input" 
                            placeholder="ELO Overrride"
                            value={editElo}
                            onChange={(e) => setEditElo(e.target.value)}
                          />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
                          <input 
                            type="number" 
                            className="premium-input" 
                            placeholder="Age"
                            value={editAge}
                            onChange={(e) => setEditAge(e.target.value)}
                          />
                          <input 
                            type="number" 
                            className="premium-input" 
                            placeholder="Grade"
                            value={editGrade}
                            onChange={(e) => setEditGrade(e.target.value)}
                          />
                          <input 
                            type="text" 
                            className="premium-input" 
                            placeholder="Interests"
                            value={editInterests}
                            onChange={(e) => setEditInterests(e.target.value)}
                          />
                        </div>
                        
                        <div className="glass-card" style={{ padding: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', marginTop: '5px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
                            <span style={{ fontSize: '15px', fontWeight: 600, color: 'hsl(var(--text-main))' }}>Active Telemetry Shield & Waste Defense</span>
                            <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))' }}>Monitors tab switching, inactivity, guess-checking, and lockouts.</span>
                          </div>
                          <div 
                            onClick={() => setEditTelemetryEnabled(!editTelemetryEnabled)}
                            style={{
                              width: '56px',
                              height: '30px',
                              borderRadius: '15px',
                              background: editTelemetryEnabled ? 'linear-gradient(135deg, #10b981, #059669)' : 'rgba(255,255,255,0.1)',
                              cursor: 'pointer',
                              position: 'relative',
                              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                              boxShadow: editTelemetryEnabled ? '0 0 15px rgba(16, 185, 129, 0.4)' : 'none',
                              display: 'flex',
                              alignItems: 'center',
                              padding: '3px'
                            }}
                          >
                            <div 
                              style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '50%',
                                background: '#ffffff',
                                transform: editTelemetryEnabled ? 'translateX(26px)' : 'translateX(0px)',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                              }}
                            ></div>
                          </div>
                        </div>

                        <div className="glass-card" style={{ padding: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', marginTop: '5px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', textAlign: 'left' }}>
                            <span style={{ fontSize: '15px', fontWeight: 600, color: 'hsl(var(--text-main))' }}>Require Parent Password Verification</span>
                            <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))' }}>When enabled, locks parental controls behind password validation.</span>
                          </div>
                          <div 
                            onClick={handleToggleParentAuth}
                            style={{
                              width: '56px',
                              height: '30px',
                              borderRadius: '15px',
                              background: parentAuthRequired ? 'linear-gradient(135deg, #a78bfa, #7c3aed)' : 'rgba(255,255,255,0.1)',
                              cursor: 'pointer',
                              position: 'relative',
                              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                              boxShadow: parentAuthRequired ? '0 0 15px rgba(139, 92, 246, 0.4)' : 'none',
                              display: 'flex',
                              alignItems: 'center',
                              padding: '3px'
                            }}
                          >
                            <div 
                              style={{
                                width: '24px',
                                height: '24px',
                                borderRadius: '50%',
                                background: '#ffffff',
                                transform: parentAuthRequired ? 'translateX(26px)' : 'translateX(0px)',
                                transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                                boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                              }}
                            ></div>
                          </div>
                        </div>

                        <button type="submit" className="btn-primary">
                          <Save className="w-5 h-5" />
                          <span>Save Settings Override</span>
                        </button>
                      </form>
                    </div>

                  </div>
                )}
                  </>
                ) : null}

                {/* ── MATATAG Lab tab ──────────────────────────────────── */}
                {parentActiveTab === 'matatag_lab' && (
                  <div style={{ padding: '10px 0' }}>

                    {/* ── Node selector panel ─────────────────────────── */}
                    <div className="glass-card" style={{ padding: '20px', marginBottom: '20px' }}>
                      <div style={{ marginBottom: '16px' }}>
                        <label style={{ fontSize: '12px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.08em', display: 'block', marginBottom: '8px' }}>
                          SEARCH NODE
                        </label>
                        <input
                          type="text"
                          className="premium-input"
                          placeholder="Type node ID, concept, or keyword — e.g. mat_g1_na, addition, calendar…"
                          value={matatagNodeSearch}
                          onChange={e => setMatatagNodeSearch(e.target.value)}
                          style={{ padding: '9px 13px', fontSize: '13px', width: '100%', boxSizing: 'border-box' }}
                        />
                      </div>

                      {/* Filtered node list */}
                      {matatagNodes.length === 0 && (
                        <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))' }}>Loading nodes…</p>
                      )}
                      {matatagNodes.length > 0 && (() => {
                        const q = matatagNodeSearch.toLowerCase();
                        const filtered = matatagNodes.filter(n =>
                          !q || n.node_id.includes(q) || n.competency.toLowerCase().includes(q) || n.primary_concept.includes(q)
                        );
                        return (
                          <select
                            size={Math.min(8, filtered.length || 1)}
                            className="premium-input"
                            style={{ width: '100%', padding: '4px', fontSize: '12.5px', fontFamily: 'monospace', cursor: 'pointer' }}
                            value={matatagNodeId}
                            onChange={e => {
                              const id = e.target.value;
                              setMatatagNodeId(id);
                              fetchMatatagAxes(id);
                              fetchLabConfig(id);  // Also load enhanced lab config
                            }}
                          >
                            {filtered.map(n => (
                              <option key={n.node_id} value={n.node_id} title={n.competency}>
                                {n.label}
                              </option>
                            ))}
                          </select>
                        );
                      })()}

                      {/* Selected node info badge */}
                      {matatagNodeId && (() => {
                        const node = matatagNodes.find(n => n.node_id === matatagNodeId);
                        if (!node) return null;
                        const fmts = node.available_formats || ['mcq'];
                        const hasBoth = fmts.includes('mcq') && fmts.includes('visual');
                        return (
                          <div>
                            <div style={{ marginTop: '12px', padding: '12px', background: 'rgba(16,185,129,0.08)', borderRadius: '8px', borderLeft: '3px solid #10b981' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px', flexWrap: 'wrap' }}>
                                <span style={{ fontSize: '11px', fontFamily: 'monospace', fontWeight: 700, color: '#10b981' }}>{node.node_id}</span>
                                <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(99,102,241,0.2)', color: '#a78bfa', fontWeight: 600 }}>{node.primary_concept}</span>
                                <span style={{ fontSize: '11px', color: 'hsl(var(--text-muted))' }}>Grade {node.grade} · {node.branch.toUpperCase()} · Q{node.quarter}</span>
                                {/* Format badges */}
                                {fmts.map(f => (
                                  <span key={f} style={{ fontSize: '10px', padding: '1px 7px', borderRadius: '8px', background: f === 'visual' ? 'rgba(167,139,250,0.2)' : 'rgba(99,102,241,0.15)', color: f === 'visual' ? '#a78bfa' : '#818cf8', fontWeight: 700, textTransform: 'uppercase' }}>{f}</span>
                                ))}
                              </div>
                              <p style={{ fontSize: '12.5px', color: 'hsl(var(--text))', lineHeight: 1.5, margin: 0 }}>{node.competency}</p>
                            </div>

                          </div>
                        );
                      })()}
                    </div>

                    {/* ── Enhanced Lab v2: Difficulty Dimensions, Variants, Formatters ── */}
                    {matatagNodeId && (
                      <div className="glass-card" style={{ padding: '20px', marginBottom: '20px' }}>
                        {/* Section header with loading indicator */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
                          <span style={{ fontSize: '12px', fontWeight: 700, color: '#a78bfa', letterSpacing: '0.08em' }}>
                            LAB CONTROLS v2
                          </span>
                          {labConfigLoading && (
                            <span style={{ fontSize: '11px', color: 'hsl(var(--text-muted))' }}>Loading config…</span>
                          )}
                          {!labConfigLoading && labConfig && (
                            <span style={{ fontSize: '11px', color: 'hsl(var(--text-muted))' }}>
                              {labConfig.difficulty_dimensions?.length || 0} dimensions · {labConfig.contextual_variants?.length || 0} variants · {labConfig.formatters?.length || 0} formatters
                            </span>
                          )}
                          <button
                            onClick={() => fetchLabConfig(matatagNodeId)}
                            style={{ marginLeft: 'auto', padding: '4px 10px', fontSize: '10px', borderRadius: '6px', background: 'rgba(99,102,241,0.2)', border: 'none', color: '#818cf8', cursor: 'pointer', fontWeight: 600 }}
                          >
                            Reload
                          </button>
                        </div>

                        {!labConfigLoading && !labConfig && (
                          <div style={{ textAlign: 'center', padding: '20px', color: 'hsl(var(--text-muted))' }}>
                            {labConfigError && (
                              <div style={{padding: '12px', margin: '12px 0', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#ef4444', fontSize: '13px'}}>
                                <strong>Failed to load lab config:</strong> {labConfigError}
                                <br />Click Reload to try again.
                              </div>
                            )}
                            <button
                              className="btn-secondary"
                              onClick={() => fetchLabConfig(matatagNodeId)}
                              style={{ padding: '8px 16px', fontSize: '12px' }}
                            >
                              Load Lab Config
                            </button>
                          </div>
                        )}

                        {!labConfigLoading && labConfig && (
                          <>
                            {/* ── 1. DIFFICULTY DIMENSIONS ── */}
                            <div style={{ marginBottom: '24px' }}>
                              <div style={{ fontSize: '11px', fontWeight: 700, color: '#10b981', letterSpacing: '0.08em', marginBottom: '12px' }}>
                                DIFFICULTY DIMENSIONS
                              </div>
                              {labConfig.difficulty_dimensions?.length === 0 && (
                                <p style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', margin: 0 }}>No difficulty dimensions defined.</p>
                              )}
                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                                {labConfig.difficulty_dimensions?.map(dim => {
                                  const currentScalar = labDifficultyScalars[dim.name] ?? 0.0;
                                  const currentOption = dim.options.find(o => Math.abs(o.scalar - currentScalar) < 0.01) || dim.options[0];
                                  const pct = currentScalar * 100;
                                  const difficulty_color = pct < 33 ? '#10b981' : pct < 66 ? '#f59e0b' : '#ef4444';
                                  return (
                                    <div key={dim.name} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                        <label style={{ fontSize: '11px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.06em' }}>
                                          {dim.label.toUpperCase()}
                                        </label>
                                      </div>
                                      
                                      {/* Allowed Settings Checkboxes */}
                                      <div style={{ marginTop: '8px', padding: '8px', background: 'rgba(0,0,0,0.1)', borderRadius: '6px' }}>
                                        <div style={{ fontSize: '9px', fontWeight: 700, color: '#10b981', marginBottom: '6px' }}>ALLOWED IN PORTAL</div>
                                        {dim.options.map(opt => (
                                          <label key={opt.scalar} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>
                                            <input 
                                              type="checkbox" 
                                              checked={(labAllowedDifficulties[dim.name] || []).includes(opt.scalar)}
                                              onChange={(e) => {
                                                const isChecked = e.target.checked;
                                                setLabAllowedDifficulties(prev => {
                                                  const curr = prev[dim.name] || [];
                                                  return { ...prev, [dim.name]: isChecked ? [...curr, opt.scalar] : curr.filter(x => x !== opt.scalar) };
                                                });
                                              }}
                                            />
                                            {opt.label}
                                          </label>
                                        ))}
                                      </div>
                                      
                                    </div>
                                  );
                                })}
                              </div>
                            </div>

                            {/* ── 2. CONTEXTUAL VARIANTS ── */}
                            {labConfig.contextual_variants?.length > 0 && (
                              <div style={{ marginBottom: '24px' }}>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: '#f59e0b', letterSpacing: '0.08em', marginBottom: '12px' }}>
                                  CONTEXTUAL VARIANTS
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                  {/* Grid for normal variants */}
                                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '16px' }}>
                                    {labConfig.contextual_variants
                                      .filter(variant => variant.name !== 'spine')
                                      .map(variant => {
                                        const currentVal = labVariantValues[variant.name] || variant.default;
                                        const selectedFormatter = labConfig.formatters?.find(f => f.name === labSelectedFormatter);
                                        const restrictions = selectedFormatter?.variant_restrictions;
                                        const isRestricted = restrictions && restrictions[variant.name] && !restrictions[variant.name].includes(currentVal);
                                        
                                        return (
                                          <div key={variant.name} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                              <label style={{ fontSize: '11px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.06em' }}>
                                                {variant.label.toUpperCase()}
                                              </label>
                                            </div>
                                            
                                            {/* Allowed Settings Checkboxes */}
                                            <div style={{ marginTop: '8px', padding: '8px', background: 'rgba(0,0,0,0.1)', borderRadius: '6px' }}>
                                              <div style={{ fontSize: '9px', fontWeight: 700, color: '#f59e0b', marginBottom: '6px' }}>ALLOWED IN PORTAL</div>
                                              {variant.options.map(opt => (
                                                <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>
                                                  <input 
                                                    type="checkbox" 
                                                    checked={(labAllowedContexts[variant.name] || []).includes(opt)}
                                                    onChange={(e) => {
                                                      const isChecked = e.target.checked;
                                                      setLabAllowedContexts(prev => {
                                                        const curr = prev[variant.name] || [];
                                                        return { ...prev, [variant.name]: isChecked ? [...curr, opt] : curr.filter(x => x !== opt) };
                                                      });
                                                    }}
                                                  />
                                                  {opt.replace(/_/g, ' ')}
                                                </label>
                                              ))}
                                            </div>
                                            
                                          </div>
                                        );
                                      })}
                                  </div>

                                  {/* Spine checkboxes rendered below context checkboxes when word_problem is allowed */}
                                  {(() => {
                                    const spineVariant = labConfig.contextual_variants.find(v => v.name === 'spine');
                                    const showSpine = spineVariant && (labAllowedContexts['context'] || []).includes('word_problem');
                                    if (!showSpine) return null;

                                    return (
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '12px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                          <label style={{ fontSize: '11px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.06em' }}>
                                            {spineVariant.label.toUpperCase()} (STORY SPINES)
                                          </label>
                                        </div>
                                        <div style={{ marginTop: '8px', padding: '8px', background: 'rgba(0,0,0,0.1)', borderRadius: '6px' }}>
                                          <div style={{ fontSize: '9px', fontWeight: 700, color: '#f59e0b', marginBottom: '6px' }}>ALLOWED IN PORTAL</div>
                                          {(labAllowedContexts[spineVariant.name] || []).length === 0 && (
                                            <div style={{ fontSize: '11px', color: '#ef4444', marginBottom: '6px' }}>Warning: No spines selected. Check at least one.</div>
                                          )}
                                          {spineVariant.options.map(opt => (
                                            <label key={opt} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>
                                              <input 
                                                type="checkbox" 
                                                checked={(labAllowedContexts[spineVariant.name] || []).includes(opt)}
                                                onChange={(e) => {
                                                  const isChecked = e.target.checked;
                                                  setLabAllowedContexts(prev => {
                                                    const curr = prev[spineVariant.name] || [];
                                                    return { ...prev, [spineVariant.name]: isChecked ? [...curr, opt] : curr.filter(x => x !== opt) };
                                                  });
                                                }}
                                              />
                                              {opt.replace(/_/g, ' ')}
                                            </label>
                                          ))}
                                        </div>
                                      </div>
                                    );
                                  })()}
                                </div>
                              </div>
                            )}

                            {/* ── 2b. STUDENT INTEREST (for word problems) ── */}
                            {labInterests.length > 0 && (
                              <div style={{ marginBottom: '24px' }}>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: '#ec4899', letterSpacing: '0.08em', marginBottom: '12px' }}>
                                  STUDENT INTEREST (WORD PROBLEM THEME)
                                </div>
                                <select
                                  className="premium-input"
                                  value={labSelectedInterest || ''}
                                  onChange={e => setLabSelectedInterest(e.target.value || null)}
                                  style={{ padding: '8px 12px', fontSize: '13px', maxWidth: '350px', width: '100%' }}
                                >
                                  {labInterests.map(interest => (
                                    <option 
                                      key={interest.interest_id || 'random'} 
                                      value={interest.interest_id || ''}
                                    >
                                      {interest.emoji} {interest.name}
                                    </option>
                                  ))}
                                </select>
                                <div style={{ fontSize: '10px', color: 'hsl(var(--text-muted))', marginTop: '6px', opacity: 0.7 }}>
                                  Themes characters, objects, and settings in word problems · Source: interest_bank.json
                                </div>
                              </div>
                            )}

                            {/* ── 3. PROBLEM TYPE (FORMATTER) ── */}
                            <div style={{ marginBottom: '20px' }}>
                              <div style={{ fontSize: '11px', fontWeight: 700, color: '#6366f1', letterSpacing: '0.08em', marginBottom: '12px' }}>
                                PROBLEM TYPE (FORMATTER)
                              </div>
                              {(() => {
                                const CONTEXT_SENSITIVE_FORMATTERS = new Set(['mcq', 'cloze', 'numeric_input', 'true_false', 'error_detect']);
                                const formatters = labConfig.formatters || [];
                                const contextSensitive = formatters.filter(fmt => CONTEXT_SENSITIVE_FORMATTERS.has(fmt.name));
                                const contextIndependent = formatters.filter(fmt => !CONTEXT_SENSITIVE_FORMATTERS.has(fmt.name));

                                const renderFormatterButton = (fmt) => {
                                  const hasRestrictions = fmt.variant_restrictions && Object.keys(fmt.variant_restrictions).length > 0;
                                  return (
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <input 
                                          type="checkbox" 
                                          checked={(labAllowedFormatters || []).includes(fmt.name)}
                                          onChange={(e) => {
                                            const isChecked = e.target.checked;
                                            setLabAllowedFormatters(prev => {
                                              return isChecked ? [...prev, fmt.name] : prev.filter(x => x !== fmt.name);
                                            });
                                          }}
                                          title="Allow in Portal"
                                        />
                                        <span style={{ fontSize: '11px', fontWeight: 600, color: 'hsl(var(--text))' }}>
                                          {fmt.label}
                                          {hasRestrictions && (
                                            <span style={{ marginLeft: '6px', fontSize: '9px', padding: '1px 4px', borderRadius: '4px', background: 'rgba(245,158,11,0.2)', color: '#f59e0b' }}>
                                              restricted
                                            </span>
                                          )}
                                        </span>
                                      </div>
                                  );
                                };

                                return (
                                  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                    {contextSensitive.length > 0 && (
                                      <div>
                                        <div style={{ fontSize: '10px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.04em', marginBottom: '8px', opacity: 0.8 }}>
                                          AFFECTED BY WORD PROBLEM CONTEXT
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                          {contextSensitive.map(renderFormatterButton)}
                                        </div>
                                      </div>
                                    )}
                                    {contextIndependent.length > 0 && (
                                      <div>
                                        <div style={{ fontSize: '10px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.04em', marginBottom: '8px', opacity: 0.8 }}>
                                          NOT AFFECTED BY CONTEXT (VISUAL & SYMBOLIC)
                                        </div>
                                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                          {contextIndependent.map(renderFormatterButton)}
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                );
                              })()}
                              
                              {/* Show restrictions for selected formatter */}
                              {(() => {
                                const fmt = labConfig.formatters?.find(f => f.name === labSelectedFormatter);
                                if (fmt?.variant_restrictions && Object.keys(fmt.variant_restrictions).length > 0) {
                                  return (
                                    <div style={{ marginTop: '10px', padding: '10px', background: 'rgba(245,158,11,0.08)', borderRadius: '6px', border: '1px solid rgba(245,158,11,0.2)' }}>
                                      <div style={{ fontSize: '10px', fontWeight: 700, color: '#f59e0b', marginBottom: '6px' }}>VARIANT RESTRICTIONS</div>
                                      <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))' }}>
                                        {Object.entries(fmt.variant_restrictions).map(([varName, allowed]) => (
                                          <div key={varName}>
                                            <strong>{varName}</strong>: {allowed.join(', ')}
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  );
                                }
                                return null;
                              })()}
                            </div>

                            {/* ── Generate button ── */}
                            <div style={{ display: 'flex', gap: '12px', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                              <button
                                className="btn-primary"
                                onClick={fetchMatatagQuestion}
                                disabled={matatagLoading || !matatagNodeId}
                                style={{ padding: '10px 24px' }}
                              >
                                <Zap className="w-4 h-4" />
                                <span>{matatagLoading ? 'Generating…' : 'Generate Preview'}</span>
                              </button>
                              <button
                                className="btn-primary"
                                onClick={saveLabConfig}
                                disabled={matatagLoading || !matatagNodeId}
                                style={{ padding: '10px 24px', background: '#10b981', borderColor: '#059669', color: '#fff' }}
                              >
                                <CheckCircle className="w-4 h-4" />
                                <span>Save Settings for Portal</span>
                              </button>
                              {matatagQuestion && !matatagResult && (
                                <button className="btn-secondary" onClick={_resetMatatagState} style={{ padding: '10px 16px', fontSize: '13px' }}>
                                  Clear
                                </button>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    )}

                    {/* Empty state */}
                    {!matatagNodeId && (
                      <div style={{ textAlign: 'center', padding: '60px 20px', color: 'hsl(var(--text-muted))' }}>
                        <Layout style={{ width: 40, height: 40, margin: '0 auto 12px', opacity: 0.3 }} />
                        <p style={{ fontSize: '15px' }}>Search for a node above and select it to load lab controls.</p>
                        <p style={{ fontSize: '13px', marginTop: '6px', opacity: 0.6 }}>
                          Each competency has unique <strong>difficulty dimensions</strong> (with scalar values), <strong>contextual variants</strong>, and compatible <strong>formatters</strong>.
                        </p>
                      </div>
                    )}

                    {/* ── Question card ────────────────────────────────── */}
                    {matatagQuestion && (
                      <div className="glass-card animate-fade-in" style={{ padding: '28px' }}>

                        {/* Header row */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
                          <span style={{
                            padding: '4px 12px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
                            background: matatagQuestion.is_visual ? '#a78bfa' : '#6366f1',
                            color: '#fff', textTransform: 'uppercase', letterSpacing: '0.05em'
                          }}>
                            {matatagQuestion.is_visual ? matatagQuestion.visual_type : 'MCQ'}
                          </span>
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(16,185,129,0.15)', color: '#10b981', fontWeight: 600 }}>
                            {matatagQuestion.primary_concept}
                          </span>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'hsl(var(--secondary))' }}>
                            Grade {matatagQuestion.grade}
                          </span>
                          <span style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', fontFamily: 'monospace' }}>
                            {matatagQuestion.skeleton_id}
                          </span>
                        </div>

                        {/* Active axis values summary (v1 fallback) */}
                        {!labConfig && Object.keys(matatagAxisValues).length > 0 && (
                           <div style={{ marginBottom: '16px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                             {Object.entries(matatagAxisValues).map(([k, v]) => (
                               <span key={k} style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(255,255,255,0.06)', color: 'hsl(var(--text-muted))' }}>
                                 {k}: <strong style={{ color: 'hsl(var(--text))' }}>{v}</strong>
                               </span>
                             ))}
                           </div>
                         )}

                         {/* Active difficulty profile & variant values summary (v2) */}
                         {labConfig && matatagQuestion && (
                           <div style={{ marginBottom: '16px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                             {/* Render Formatter */}
                             <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(99,102,241,0.15)', color: '#818cf8', fontWeight: 600 }}>
                               formatter: <strong style={{ color: '#a78bfa' }}>{matatagQuestion.format}</strong>
                             </span>
                             
                             {/* Render Difficulty Dimensions */}
                             {labConfig.difficulty_dimensions?.map(dim => {
                               const val = matatagQuestion.difficulty_axes_served?.[dim.name] ?? matatagQuestion.difficulty_profile?.[dim.name];
                               if (val === undefined) return null;
                               return (
                                 <span key={dim.name} style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(16,185,129,0.1)', color: '#10b981' }}>
                                   {dim.label}: <strong style={{ color: 'hsl(var(--text))' }}>{val}</strong>
                                 </span>
                               );
                             })}

                             {/* Render Contextual Variants */}
                             {labConfig.contextual_variants?.map(v => {
                               const val = matatagQuestion.difficulty_profile?.[v.name];
                               if (val === undefined) return null;
                               return (
                                 <span key={v.name} style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(245,158,11,0.1)', color: '#f59e0b' }}>
                                   {v.label}: <strong style={{ color: 'hsl(var(--text))' }}>{val}</strong>
                                 </span>
                               );
                             })}
                           </div>
                         )}

                        {/* Competency text */}
                        {matatagQuestion.competency_text && (
                          <div style={{ marginBottom: '20px', padding: '10px 14px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', borderLeft: '3px solid #10b981' }}>
                            <div style={{ fontSize: '10px', fontWeight: 700, color: '#10b981', marginBottom: '3px', letterSpacing: '0.08em' }}>MATATAG COMPETENCY</div>
                            <div style={{ fontSize: '12.5px', lineHeight: 1.5, color: 'hsl(var(--text))' }}>{matatagQuestion.competency_text}</div>
                          </div>
                        )}

                        {/* Stem */}
                        <p style={{ fontSize: '16px', lineHeight: 1.7, marginBottom: '24px', color: '#f1f5f9', fontWeight: 600 }}>
                          {renderMath(matatagQuestion.stem)}
                        </p>

                        {/* Question Renderer (Unified) */}
                        <div style={{ marginBottom: '24px' }}>
                          <QuestionRenderer 
                            question={matatagQuestion}
                            answer={matatagAnswer}
                            setAnswer={setMatatagAnswer}
                            answerResult={matatagResult}
                          />
                        </div>

                        {/* Submit / result */}
                        {!matatagResult ? (
                          <button
                            className="btn-primary"
                            onClick={submitMatatagAnswer}
                            disabled={matatagAnswer === null || matatagAnswer === ''}
                            style={{ width: '100%', padding: '14px' }}
                          >
                            <Check className="w-5 h-5" />
                            <span>Submit Answer</span>
                          </button>
                        ) : (
                          <div className="glass-card" style={{ padding: '20px', borderLeft: matatagResult.is_correct ? '4px solid #10b981' : '4px solid #ef4444', background: 'rgba(255,255,255,0.02)' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
                              {matatagResult.is_correct
                                ? <CheckCircle className="w-6 h-6" style={{ color: '#10b981' }} />
                                : <XCircle className="w-6 h-6" style={{ color: '#ef4444' }} />
                              }
                              <span style={{ fontSize: '17px', fontWeight: 700 }}>
                                {matatagResult.is_correct ? 'Correct!' : 'Incorrect'}
                              </span>
                              {!matatagResult.is_correct && (
                                <span style={{ fontSize: '14px', color: 'hsl(var(--text-muted))' }}>
                                  Correct: <strong style={{ color: '#f1f5f9' }}>{matatagResult.correct_answer}</strong>
                                </span>
                              )}
                            </div>
                            {matatagResult.trap_triggered && (
                              <div style={{ padding: '10px', marginBottom: '12px', background: 'rgba(255,165,0,0.1)', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
                                <div style={{ fontSize: '11px', fontWeight: 700, color: '#f59e0b', marginBottom: '4px' }}>COMMON MISCONCEPTION</div>
                                <div style={{ fontSize: '13px', color: 'hsl(var(--text))' }}>{matatagResult.trap_triggered}</div>
                              </div>
                            )}
                            <p style={{ fontSize: '14px', color: 'hsl(var(--text-muted))', marginBottom: '16px', lineHeight: 1.6 }}>
                              {matatagResult.explanation}
                            </p>
                            <button className="btn-primary" onClick={fetchMatatagQuestion} style={{ width: '100%' }}>
                              <Zap className="w-4 h-4" />
                              <span>Generate Another</span>
                            </button>
                          </div>
                        )}

                        {/* Flag Question button */}
                        <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'center' }}>
                          <button 
                            className="btn-secondary" 
                            onClick={() => setShowFlagModal(true)}
                            style={{ padding: '6px 12px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.1)', color: '#f87171', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                          >
                            <AlertTriangle className="w-4 h-4" />
                            <span>🚩 Flag</span>
                          </button>
                        </div>

                      </div>
                    )}

                  </div>
                )}

                {/* ── Intro Lab tab ──────────────────────────────────── */}
                {parentActiveTab === 'intro_lab' && (
                  <div style={{ padding: '10px 0' }}>
                    {/* Controls */}
                    <div className="glass-card" style={{ padding: '20px', marginBottom: '20px' }}>
                      <h3 style={{ fontSize: '18px', margin: '0 0 16px 0' }}>Intro Content Lab</h3>
                      <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginBottom: '20px' }}>
                        Preview introductory lesson content for MATATAG nodes. Select a node and optionally an interest theme to generate dynamic intro slides.
                      </p>

                      <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                        {/* Node dropdown */}
                        <div style={{ flex: 1, minWidth: '200px' }}>
                          <label style={{ fontSize: '12px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.08em', display: 'block', marginBottom: '6px' }}>
                            NODE
                          </label>
                          <select
                            className="premium-input"
                            value={introSelectedNode}
                            onChange={e => setIntroSelectedNode(e.target.value)}
                            style={{ padding: '9px 13px', fontSize: '13px', width: '100%' }}
                          >
                            <option value="">Select a node...</option>
                            {introNodes.map(n => (
                              <option key={n.node_key} value={n.node_key}>
                                {n.label} ({n.mini_lesson_count} mini-lessons)
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Interest dropdown */}
                        <div style={{ flex: 1, minWidth: '200px' }}>
                          <label style={{ fontSize: '12px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.08em', display: 'block', marginBottom: '6px' }}>
                            STUDENT INTEREST (optional)
                          </label>
                          <select
                            className="premium-input"
                            value={introSelectedInterest}
                            onChange={e => setIntroSelectedInterest(e.target.value)}
                            style={{ padding: '9px 13px', fontSize: '13px', width: '100%' }}
                          >
                            <option value="">No interest (neutral)</option>
                            {introInterests.map(t => (
                              <option key={t.key} value={t.key}>{t.name}</option>
                            ))}
                          </select>
                        </div>

                        {/* Generate button */}
                        <button
                          onClick={generateIntroContent}
                          disabled={!introSelectedNode || introLoading}
                          style={{
                            padding: '10px 24px',
                            borderRadius: '10px',
                            fontSize: '14px',
                            fontWeight: 700,
                            cursor: introSelectedNode && !introLoading ? 'pointer' : 'not-allowed',
                            background: introSelectedNode && !introLoading ? '#06b6d4' : 'rgba(255,255,255,0.05)',
                            color: introSelectedNode && !introLoading ? '#fff' : 'hsl(var(--text-muted))',
                            border: 'none',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                          }}
                        >
                          {introLoading ? 'Generating...' : 'Generate'}
                          {!introLoading && <Play className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Intro Content Display */}
                    {renderIntroViewer()}
                  </div>
                )}

              </div>
            </div>
          );
        })()}
    </>
  );
}
