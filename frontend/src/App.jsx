import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState, 
  addEdge, 
  MarkerType,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS as DndCSS } from '@dnd-kit/utilities';
import { 
  Shield, Zap, BookOpen, Award, User, Lock, Unlock, Settings, 
  AlertTriangle, Globe, RefreshCw, Play, CheckCircle, 
  XCircle, MessageSquare, Check, Trash2, Edit, Save,
  Search, Maximize2, Minimize2, Eye, Layout, Volume2, VolumeX
} from 'lucide-react';
import { useSoundEffects } from './hooks/useSoundEffects.js';
import { 
  NumberLineInteractive, 
  ClockSetInteractive, 
  PesoMoneyPicker,
  FillInTableInteractive,
  RuleDiscoveryInteractive,
  ConstraintSatisfactionInteractive,
  BarChartInteractive,
  SortOrderInteractive,
  GridAreaInteractive,
  CategorizeInteractive,
  CalendarInteractive,
  EmojiPictorialInteractive,
  PlaceValueBlocksInteractive,
  PatternSequenceInteractive,
  FractionModelInteractive,
  FractionShadeInteractive,
  TenFrameInteractive,
  RulerMeasureInteractive,
  BalanceScaleInteractive,
  ShapeBoardInteractive
} from './components/VisualSkeletons.jsx';
const _host = window.location.hostname;
// Detect if we are on a local LAN network (IPs or .local hostnames)
const _isLan = /^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)/.test(_host) || _host.endsWith('.local');

// Dynamically connect to the backend on the same host (port 8000) for local LAN / Tailscale / Tunnels
const _isTunnel = _host.endsWith('loca.lt') || 
                  _host.endsWith('serveousercontent.com') || 
                  _host.endsWith('pinggy-free.link') || 
                  _host.endsWith('trycloudflare.com') ||
                  _host.endsWith('ts.net') ||
                  _host.includes('tunnel') ||
                  _host.includes('ngrok');

const _isFirebase = _host.endsWith('web.app') || _host.endsWith('firebaseapp.com');

// If accessed via LAN IP, use http on port 8000. If tunnel, use https. Otherwise fallback to https on the same host.
let DEFAULT_API_BASE = `https://${_host}/api`;
if (_isLan) {
  DEFAULT_API_BASE = `http://${_host}:8000/api`;
}

// If accessed externally via here.now, default directly to the active, zero-warning secure Tailscale funnel!
// During testing, we allow this to be overridden by LAN settings or manual config.
if (_host.endsWith('here.now') && !_isLan && !_host.includes('localhost')) {
  DEFAULT_API_BASE = 'https://enrichmentcaps-mac-mini.tailf77f05.ts.net/api';
}

// Persistent server URL configuration for external network access
let API_BASE = localStorage.getItem('ccmed_api_base');

// Reset to default if the stored API base is empty, or if we are on localhost/127.0.0.1
// This ensures local testing always defaults to the correct local ports.
if (!API_BASE || _host === 'localhost' || _host === '127.0.0.1') {
  API_BASE = DEFAULT_API_BASE;
} else if (!API_BASE.startsWith('http://') && !API_BASE.startsWith('https://')) {
  // If the user typed it manually without protocol, default to https://
  API_BASE = 'https://' + API_BASE;
}
console.log("[CCMed] Active hostname:", _host);
console.log("[CCMed] Is tunnel connection:", _isTunnel);
console.log("[CCMed] API_BASE URL computed:", API_BASE);

;

const originalFetch = window.fetch;
window.fetch = async function () {
  let [resource, config] = arguments;
  if (typeof resource === 'string' && (
    resource.includes('loca.lt') || 
    resource.includes('serveousercontent.com') || 
    resource.includes('pinggy-free.link') || 
    resource.includes('trycloudflare.com') || 
    resource.includes('tunnel') || 
    resource.includes('ngrok')
  )) {
    if (!config) config = {};
    if (!config.headers) config.headers = {};
    config.headers['Bypass-Tunnel-Reminder'] = 'true';
    config.headers['ngrok-skip-browser-warning'] = 'true';
  }
  return originalFetch(resource, config);
};

/**
 * Convert LaTeX-encoded math to plain readable text.
 * Handles the most common patterns produced by the testy agent.
 *
 * Examples:
 *   \(\frac{3}{4}\)            → 3/4
 *   \(5 \times [3 + (8-2)]\)   → 5 × [3 + (8-2)]
 *   \(2^{-3}\)                 → 2^(-3)
 *   $\sqrt{16}$                → √16
 */
function renderMath(text) {
  if (!text || typeof text !== 'string') return text;

  return text
    // Strip display-math delimiters \[ ... \] and \( ... \)
    .replace(/\\\[/g, '').replace(/\\\]/g, '')
    .replace(/\\\(/g, '').replace(/\\\)/g, '')
    // Strip inline $ delimiters (single and double)
    .replace(/\$\$/g, '').replace(/\$/g, '')
    // Common operators
    .replace(/\\times/g, '×')
    .replace(/\\div/g, '÷')
    .replace(/\\cdot/g, '·')
    .replace(/\\pm/g, '±')
    .replace(/\\neq/g, '≠')
    .replace(/\\leq/g, '≤')
    .replace(/\\geq/g, '≥')
    .replace(/\\approx/g, '≈')
    .replace(/\\infty/g, '∞')
    .replace(/\\pi/g, 'π')
    .replace(/\\sqrt\{([^}]+)\}/g, '√($1)')
    // Fractions: \frac{num}{den} → num/den
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '$1/$2')
    // Superscripts: ^{expr} → ^(expr)
    .replace(/\^\{([^}]+)\}/g, '^($1)')
    // Subscripts: _{expr} → _expr
    .replace(/\_\{([^}]+)\}/g, '_$1')
    // Escaped braces
    .replace(/\\\{/g, '{').replace(/\\\}/g, '}')
    // Remove remaining LaTeX commands (e.g. \text{...} → content)
    .replace(/\\text\{([^}]*)\}/g, '$1')
    .replace(/\\mathrm\{([^}]*)\}/g, '$1')
    .replace(/\\mathbf\{([^}]*)\}/g, '$1')
    .replace(/\\left/g, '').replace(/\\right/g, '')
    // Remove any remaining lone backslash-commands
    .replace(/\\[a-zA-Z]+/g, '')
    // Normalize multiple spaces
    .replace(/\s{2,}/g, ' ')
    .trim();
}


function renderVisualInner(vt, vp, onAnswer, disabled, uniqueKey) {
  switch (vt) {
    case 'SortOrder':
      return <SortOrderInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'NumberLine':
      return <NumberLineInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'PlaceValueBlocks':
      return <PlaceValueBlocksInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'EmojiPictorial':
      return <EmojiPictorialInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'ClockSet':
      return <ClockSetInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'PesoMoney':
      return <PesoMoneyPicker key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'GridArea':
      return <GridAreaInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'Calendar':
      return <CalendarInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'Categorize':
      return <CategorizeInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'FillInTable':
      return <FillInTableInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'RuleDiscovery':
      return <RuleDiscoveryInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'BarChart':
      return <BarChartInteractive key={uniqueKey} params={vp} onAnswer={onAnswer} disabled={disabled} />;
    case 'PatternSequence':
      return <PatternSequenceInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'FractionModel':
      return <FractionModelInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'FractionShade':
      return <FractionShadeInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'TenFrame':
      return <TenFrameInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'RulerMeasure':
      return <RulerMeasureInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'BalanceScale':
      return <BalanceScaleInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    case 'ShapeBoard':
      return <ShapeBoardInteractive key={uniqueKey} params={vp} disabled={disabled} />;
    default:
      return <div style={{ padding: '20px', background: 'rgba(239,68,68,0.1)', borderRadius: '8px', color: '#f87171' }}>Unknown visual type: {vt}</div>;
  }
}

function App() {
  // Global App States
  const [currentView, setCurrentView] = useState('login'); // 'login', 'practice', 'parent'
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [pinInput, setPinInput] = useState('');
  const [pinError, setPinError] = useState('');
  
  // Backend Connection Manager States
  const [customApiUrl, setCustomApiUrl] = useState(API_BASE);
  const [showApiEditor, setShowApiEditor] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('checking'); // 'checking', 'connected', 'error'
  
  // Registration States
  const [regName, setRegName] = useState('');
  const [regPin, setRegPin] = useState('');
  const [regAge, setRegAge] = useState(10);
  const [regGrade, setRegGrade] = useState(5);
  const [regInterests, setRegInterests] = useState('basketball, bible');
  const [regLang, setRegLang] = useState('en');

  // Practice States
  const [activeQuestion, setActiveQuestion] = useState(null);
  const [selectedOptionKey, setSelectedOptionKey] = useState(null);
  const [answerResult, setAnswerResult] = useState(null);
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [questionStartTime, setQuestionStartTime] = useState(null);
  const [questionQueue, setQuestionQueue] = useState([]);
  const [matatagLoading, setMatatagLoading] = useState(false);
  // Visual question state for practice mode
  const [practiceVisualAnswer, setPracticeVisualAnswer] = useState(null);
  const [practiceOrdered, setPracticeOrdered] = useState([]);
  const [practiceClozeInputs, setPracticeClozeInputs] = useState([]);
  const [practiceNumeric, setPracticeNumeric] = useState('');

  // Socratic Split States
  const [socraticActive, setSocraticActive] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [sendingChat, setSendingChat] = useState(false);

  // Student interest input (subject_selection page)
  const [studentInterestInput, setStudentInterestInput] = useState('');
  const [interestSaveStatus, setInterestSaveStatus] = useState(''); // '' | 'saving' | 'saved'


  // Subject Navigation States
  const [selectedSubject, setSelectedSubject] = useState('Math'); // 'Math', 'Verbal', 'Matatag'
  const [practiceViewType, setPracticeViewType] = useState('subject_selection'); // 'subject_selection', 'workspace', 'math_track_selection', 'verbal_track_selection', 'matatag_track_selection'
  const [selectedSubdomain, setSelectedSubdomain] = useState(null);
  const [mathTracks, setMathTracks] = useState([]);
  const [loadingMathTracks, setLoadingMathTracks] = useState(false);
  const [matatagTracks, setMatatagTracks] = useState([]);
  const [loadingMatatagTracks, setLoadingMatatagTracks] = useState(false);


  // Telemetry Metrics
  const [telemetrySessionId, setTelemetrySessionId] = useState(null);
  const [tabSwitchCount, setTabSwitchCount] = useState(0);
  const [idleSeconds, setIdleSeconds] = useState(0);
  const [spamClickCount, setSpamClickCount] = useState(0);
  const [guessCount, setGuessCount] = useState(0);
  const [telemetryWarning, setTelemetryWarning] = useState('');

  // Parent States
  const [parentPassword, setParentPassword] = useState('');
  const [parentLoggedIn, setParentLoggedIn] = useState(false);
  const [parentActiveTab, setParentActiveTab] = useState('analytics'); // 'analytics', 'graph_auditor', 'problem_lab'
  const [adminSubject, setAdminSubject] = useState('Math');
  const [parentError, setParentError] = useState('');
  const [analyticsData, setAnalyticsData] = useState(null);
  const [parentGraphData, setParentGraphData] = useState(null);
  const [parentSelectedGrade, setParentSelectedGrade] = useState('5');
  const [showTelemetryModal, setShowTelemetryModal] = useState(false);
  const [parentSubjectFilter, setParentSubjectFilter] = useState('all');
  const [parentAuthRequired, setParentAuthRequired] = useState(false);

  // AI backend selector state (parental controls)
  const [aiBackend, setAiBackend] = useState('gemini');
  const [opencodeModel, setOpencodeModel] = useState('opencode/deepseek-v4-flash-free');
  const [opencodeModels, setOpencodeModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelFilter, setModelFilter] = useState('');


  // MATATAG Node+Difficulty Problem Lab states
  const [matatagMode,          setMatatagMode]          = useState(false);
  const [matatagNodes,         setMatatagNodes]         = useState([]);
  const [matatagNodeSearch,    setMatatagNodeSearch]    = useState('');
  const [matatagNodeId,        setMatatagNodeId]        = useState('');
  const [matatagAxes,          setMatatagAxes]          = useState([]); // [{name,label,options,default}]
  const [matatagAxisValues,    setMatatagAxisValues]    = useState({});
  const [matatagFormatPref,    setMatatagFormatPref]    = useState('auto'); // 'mcq' | 'visual' | 'auto'
  const [matatagAxesLoading,   setMatatagAxesLoading]   = useState(false);
  const [matatagQuestion,      setMatatagQuestion]      = useState(null);
  const [matatagAnswer,        setMatatagAnswer]        = useState(null);
  const [matatagResult,        setMatatagResult]        = useState(null);

  // Enhanced Lab v2: difficulty dimensions, variants, formatters
  const [labConfig,            setLabConfig]            = useState(null); // full config from /api/matatag/lab/config/{node_id}
  const [labDifficultyScalars, setLabDifficultyScalars] = useState({}); // {dimension_name: scalar}
  const [labVariantValues,     setLabVariantValues]     = useState({}); // {variant_name: value}
  const [labSelectedFormatter, setLabSelectedFormatter] = useState('mcq');
  const [labConfigLoading,     setLabConfigLoading]     = useState(false);
  const [labInterests,         setLabInterests]         = useState([]); // [{interest_id, name, emoji}]
  const [labSelectedInterest,  setLabSelectedInterest]  = useState(null); // interest_id or null for random
  const [labAllowedDifficulties, setLabAllowedDifficulties] = useState({}); // {dimension_name: [scalar1, ...]}
  const [labAllowedContexts,     setLabAllowedContexts]     = useState({}); // {variant_name: [val1, ...]}
  const [labAllowedFormatters,   setLabAllowedFormatters]   = useState([]); // [fmt1, ...]

  const [selectedRoadmapNode,    setSelectedRoadmapNode]    = useState(null); // stores the node_id when a roadmap node is clicked

  // Intro Lab states
  const [introNodes,          setIntroNodes]          = useState([]);
  const [introInterests,      setIntroInterests]      = useState([]);
  const [introSelectedNode,   setIntroSelectedNode]   = useState('');
  const [introSelectedInterest, setIntroSelectedInterest] = useState('');
  const [introContent,        setIntroContent]        = useState(null);
  const [introLoading,        setIntroLoading]        = useState(false);
  const [introSlideIndex,     setIntroSlideIndex]     = useState(0);
  const [introMiniLessonIndex, setIntroMiniLessonIndex] = useState(0);
  const [introStepIndex,      setIntroStepIndex]      = useState(0);

  // dnd-kit sensors for Problem Lab ordering (must be at component top level)
  const dndSensors = useSensors(useSensor(PointerSensor));

  
  // Edit Profile States (Parent Panel)
  const [editName, setEditName] = useState('');
  const [editAge, setEditAge] = useState(10);
  const [editGrade, setEditGrade] = useState(5);
  const [editInterests, setEditInterests] = useState('basketball, bible');
  const [editElo, setEditElo] = useState(1200);
  const [editTelemetryEnabled, setEditTelemetryEnabled] = useState(true);

  // Flagging States
  const [isFlagging, setIsFlagging] = useState(false);
  const [showFlagModal, setShowFlagModal] = useState(false);
  const [flagReason, setFlagReason] = useState('incorrect');
  const [flagComment, setFlagComment] = useState('');

  // Sound Effects State
  const [soundEnabled, setSoundEnabled] = useState(() => {
    const saved = localStorage.getItem('ccmed_sound_enabled');
    return saved !== 'false'; // Default to true
  });

  // Initialize sound effects
  const { playSelect, playCorrect, playIncorrect, initAudio } = useSoundEffects(soundEnabled);

  // Toggle sound setting
  const toggleSound = useCallback(() => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    localStorage.setItem('ccmed_sound_enabled', String(newValue));
    if (newValue) {
      initAudio();
    }
  }, [soundEnabled, initAudio]);

  // Refs for Telemetry
  const lastActiveTime = useRef(Date.now());
  const clickTracker = useRef([]);
  const chatEndRef = useRef(null);

  // Auto-scroll chat container to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, sendingChat]);

  // Load profiles and parent config on mount with dynamic server verification
  useEffect(() => {
    const verifyServerAndLoad = async () => {
      setConnectionStatus('checking');
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for serverless cold start
      
      try {
        const res = await fetch(`${API_BASE}/parent/config`, { signal: controller.signal });
        clearTimeout(timeoutId);
        if (res.ok) {
          setConnectionStatus('connected');
          const config = await res.json();
          setParentAuthRequired(config.password_auth_required);
          setAiBackend(config.ai_backend || 'gemini');
          setOpencodeModel(config.opencode_model || 'opencode/deepseek-v4-flash-free');
          // Pre-load model list if opencode backend is already configured
          if (config.ai_backend === 'opencode') {
            fetch(`${API_BASE}/parent/opencode-models`)
              .then(r => r.json())
              .then(d => setOpencodeModels(d.models || []))
              .catch(() => {});
          }
          if (!config.password_auth_required) {
            setParentLoggedIn(true);
          } else {
            setParentLoggedIn(false);
          }
          // Dynamic load profiles only when server is verified active
          fetchProfiles();
          return;
        }
      } catch (e) {
        clearTimeout(timeoutId);
        console.error("CCMed server connection check failed:", e);
      }
      setConnectionStatus('error');
    };
    verifyServerAndLoad();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/students/profiles`);
      const data = await res.json();
      setStudents(data);
    } catch (e) {
      console.error("Failed to fetch profiles", e);
    }
  };

  // --- Telemetry Listeners ---
  useEffect(() => {
    if (currentView !== 'practice' || !telemetrySessionId) return;

    // 1. Window Blur/Focus Detection
    const handleVisibilityChange = () => {
      if (document.hidden) {
        setTabSwitchCount(prev => prev + 1);
        setTelemetryWarning("Window out of focus! Focus on your math problem.");
        setTimeout(() => setTelemetryWarning(''), 5000);
        // Sync telemetry alert to backend immediately
        syncTelemetry(1, 0, 0, 0);
      }
    };

    const handleWindowBlur = () => {
      setTabSwitchCount(prev => prev + 1);
      setTelemetryWarning("Tab switch detected! Telemetry shield active.");
      setTimeout(() => setTelemetryWarning(''), 5000);
      syncTelemetry(1, 0, 0, 0);
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);

    // 2. Idle Timer (Tick every 1s)
    const interval = setInterval(() => {
      const idleTime = (Date.now() - lastActiveTime.current) / 1000;
      if (idleTime > 10) {
        setIdleSeconds(prev => prev + 1);
        syncTelemetry(0, 1, 0, 0);
      }
    }, 1000);

    // Track user input to reset idle timer
    const resetIdleTimer = () => {
      lastActiveTime.current = Date.now();
    };

    window.addEventListener('mousemove', resetIdleTimer);
    window.addEventListener('keydown', resetIdleTimer);
    window.addEventListener('click', resetIdleTimer);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      clearInterval(interval);
      window.removeEventListener('mousemove', resetIdleTimer);
      window.removeEventListener('keydown', resetIdleTimer);
      window.removeEventListener('click', resetIdleTimer);
    };
  }, [currentView, telemetrySessionId]);

  const syncTelemetry = async (tabs, idles, spams, guesses, ended = false) => {
    if (!telemetrySessionId) return;
    try {
      await fetch(`${API_BASE}/telemetry/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: telemetrySessionId,
          tab_switch_count: tabs,
          idle_seconds: idles,
          spam_click_count: spams,
          guess_count: guesses,
          ended: ended
        })
      });
    } catch (e) {
      console.error("Telemetry sync failed", e);
    }
  };

  // --- ACTIONS ---

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!regName || !regPin) return;
    try {
      const res = await fetch(`${API_BASE}/students/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: regName,
          pin: regPin,
          age: parseInt(regAge),
          grade: parseInt(regGrade),
          language_preference: regLang,
          interest_tags: regInterests
        })
      });
      if (res.ok) {
        fetchProfiles();
        setRegName('');
        setRegPin('');
      }
    } catch (e) {
      console.error("Registration failed", e);
    }
  };

  const handleSelectStudent = (student) => {
    setSelectedStudent(student);
    setPinInput('');
    setPinError('');
  };

  const handleStudentLogin = async (id, pin = null) => {
    const activePin = pin || pinInput;
    try {
      const res = await fetch(`${API_BASE}/students/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: id, pin: activePin })
      });
      if (res.ok) {
        const profile = await res.json();
        setSelectedStudent(profile);
        setStudentInterestInput(profile.student_interest_tags || '');
        
        // Start Telemetry Session if enabled
        if (profile.telemetry_enabled) {
          const telRes = await fetch(`${API_BASE}/telemetry/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: profile.id })
          });
          const telData = await telRes.json();
          setTelemetrySessionId(telData.session_id);
        } else {
          setTelemetrySessionId(null);
        }
        
        // Reset metrics
        setTabSwitchCount(0);
        setIdleSeconds(0);
        setSpamClickCount(0);
        setGuessCount(0);

        // Transition view and open the subject track dashboard selector
        setCurrentView('practice');
        setPracticeViewType('subject_selection');
      } else {
        setPinError("Invalid student PIN code.");
      }
    } catch (e) {
      setPinError("Failed to authenticate.");
    }
  };

  const fetchIntroForStudent = async (nodeId) => {
    setLoadingQuestion(true);
    setPracticeViewType('intro_viewer');
    setIntroContent(null);
    setIntroMiniLessonIndex(0);
    setIntroSlideIndex(0);
    setIntroStepIndex(0);
    setSocraticActive(true); // Always show tutor for intro content
    setChatMessages([]);
    try {
      // Convert full node_id (e.g. "mat_g3_na_q1_0") to the node_key
      // format the intro endpoint expects (e.g. "g3_na_q1").
      // Strip leading "mat_" prefix and trailing "_<index>" suffix.
      const nodeKey = nodeId
        .replace(/^mat_/, '')       // strip "mat_"
        .replace(/_\d+$/, '');      // strip trailing "_0", "_1" etc.
      const res = await fetch(`${API_BASE}/matatag/intro/${nodeKey}?student_id=${selectedStudent?.id || ''}`);
      if (!res.ok) throw new Error('Failed to load intro content');
      const data = await res.json();
      setIntroContent(data);
    } catch (err) {
      console.error('fetchIntroForStudent failed:', err);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const fetchNextQuestion = async (studentId, subject = selectedSubject, subdomain = selectedSubdomain, forceRefresh = false) => {
    setLoadingQuestion(true);
    setAnswerResult(null);
    setSelectedOptionKey(null);
    setChatMessages([]);
    if (subject === 'Matatag' || subject === 'MATATAG') {
      setSocraticActive(true);
    } else {
      setSocraticActive(false);
    }
    // Reset visual practice state
    setPracticeVisualAnswer(null);
    setPracticeOrdered([]);
    setPracticeClozeInputs([]);
    setPracticeNumeric('');
    try {
      if (!forceRefresh && questionQueue.length > 0) {
        const nextQ = questionQueue[0];
        setQuestionQueue(prev => prev.slice(1));
        setActiveQuestion(nextQ);
        setQuestionStartTime(Date.now());
        setLoadingQuestion(false);
        // Initialize ordering state if it's an ordering question
        if (nextQ.question_mode === 'ordering' && nextQ.visual_params?.items) {
          setPracticeOrdered(nextQ.visual_params.items.map((item, idx) => ({ id: `item_${idx}`, key: `${idx}`, text: String(item) })));
        }

        // Trigger background fetch when queue drops to exactly count-1 (2 for a batch of 3).
        // Using === instead of <= ensures we fire exactly ONCE per batch cycle — right after
        // the first question is consumed — never twice.
        if (questionQueue.length === 2) {
          backgroundFetchQueue(studentId, subject, subdomain);
        }
        return;
      }

      let url = `${API_BASE}/practice/${studentId}/batch?count=3&subject=${subject}`;
      // Pass subdomain (node_id for Matatag, track key for Math) to scope the question
      if (subdomain && (subject === 'Math' || subject === 'Matatag' || subject === 'MATATAG')) {
        url += `&subdomain=${encodeURIComponent(subdomain)}`;
      }
      const res = await fetch(url);
      const data = await res.json();
      
      if (data && data.length > 0) {
        setActiveQuestion(data[0]);
        setQuestionQueue(data.slice(1));
        setQuestionStartTime(Date.now());
        // Initialize ordering state if first question is ordering
        if (data[0].question_mode === 'ordering' && data[0].visual_params?.items) {
          setPracticeOrdered(data[0].visual_params.items.map((item, idx) => ({ id: `item_${idx}`, key: `${idx}`, text: String(item) })));
        }
      }
    } catch (e) {
      console.error("Failed to load question", e);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const backgroundFetchQueue = async (studentId, subject, subdomain) => {
      let url = `${API_BASE}/practice/${studentId}/batch?count=3&subject=${subject}`;
      if (subdomain && (subject === 'Math' || subject === 'Matatag' || subject === 'MATATAG')) {
        url += `&subdomain=${encodeURIComponent(subdomain)}`;
      }
      try {
        const res = await fetch(url);
        const data = await res.json();
        if (data && data.length > 0) {
            setQuestionQueue(prev => [...prev, ...data]);
        }
      } catch (e) {
          console.error("Background fetch queue failed", e);
      }
  };

  const handleSaveInterests = async () => {
    if (!selectedStudent) return;
    setInterestSaveStatus('saving');
    try {
      const res = await fetch(`${API_BASE}/students/${selectedStudent.id}/interests`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ interest_tags: studentInterestInput })
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedStudent(updated);
        setStudentInterestInput(updated.student_interest_tags || '');
        setInterestSaveStatus('saved');
        setTimeout(() => setInterestSaveStatus(''), 3000);
      } else {
        console.error("Save interests failed:", res.status);
        setInterestSaveStatus('error');
        setTimeout(() => setInterestSaveStatus(''), 3000);
      }
    } catch (e) {
      console.error("Failed to save interests", e);
      setInterestSaveStatus('error');
      setTimeout(() => setInterestSaveStatus(''), 3000);
    }
  };

  const fetchMathTracks = async (studentId) => {
    setLoadingMathTracks(true);
    try {
      const res = await fetch(`${API_BASE}/parent/graph/${studentId}`);
      const data = await res.json();
      if (data && data.tracks) {
        // Only keep Math tracks
        const mathOnly = data.tracks.filter(t => t.title.toLowerCase().includes('math'));
        setMathTracks(mathOnly);
      }
    } catch (e) {
      console.error("Failed to fetch math tracks", e);
    } finally {
      setLoadingMathTracks(false);
    }
  };

  const fetchVerbalTracks = async (studentId) => {
    setLoadingVerbalTracks(true);
    try {
      const res = await fetch(`${API_BASE}/parent/graph/${studentId}`);
      const data = await res.json();
      if (data && data.tracks) {
        // Filter out Math tracks to keep ELA only
        const elaOnly = data.tracks.filter(t => !t.title.toLowerCase().includes('math'));
        setVerbalTracks(elaOnly);
      }
    } catch (e) {
      console.error("Failed to fetch verbal tracks", e);
    } finally {
      setLoadingVerbalTracks(false);
    }
  };

  const fetchMatatagTracks = async (studentId) => {
    setLoadingMatatagTracks(true);
    try {
      // Use the new progress endpoint that returns grade/quarter position
      const res = await fetch(`${API_BASE}/matatag/progress/${studentId}`);
      const data = await res.json();
      
      if (data && data.content_areas) {
        // Transform the progress data into tracks format
        const tracks = data.content_areas.map(area => ({
          key: `MATATAG_${area.key}`,
          title: `${area.emoji} ${area.title}`,
          color: area.color,
          emoji: area.emoji,
          subject: 'Matatag',
          // New fields for grade/quarter display
          currentGrade: area.current_grade,
          currentQuarter: area.current_quarter,
          quarterCompetencies: area.quarter_competencies,
          quarterMastered: area.quarter_mastered,
          quarterActive: area.quarter_active,
          totalCompetencies: area.total_competencies,
          totalMastered: area.total_mastered,
          // For backward compatibility
          nodes: []
        }));
        setMatatagTracks(tracks);
      } else {
        // Fallback: create default content area tracks
        const defaultTracks = [
          { key: 'MATATAG_NA', title: '🔢 Number and Algebra', color: '#8b5cf6', emoji: '🔢', nodes: [], subject: 'Matatag', currentGrade: 1, currentQuarter: 1, quarterCompetencies: 0, quarterMastered: 0, quarterActive: 0, totalCompetencies: 0, totalMastered: 0 },
          { key: 'MATATAG_MG', title: '📐 Measurement and Geometry', color: '#f59e0b', emoji: '📐', nodes: [], subject: 'Matatag', currentGrade: 1, currentQuarter: 1, quarterCompetencies: 0, quarterMastered: 0, quarterActive: 0, totalCompetencies: 0, totalMastered: 0 },
          { key: 'MATATAG_DP', title: '📊 Data and Probability', color: '#10b981', emoji: '📊', nodes: [], subject: 'Matatag', currentGrade: 1, currentQuarter: 1, quarterCompetencies: 0, quarterMastered: 0, quarterActive: 0, totalCompetencies: 0, totalMastered: 0 },
        ];
        setMatatagTracks(defaultTracks);
      }
    } catch (e) {
      console.error("Failed to fetch matatag tracks", e);
      // Fallback on error
      const defaultTracks = [
        { key: 'MATATAG_NA', title: '🔢 Number and Algebra', color: '#8b5cf6', emoji: '🔢', nodes: [], subject: 'Matatag', currentGrade: 1, currentQuarter: 1, quarterCompetencies: 0, quarterMastered: 0, quarterActive: 0, totalCompetencies: 0, totalMastered: 0 },
        { key: 'MATATAG_MG', title: '📐 Measurement and Geometry', color: '#f59e0b', emoji: '📐', nodes: [], subject: 'Matatag', currentGrade: 1, currentQuarter: 1, quarterCompetencies: 0, quarterMastered: 0, quarterActive: 0, totalCompetencies: 0, totalMastered: 0 },
        { key: 'MATATAG_DP', title: '📊 Data and Probability', color: '#10b981', emoji: '📊', nodes: [], subject: 'Matatag', currentGrade: 1, currentQuarter: 1, quarterCompetencies: 0, quarterMastered: 0, quarterActive: 0, totalCompetencies: 0, totalMastered: 0 },
      ];
      setMatatagTracks(defaultTracks);
    } finally {
      setLoadingMatatagTracks(false);
    }
  };



  // Click handler with Telemetry detection
  const handleOptionClick = (key) => {
    // Initialize audio on first interaction
    initAudio();

    // 1. Spam Block detection
    const now = Date.now();
    clickTracker.current.push(now);
    
    // Filter click logs in last 1.5 seconds
    const recentClicks = clickTracker.current.filter(t => now - t < 1500);
    clickTracker.current = recentClicks;
    
    if (selectedStudent?.telemetry_enabled && recentClicks.length >= 4) {
      setSpamClickCount(prev => prev + 1);
      setTelemetryWarning("Spam click blocked! Take a deep breath.");
      setTimeout(() => setTelemetryWarning(''), 5000);
      syncTelemetry(0, 0, 1, 0);
      return; // Block
    }

    // Play selection sound
    playSelect();
    setSelectedOptionKey(key);
  };

  const handleAnswerSubmit = async () => {
    if (!activeQuestion) return;
    
    // Determine answer based on question type
    let answerToSubmit;
    const isMcq = !activeQuestion.is_visual && (!activeQuestion.question_mode || activeQuestion.question_mode === 'mcq');
    if (isMcq) {
      if (!selectedOptionKey) return;
      answerToSubmit = selectedOptionKey;
    } else {
      // Visual formats and non-MCQ textual formats store answer in practiceVisualAnswer
      if (practiceVisualAnswer === null || practiceVisualAnswer === undefined || practiceVisualAnswer === '') return;
      answerToSubmit = typeof practiceVisualAnswer === 'object' 
        ? JSON.stringify(practiceVisualAnswer) 
        : String(practiceVisualAnswer);
    }

    const timeSpentMs = Date.now() - questionStartTime;
    
    // 2. Guessing Telemetry flag
    let flaggedAsGuess = false;
    if (selectedStudent?.telemetry_enabled && timeSpentMs < 1500) {
      flaggedAsGuess = true;
      setGuessCount(prev => prev + 1);
      setTelemetryWarning("Super fast click detected! Guess flagged.");
      setTimeout(() => setTelemetryWarning(''), 5000);
      syncTelemetry(0, 0, 0, 1);
    }

    try {
      const res = await fetch(`${API_BASE}/practice/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: selectedStudent.id,
          session_id: telemetrySessionId,
          skill_id: activeQuestion.skill_id,
          skeleton_id: activeQuestion.skeleton_id,
          stem: activeQuestion.stem,
          correct_answer: '', // Calculated on backend
          selected_answer: answerToSubmit,
          response_time_ms: timeSpentMs,
          telemetry_flagged: flaggedAsGuess
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        console.error("Submit Error:", errorData);
        setAnswerResult({
          is_correct: false,
          correct_answer: null,
          explanation: "⚠️ Session Expired or Server Error: Please click 'Next Question' or refresh the page to sync with the server."
        });
        return;
      }

      const data = await res.json();
      setAnswerResult(data);

      // Play sound based on correctness
      if (data.is_correct) {
        playCorrect();
      } else {
        playIncorrect();
      }

      // Update active student ELO in profile local state
      setSelectedStudent(prev => ({
        ...prev,
        elo_rating: data.new_student_elo
      }));

      // Flush queue if placement, to enforce sequential updating
      if (activeQuestion.is_placement) {
        setQuestionQueue([]);
      }

      // Auto-trigger Socratic Tutor on ANY incorrect practice question
      if (!data.is_correct && !activeQuestion.is_placement) {
        setSocraticActive(true);
        const greeting = selectedStudent.language_preference === 'tl' 
          ? "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Suriin natin ang iyong sagot..."
          : "Praise God and the Lord Jesus Christ, I'm your tutor today. Let's analyze your answer...";
        
        setChatMessages([
          { role: 'assistant', content: greeting }
        ]);

        // Auto-ask the tutor to explain the mistake
        setSendingChat(true);
        fetch(`${API_BASE}/socratic/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id:     selectedStudent.id,
            skill_id:       activeQuestion.skill_id,
            question_text:  activeQuestion.stem,
            student_answer: data.student_answer || selectedOptionKey || '',
            is_intro:       false,
            message: selectedStudent.language_preference === 'tl'
              ? 'Mali ang aking sagot. Tulungan mo ako na maunawaan kung bakit.'
              : 'I chose the wrong answer. Can you help me understand why?',
            history: []
          })
        })
        .then(res => res.json())
        .then(chatData => {
          setChatMessages([
            { role: 'assistant', content: greeting + "\n\n" + chatData.reply }
          ]);
        })
        .catch(e => {
          console.error(e);
          setChatMessages([
            { role: 'assistant', content: greeting + "\n\n" + data.explanation }
          ]);
        })
        .finally(() => {
          setSendingChat(false);
        });
      } else if (data.trap_selected) {
        setSocraticActive(true);
        const greeting = selectedStudent.language_preference === 'tl' 
          ? "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Paano kita matutulungan?"
          : "Praise God and the Lord Jesus Christ, I'm your tutor today. How can I help you?";
        
        setChatMessages([
          { role: 'assistant', content: greeting }
        ]);
      }
    } catch (e) {
      console.error("Answer submission failed", e);
    }
  };

  const handleSkipPlacement = async () => {
    if (!selectedStudent || !selectedSubject) return;
    try {
      const res = await fetch(`${API_BASE}/practice/placement/skip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: selectedStudent.id,
          subject: selectedSubject
        })
      });
      if (res.ok) {
        // Refresh question to get out of placement mode
        fetchNextQuestion(selectedStudent.id, selectedSubject, selectedSubdomain, true);
      }
    } catch (e) {
      console.error("Skip placement failed", e);
    }
  };

  // --- Socratic Chat ---
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || (!activeQuestion && practiceViewType !== 'intro_viewer')) return;

    const userMsg = { role: 'user', content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setSendingChat(true);

    try {
      const res = await fetch(`${API_BASE}/socratic/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id:     selectedStudent.id,
          skill_id:       practiceViewType === 'intro_viewer'
            ? (introContent?.node_key || selectedSubdomain || '')
            : (activeQuestion?.skill_id || ''),
          question_text:  practiceViewType === 'intro_viewer'
            ? (introContent?.mini_lessons?.[introMiniLessonIndex]?.slides?.[introSlideIndex]?.content
                || introContent?.mini_lessons?.[introMiniLessonIndex]?.title
                || 'Intro lesson content')
            : (activeQuestion?.stem || ''),
          student_answer: selectedOptionKey || (typeof practiceVisualAnswer === 'object' ? JSON.stringify(practiceVisualAnswer) : String(practiceVisualAnswer || '')) || '',
          is_intro:       practiceViewType === 'intro_viewer',
          message:        chatInput,
          history:        chatMessages
        })
      });
      const data = await res.json();
      
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
      
      // If misconception is solved, tutor resolves Socratic mode and unlocks normal practice
      if (data.resolved) {
        let successMsg = "Hooray! You solved the concept beautifully! You can now move on to the next challenge.";
        if (selectedSubject === 'Math') {
          successMsg = "Hooray! You solved the math concept beautifully! You can now move on to the next math challenge.";
        } else if (selectedSubject.includes('Reading')) {
          successMsg = "Hooray! You solved the reading analysis beautifully! You can now move on to the next reading challenge.";
        } else if (selectedSubject.includes('Writing')) {
          successMsg = "Hooray! You completed the writing revision beautifully! You can now move on to the next writing challenge.";
        } else if (selectedSubject.includes('Language') || selectedSubject.includes('Grammar')) {
          successMsg = "Hooray! You mastered the language concept beautifully! You can now move on to the next language challenge.";
        }
        setChatMessages(prev => [...prev, { role: 'assistant', content: successMsg }]);
        setTimeout(() => {
          setSocraticActive(false);
          fetchNextQuestion(selectedStudent.id);
        }, 5000);
      }
    } catch (e) {
      console.error("Socratic chatbot exchange failed", e);
    } finally {
      setSendingChat(false);
    }
  };

  // ── MATATAG Node+Difficulty Problem Lab ──────────────────────────────────

  const _resetMatatagState = () => {
    setMatatagQuestion(null);
    setMatatagAnswer(null);
    setMatatagResult(null);
  };

  const fetchMatatagNodes = async () => {
    if (matatagNodes.length > 0) return; // already loaded
    try {
      const res = await fetch(`${API_BASE}/matatag/nodes`);
      if (!res.ok) throw new Error('Failed to load nodes');
      const data = await res.json();
      setMatatagNodes(data.nodes || []);
    } catch (err) {
      console.error('fetchMatatagNodes failed:', err);
    }
  };

  const fetchMatatagAxes = async (nodeId) => {
    if (!nodeId) return;
    setMatatagAxesLoading(true);
    setMatatagAxes([]);
    setMatatagAxisValues({});
    _resetMatatagState();
    try {
      const res = await fetch(`${API_BASE}/matatag/difficulty-axes/${nodeId}`);
      if (!res.ok) throw new Error('Failed to load axes');
      const data = await res.json();
      const axes = data.axes || [];
      setMatatagAxes(axes);
      // Seed defaults
      const defaults = {};
      axes.forEach(ax => { defaults[ax.name] = ax.default; });
      setMatatagAxisValues(defaults);
    } catch (err) {
      console.error('fetchMatatagAxes failed:', err);
    } finally {
      setMatatagAxesLoading(false);
    }
  };

  // Enhanced Lab v2: Fetch full config with difficulty dimensions, variants, formatters
  const fetchLabConfig = async (nodeId) => {
    if (!nodeId) return;
    setLabConfigLoading(true);
    setLabConfig(null);
    setLabDifficultyScalars({});
    setLabVariantValues({});
    setLabSelectedFormatter('mcq');
    _resetMatatagState();
    try {
      const res = await fetch(`${API_BASE}/matatag/lab/config/${nodeId}`);
      if (!res.ok) throw new Error('Failed to load lab config');
      const data = await res.json();
      setLabConfig(data);

      // Seed defaults for difficulty scalars (all at 0.0 = easiest)
      const defaultScalars = {};
      (data.difficulty_dimensions || []).forEach(dim => {
        defaultScalars[dim.name] = 0.0;
      });
      setLabDifficultyScalars(defaultScalars);

      // Seed defaults for variants
      const defaultVariants = {};
      (data.contextual_variants || []).forEach(v => {
        defaultVariants[v.name] = v.default || v.options[0];
      });
      setLabVariantValues(defaultVariants);

      // Set default formatter to first available
      if (data.formatters && data.formatters.length > 0) {
        setLabSelectedFormatter(data.formatters[0].name);
      }

      // Fetch saved checkboxes config
      try {
        const confRes = await fetch(`${API_BASE}/matatag/node/${nodeId}/config`);
        if (confRes.ok) {
          const confData = await confRes.json();
          // if confData is empty or new, default to selecting all options
          const allowedDiffs = confData.allowed_difficulties && Object.keys(confData.allowed_difficulties).length > 0 ? confData.allowed_difficulties : {};
          const allowedCtxs = confData.allowed_contexts && Object.keys(confData.allowed_contexts).length > 0 ? confData.allowed_contexts : {};
          const allowedFmts = confData.allowed_formatters && confData.allowed_formatters.length > 0 ? confData.allowed_formatters : [];
          
          // Seed defaults for empty arrays from the capabilities
          if (Object.keys(allowedDiffs).length === 0) {
            (data.difficulty_dimensions || []).forEach(dim => {
              allowedDiffs[dim.name] = dim.options.map(o => o.scalar);
            });
          }
          if (Object.keys(allowedCtxs).length === 0) {
            (data.contextual_variants || []).forEach(v => {
              if (v.name !== 'spine') {
                allowedCtxs[v.name] = [...v.options];
              }
            });
          }
          if (allowedFmts.length === 0) {
            // For peso nodes keep all formatters; for all other (non-peso) nodes
            // default to MCQ only so only the working formatter is pre-selected.
            const allFmtNames = (data.formatters || []).map(f => f.name);
            const isPesoNode = allFmtNames.some(n => n === 'peso_money_read' || n === 'peso_money_build');
            if (isPesoNode) {
              allowedFmts.push(...allFmtNames);
            } else {
              // Default: only MCQ enabled for non-peso nodes
              allowedFmts.push('mcq');
            }
          }

          setLabAllowedDifficulties(allowedDiffs);
          setLabAllowedContexts(allowedCtxs);
          setLabAllowedFormatters(allowedFmts);
        }
      } catch (e) {
        console.error('Failed to fetch node config:', e);
      }

      // Fetch all interests (no grade filtering)
      try {
        const interestRes = await fetch(`${API_BASE}/matatag/lab/interests`);
        if (interestRes.ok) {
          const interestData = await interestRes.json();
          setLabInterests(interestData.interests || []);
        }
      } catch (e) {
        console.error('Failed to fetch interests:', e);
      }
    } catch (err) {
      console.error('fetchLabConfig failed:', err);
    } finally {
      setLabConfigLoading(false);
    }
  };

  const saveLabConfig = async () => {
    if (!matatagNodeId) return;
    try {
      const res = await fetch(`${API_BASE}/matatag/node/${matatagNodeId}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          allowed_difficulties: labAllowedDifficulties,
          allowed_contexts: labAllowedContexts,
          allowed_formatters: labAllowedFormatters
        })
      });
      if (res.ok) {
        alert('Configuration saved for student portal!');
      } else {
        alert('Failed to save config.');
      }
    } catch(e) {
      console.error(e);
      alert('Error saving config.');
    }
  };

  const fetchMatatagQuestion = async () => {
    if (!matatagNodeId) {
      alert('Please select a node first');
      return;
    }
    setMatatagLoading(true);
    _resetMatatagState();
    try {
      // Use v2 endpoint when lab config is loaded
      if (labConfig) {
        // 1. Pick a random allowed difficulty for each dimension
        const difficultyProfile = {};
        labConfig.difficulty_dimensions?.forEach(dim => {
          const allowedScalars = labAllowedDifficulties[dim.name] || [];
          const chosenScalar = allowedScalars.length > 0 
            ? allowedScalars[Math.floor(Math.random() * allowedScalars.length)]
            : (dim.default_scalar ?? 0.0);
          const matchingOption = dim.options.find(o => Math.abs(o.scalar - chosenScalar) < 0.01);
          if (matchingOption) {
            difficultyProfile[dim.name] = dim.dim_type === 'continuous' ? matchingOption.value : matchingOption.level;
          }
        });

        // 2. Pick a random allowed variant for each context
        const variantValues = {};
        labConfig.contextual_variants?.forEach(v => {
          const allowedOpts = labAllowedContexts[v.name] || [];
          if (allowedOpts.length > 0) {
            variantValues[v.name] = allowedOpts[Math.floor(Math.random() * allowedOpts.length)];
          }
        });

        // 3. Pick a random allowed formatter
        const safeFormatters = labAllowedFormatters?.length > 0 
          ? labAllowedFormatters 
          : (labConfig.formatters?.map(f => f.name) || []);
        const chosenFormatter = safeFormatters.length > 0 
          ? safeFormatters[Math.floor(Math.random() * safeFormatters.length)] 
          : null;

        const res = await fetch(`${API_BASE}/matatag/lab/v2/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            node_id: matatagNodeId,
            formatter: chosenFormatter,
            difficulty_profile: Object.keys(difficultyProfile).length > 0 ? difficultyProfile : null,
            variant_values: Object.keys(variantValues).length > 0 ? variantValues : null,
            interest_theme: labSelectedInterest || null,
            seed: Math.floor(Math.random() * 1_000_000),
          }),
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(`MATATAG Lab v2: ${err.detail || 'Failed to generate problem'}`);
          setMatatagLoading(false);
          return;
        }
        const data = await res.json();
        // Map v2 response to expected structure for rendering
        setMatatagQuestion({
          ...data,
          skeleton_id: data.problem_id,  // Map problem_id to skeleton_id for compatibility
          stem: data.question_text,
          mcq_options: (() => {
            const rawOpts = data.format_data?.mcq_options || data.format_data?.options;
            if (Array.isArray(rawOpts)) {
              return rawOpts.map(o => ({
                key: o.key,
                text: String(o.value !== undefined && o.value !== null ? o.value : (o.text ?? ''))
              }));
            }
            if (Array.isArray(data.options)) {
              return data.options.map(o => ({
                key: o.key,
                text: String(o.value !== undefined && o.value !== null ? o.value : (o.text ?? ''))
              }));
            }
            if (data.options && typeof data.options === 'object') {
              return Object.entries(data.options).map(([key, val]) => ({
                key,
                text: String(val !== undefined && val !== null ? val : '')
              }));
            }
            return [];
          })(),
          difficulty: 0.5,  // v2 doesn't return a scalar difficulty yet
        });
      } else {
        // Fall back to old v1 endpoint
        const params = new URLSearchParams();
        params.set('node_id', matatagNodeId);
        params.set('seed', Math.floor(Math.random() * 1_000_000));
        params.set('format_preference', matatagFormatPref);
        if (Object.keys(matatagAxisValues).length > 0) {
          params.set('axis_values', JSON.stringify(matatagAxisValues));
        }

        const res = await fetch(`${API_BASE}/matatag/lab/generate?${params}`);
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(`MATATAG Problem Lab: ${err.detail || 'Failed to generate problem'}`);
          setMatatagLoading(false);
          return;
        }
        const data = await res.json();
        setMatatagQuestion(data);
      }
    } catch (err) {
      alert(`MATATAG Problem Lab error: ${err.message}`);
    } finally {
      setMatatagLoading(false);
    }
  };

  const submitMatatagAnswer = async () => {
    if (!matatagQuestion || matatagAnswer === null) return;
    try {
      // Format the answer payload based on format type
      let answerPayload;
      if (matatagQuestion.format === 'error_detect') {
        // Two-step: send JSON object
        answerPayload = JSON.stringify(matatagAnswer);
      } else if (matatagQuestion.answer_collection === 'mcq') {
        // MCQ answer is always a key string (A/B/C/D), even for visual formats
        answerPayload = String(matatagAnswer);
      } else if (matatagQuestion.is_visual) {
        answerPayload = JSON.stringify(matatagAnswer);
      } else {
        answerPayload = String(matatagAnswer);
      }

      // Use v2 endpoint if we have a problem_id (from v2 generate)
      if (matatagQuestion.problem_id) {
        const res = await fetch(`${API_BASE}/matatag/lab/v2/submit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            problem_id: matatagQuestion.problem_id,
            student_answer: answerPayload,
          }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(`Grading error: ${err.detail || 'Failed to grade answer'}`);
          return;
        }
        const data = await res.json();
        setMatatagResult(data);
      } else {
        // Fall back to v1 endpoint
        const params = new URLSearchParams();
        params.set('skeleton_id', matatagQuestion.skeleton_id);
        params.set('student_answer', answerPayload);
        const res = await fetch(`${API_BASE}/matatag/lab/submit?${params}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          alert(`Grading error: ${err.detail || 'Failed to grade answer'}`);
          return;
        }
        const data = await res.json();
        setMatatagResult(data);
      }
    } catch (err) {
      alert(`Submit error: ${err.message}`);
    }
  };

  // ── Intro Lab Functions ──────────────────────────────────────────────────

  const fetchIntroNodes = async () => {
    if (introNodes.length > 0) return;
    try {
      const res = await fetch(`${API_BASE}/matatag/intro/nodes`);
      if (!res.ok) throw new Error('Failed to load intro nodes');
      const data = await res.json();
      setIntroNodes(data.nodes || []);
      if (data.nodes && data.nodes.length > 0) {
        setIntroSelectedNode(data.nodes[0].node_key);
      }
    } catch (err) {
      console.error('fetchIntroNodes failed:', err);
    }
  };

  const fetchIntroInterests = async (grade = 1) => {
    try {
      const res = await fetch(`${API_BASE}/matatag/intro/interests?grade=${grade}`);
      if (!res.ok) throw new Error('Failed to load interests');
      const data = await res.json();
      setIntroInterests(data.interests || []);
    } catch (err) {
      console.error('fetchIntroInterests failed:', err);
    }
  };

  const generateIntroContent = async () => {
    if (!introSelectedNode) return;
    setIntroLoading(true);
    setIntroContent(null);
    setIntroMiniLessonIndex(0);
    setIntroSlideIndex(0);
    setIntroStepIndex(0);
    try {
      const params = new URLSearchParams();
      if (introSelectedInterest) params.set('interest', introSelectedInterest);
      const res = await fetch(`${API_BASE}/matatag/intro/${introSelectedNode}?${params}`);
      if (!res.ok) throw new Error('Failed to generate intro content');
      const data = await res.json();
      setIntroContent(data);
    } catch (err) {
      console.error('generateIntroContent failed:', err);
      alert(`Error: ${err.message}`);
    } finally {
      setIntroLoading(false);
    }
  };

  const renderIntroViewer = () => {
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
                                    if (chatMessages.length === 0) {
                                      const greeting = selectedStudent?.language_preference === 'tl'
                                        ? 'Purihin ang Diyos! Ako ang iyong tutor ngayon. Paano kita matutulungan sa araling ito?'
                                        : "Praise God! I'm your tutor. What questions do you have about this lesson?";
                                      setChatMessages([{ role: 'assistant', content: greeting }]);
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
                                        inner = inner.replace(/\\Large/g, '').replace(/\\\w+\{([^}]+)\}/g, '$1').replace(/\{|\}/g, '').trim();
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
                                              <div style={{ display: 'flex', gap: '2px', marginBottom: '4px' }}>
                                                {Array.from({ length: parts }).map((_, i) => (
                                                  <div key={i} style={{
                                                    width: '32px', height: '28px', borderRadius: '3px',
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
                                      };
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', alignItems: 'flex-end', flexWrap: 'wrap' }}>
                                            {shapeList.map((sh, i) => renderShape(sh, i))}
                                          </div>
                                          {vp.dimensions && (
                                            <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px', color: 'hsl(var(--text-muted))' }}>
                                              {vp.dimensions.length && `length: ${vp.dimensions.length}`} {vp.dimensions.width && `width: ${vp.dimensions.width}`} {vp.dimensions.side && `side: ${vp.dimensions.side}`}
                                            </div>
                                          )}
                                        </div>
                                      );
                                    }
  
                                    // ArrayGrid renderer — multiplication/division arrays
                                    if (vt === 'ArrayGrid') {
                                      const rows = Math.min(vp.rows || 2, 10);
                                      const cols = Math.min(vp.cols || 2, 10);
                                      const dotSize = rows * cols <= 25 ? 22 : rows * cols <= 50 ? 16 : 12;
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <div style={{ display: 'inline-grid', gridTemplateColumns: `repeat(${cols}, ${dotSize}px)`, gap: '4px', justifyContent: 'center' }}>
                                            {Array.from({ length: rows * cols }).map((_, i) => (
                                              <div key={i} style={{ width: dotSize + 'px', height: dotSize + 'px', borderRadius: '50%', background: 'rgba(59,130,246,0.35)', border: '2px solid #3b82f6' }} />
                                            ))}
                                          </div>
                                          <div style={{ marginTop: '10px', fontSize: '13px', color: '#3b82f6', fontWeight: 700 }}>{rows} rows × {cols} = {rows * cols}</div>
                                        </div>
                                      );
                                    }
  
                                    // LengthCompare renderer
                                    if (vt === 'LengthCompare') {
                                      const lcItems = vp.items || (vp.object ? [{ label: vp.object, length: vp.length }] : []);
                                      const maxLen = Math.max(...lcItems.map(it => it.length || 1), 1);
                                      const colors = ['#3b82f6', '#b91c5c', '#10b981', '#d97706'];
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          {lcItems.map((item, i) => (
                                            <div key={i} style={{ marginBottom: '14px' }}>
                                              <div style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>{item.label}</div>
                                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <div style={{ flex: 1, height: '22px', borderRadius: '4px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', overflow: 'hidden' }}>
                                                  <div style={{ width: `${((item.length || 1) / maxLen) * 100}%`, height: '100%', background: `${colors[i % colors.length]}50`, border: `2px solid ${colors[i % colors.length]}`, borderRadius: '4px', transition: 'width 0.4s ease' }} />
                                                </div>
                                                <span style={{ fontSize: '12px', fontWeight: 700, color: colors[i % colors.length], minWidth: '48px' }}>{item.length} {vp.unit || 'units'}</span>
                                              </div>
                                            </div>
                                          ))}
                                        </div>
                                      );
                                    }
  
                                    // TurnDisplay renderer
                                    if (vt === 'TurnDisplay') {
                                      const startAngle = vp.start_angle || 0;
                                      const amount = vp.amount || 0;
                                      const dir = vp.direction === 'counter_clockwise' ? -1 : 1;
                                      const endAngle = startAngle + dir * amount;
                                      const toRad = deg => (deg - 90) * Math.PI / 180;
                                      const cx = 60, cy = 60, r = 45;
                                      const startX = cx + r * Math.cos(toRad(startAngle));
                                      const startY = cy + r * Math.sin(toRad(startAngle));
                                      const endX = cx + r * Math.cos(toRad(endAngle));
                                      const endY = cy + r * Math.sin(toRad(endAngle));
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <svg width="120" height="120" viewBox="0 0 120 120">
                                            <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1"/>
                                            {amount === 0 && <line x1={cx} y1={cy} x2={startX} y2={startY} stroke="#3b82f6" strokeWidth="3" strokeLinecap="round"/>}
                                            {amount > 0 && <>
                                              <line x1={cx} y1={cy} x2={startX} y2={startY} stroke="rgba(255,255,255,0.3)" strokeWidth="2" strokeDasharray="4"/>
                                              <line x1={cx} y1={cy} x2={endX} y2={endY} stroke="#d97706" strokeWidth="3" strokeLinecap="round"/>
                                              <text x={endX + (endX > cx ? 4 : -4)} y={endY + 4} fontSize="11" fill="#d97706" textAnchor={endX > cx ? 'start' : 'end'}>{amount}°</text>
                                            </>}
                                          </svg>
                                          <div style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', marginTop: '4px' }}>{amount > 0 ? `${amount}° ${vp.direction === 'counter_clockwise' ? 'counter-clockwise' : 'clockwise'}` : 'starting position'}</div>
                                        </div>
                                      );
                                    }
  
                                    // PictographDisplay renderer
                                    if (vt === 'PictographDisplay') {
                                      const pdData = vp.data || [];
                                      const pdScale = vp.scale || 1;
                                      const pdMode = vp.mode || 'pictograph';
                                      const pdHighlight = vp.highlight || null;
                                      const emojiForLabel = label => {
                                        const m = {'cats':'🐱','dogs':'🐶','birds':'🐦','fish':'🐟','basketball':'🏀','volleyball':'🏐','food':'🍱','dance':'💃','art':'🎨','bible':'✝️'};
                                        return m[label?.toLowerCase()] || '⭐';
                                      };
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          {pdMode === 'table' ? (
                                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                                              <thead><tr>
                                                <th style={{ padding: '6px 12px', textAlign: 'left', color: 'hsl(var(--text-muted))', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Category</th>
                                                <th style={{ padding: '6px 12px', textAlign: 'right', color: 'hsl(var(--text-muted))', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>Count</th>
                                              </tr></thead>
                                              <tbody>{pdData.map((d, i) => (
                                                <tr key={i} style={{ background: d.label === pdHighlight ? 'rgba(217,119,6,0.08)' : 'transparent' }}>
                                                  <td style={{ padding: '6px 12px', color: d.label === pdHighlight ? '#d97706' : 'inherit' }}>{d.label}</td>
                                                  <td style={{ padding: '6px 12px', textAlign: 'right', fontWeight: 700, color: d.label === pdHighlight ? '#d97706' : '#3b82f6' }}>{d.count}</td>
                                                </tr>
                                              ))}</tbody>
                                            </table>
                                          ) : (
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                              {pdScale > 1 && <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', marginBottom: '4px' }}>Each {emojiForLabel('star')} = {pdScale} students</div>}
                                              {pdData.map((d, i) => {
                                                const pics = Math.round(d.count / pdScale);
                                                const isHl = d.label === pdHighlight;
                                                return (
                                                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                    <div style={{ width: '80px', fontSize: '12px', color: isHl ? '#d97706' : 'inherit', fontWeight: isHl ? 700 : 400, flexShrink: 0 }}>{d.label}</div>
                                                    <div style={{ display: 'flex', gap: '2px', flexWrap: 'wrap' }}>
                                                      {Array.from({ length: pics }).map((_, j) => (
                                                        <span key={j} style={{ fontSize: '16px', filter: isHl ? 'drop-shadow(0 0 3px #d97706)' : 'none' }}>{emojiForLabel(d.label)}</span>
                                                      ))}
                                                    </div>
                                                    <div style={{ fontSize: '12px', fontWeight: 700, color: isHl ? '#d97706' : 'hsl(var(--text-muted))' }}>{d.count}</div>
                                                  </div>
                                                );
                                              })}
                                            </div>
                                          )}
                                        </div>
                                      );
                                    }
  
                                    // RulerDisplay renderer
                                    if (vt === 'RulerDisplay') {
                                      const rdLen = vp.length_cm || 8;
                                      const rdUnit = vp.unit || 'cm';
                                      const rdObj = vp.object || 'object';
                                      const maxCm = Math.max(rdLen + 2, 15);
                                      const pxPerCm = 260 / maxCm;
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', marginBottom: '8px' }}>{rdObj}</div>
                                          {/* Object bar */}
                                          <div style={{ height: '18px', width: `${rdLen * pxPerCm}px`, background: 'rgba(217,119,6,0.3)', border: '2px solid #d97706', borderRadius: '3px', marginBottom: '4px' }} />
                                          {/* Ruler */}
                                          <div style={{ position: 'relative', height: '30px', width: `${maxCm * pxPerCm}px`, background: 'rgba(255,255,255,0.08)', borderRadius: '3px', border: '1px solid rgba(255,255,255,0.2)' }}>
                                            {Array.from({ length: maxCm + 1 }).map((_, i) => (
                                              <div key={i} style={{ position: 'absolute', left: `${i * pxPerCm}px`, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                <div style={{ width: '1px', height: '10px', background: 'rgba(255,255,255,0.4)' }} />
                                                <div style={{ fontSize: '9px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>{i}</div>
                                              </div>
                                            ))}
                                          </div>
                                          <div style={{ marginTop: '8px', fontSize: '13px', fontWeight: 700, color: '#d97706' }}>{rdLen} {rdUnit}</div>
                                        </div>
                                      );
                                    }
  
                                    // BarGraph renderer
                                    if (vt === 'BarGraph') {
                                      const bgData = vp.data || [];
                                      const bgOrientation = vp.orientation || 'vertical';
                                      const bgHighlight = vp.highlight || null;
                                      const bgMax = Math.max(...bgData.map(d => d.value || 0), 1);
                                      const barColors = ['#3b82f6', '#b91c5c', '#10b981', '#d97706', '#a78bfa', '#f97316'];
                                      if (bgOrientation === 'horizontal') {
                                        return (
                                          <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                            {bgData.map((d, i) => {
                                              const c = d.label === bgHighlight ? '#d97706' : barColors[i % barColors.length];
                                              return (
                                                <div key={i} style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                  <div style={{ width: '70px', fontSize: '11px', color: 'hsl(var(--text-muted))', flexShrink: 0, textAlign: 'right' }}>{d.label}</div>
                                                  <div style={{ flex: 1, height: '22px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                                                    <div style={{ width: `${(d.value / bgMax) * 100}%`, height: '100%', background: `${c}50`, border: `2px solid ${c}`, borderRadius: '4px' }} />
                                                  </div>
                                                  <div style={{ fontSize: '12px', fontWeight: 700, color: c, minWidth: '24px' }}>{d.value}</div>
                                                </div>
                                              );
                                            })}
                                            {vp.x_label && <div style={{ textAlign: 'center', fontSize: '11px', color: 'hsl(var(--text-muted))', marginTop: '6px' }}>{vp.x_label}</div>}
                                          </div>
                                        );
                                      }
                                      // Vertical bar graph
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'flex', alignItems: 'flex-end', gap: '10px', height: '120px', justifyContent: 'center' }}>
                                            {bgData.map((d, i) => {
                                              const c = d.label === bgHighlight ? '#d97706' : barColors[i % barColors.length];
                                              const h = Math.max(4, (d.value / bgMax) * 100);
                                              return (
                                                <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                                                  <div style={{ fontSize: '11px', fontWeight: 700, color: c }}>{d.value}</div>
                                                  <div style={{ width: '36px', height: `${h}px`, background: `${c}40`, border: `2px solid ${c}`, borderRadius: '4px 4px 0 0' }} />
                                                  <div style={{ fontSize: '10px', color: 'hsl(var(--text-muted))', textAlign: 'center', maxWidth: '48px', wordBreak: 'break-word' }}>{d.label}</div>
                                                </div>
                                              );
                                            })}
                                          </div>
                                          {vp.y_label && <div style={{ textAlign: 'left', fontSize: '11px', color: 'hsl(var(--text-muted))', marginTop: '4px' }}>{vp.y_label}</div>}
                                        </div>
                                      );
                                    }
  
                                    // AreaGrid renderer
                                    if (vt === 'AreaGrid') {
                                      const agRows = Math.min(vp.rows || 4, 12);
                                      const agCols = Math.min(vp.cols || 4, 12);
                                      const cellSize = agRows * agCols <= 36 ? 24 : 16;
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <div style={{ display: 'inline-grid', gridTemplateColumns: `repeat(${agCols}, ${cellSize}px)`, gap: '2px', border: '2px solid #10b981', borderRadius: '4px', padding: '2px', marginBottom: '8px' }}>
                                            {Array.from({ length: agRows * agCols }).map((_, i) => (
                                              <div key={i} style={{ width: cellSize + 'px', height: cellSize + 'px', background: 'rgba(16,185,129,0.15)', border: '1px solid rgba(16,185,129,0.3)' }} />
                                            ))}
                                          </div>
                                          <div style={{ fontSize: '13px', fontWeight: 700, color: '#10b981' }}>{agRows} × {agCols} = {agRows * agCols} sq. {vp.unit || 'units'}</div>
                                        </div>
                                      );
                                    }
  
                                    // LineDisplay renderer
                                    if (vt === 'LineDisplay') {
                                      const ldType = vp.type || 'line';
                                      const svgW = 200, svgH = 80;
                                      let svgContent;
                                      const lineStyle = { stroke: '#3b82f6', strokeWidth: '2.5', strokeLinecap: 'round' };
                                      const lineStyle2 = { stroke: '#b91c5c', strokeWidth: '2.5', strokeLinecap: 'round' };
                                      const arrowHead = (x, y, angle) => {
                                        const r = (angle * Math.PI / 180);
                                        const len = 8;
                                        return `M${x} ${y} L${x - len * Math.cos(r - 0.4)} ${y - len * Math.sin(r - 0.4)} M${x} ${y} L${x - len * Math.cos(r + 0.4)} ${y - len * Math.sin(r + 0.4)}`;
                                      };
                                      if (ldType === 'parallel') svgContent = (<><line x1="20" y1="25" x2="180" y2="25" {...lineStyle}/><line x1="20" y1="55" x2="180" y2="55" {...lineStyle2}/><text x="90" y="42" fontSize="10" fill="#d97706" textAnchor="middle">always same distance</text></>);
                                      else if (ldType === 'perpendicular') svgContent = (<><line x1="20" y1="40" x2="180" y2="40" {...lineStyle}/><line x1="100" y1="8" x2="100" y2="72" {...lineStyle2}/><rect x="100" y="40" width="8" height="8" fill="none" stroke="#d97706" strokeWidth="1.5"/></>);
                                      else if (ldType === 'intersecting') svgContent = (<><line x1="20" y1="60" x2="180" y2="20" {...lineStyle}/><line x1="20" y1="20" x2="180" y2="60" {...lineStyle2}/><circle cx="100" cy="40" r="4" fill="#d97706"/></>);
                                      else if (ldType === 'line_segment') svgContent = (<><circle cx="30" cy="40" r="4" fill="#3b82f6"/><line x1="30" y1="40" x2="170" y2="40" {...lineStyle}/><circle cx="170" cy="40" r="4" fill="#3b82f6"/><text x="100" y="60" fontSize="10" fill="#d97706" textAnchor="middle">endpoints</text></>);
                                      else if (ldType === 'ray') svgContent = (<><circle cx="30" cy="40" r="4" fill="#3b82f6"/><line x1="30" y1="40" x2="180" y2="40" {...lineStyle}/><path d={arrowHead(180, 40, 0)} stroke="#3b82f6" strokeWidth="2" fill="none"/></>);
                                      else if (ldType === 'point') svgContent = (<><circle cx="100" cy="40" r="6" fill="#3b82f6"/><text x="100" y="65" fontSize="11" fill="#3b82f6" textAnchor="middle">{vp.label || 'A'}</text></>);
                                      else if (ldType === 'line_and_segment') svgContent = (<><line x1="10" y1="25" x2="190" y2="25" {...lineStyle}/><text x="100" y="20" fontSize="9" fill="#3b82f6" textAnchor="middle">line (→ forever)</text><circle cx="30" cy="55" r="4" fill="#b91c5c"/><line x1="30" y1="55" x2="170" y2="55" {...lineStyle2}/><circle cx="170" cy="55" r="4" fill="#b91c5c"/><text x="100" y="75" fontSize="9" fill="#b91c5c" textAnchor="middle">segment (endpoints)</text></>);
                                      else svgContent = (<line x1="20" y1="40" x2="180" y2="40" {...lineStyle}/>);
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <svg width={svgW} height={svgH} viewBox={`0 0 ${svgW} ${svgH}`}>{svgContent}</svg>
                                          <div style={{ fontSize: '11px', color: '#3b82f6', marginTop: '4px', textTransform: 'capitalize' }}>{ldType.replace(/_/g, ' ')}</div>
                                        </div>
                                      );
                                    }
  
                                    // BalanceScale renderer
                                    if (vt === 'BalanceScale') {
                                      const bsLeft = vp.left || { label: 'A', mass_g: 300 };
                                      const bsRight = vp.right || { label: 'B', mass_g: 200 };
                                      const lM = bsLeft.mass_g || 1;
                                      const rM = bsRight.mass_g || 1;
                                      const tilt = lM === rM ? 0 : lM > rM ? 12 : -12;
                                      return (
                                        <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <svg width="220" height="100" viewBox="0 0 220 100">
                                            {/* Fulcrum */}
                                            <polygon points="110,85 100,100 120,100" fill="rgba(255,255,255,0.2)" stroke="rgba(255,255,255,0.3)" strokeWidth="1"/>
                                            {/* Beam */}
                                            <g transform={`rotate(${tilt} 110 80)`}>
                                              <line x1="20" y1="80" x2="200" y2="80" stroke="#06b6d4" strokeWidth="3" strokeLinecap="round"/>
                                              {/* Left pan */}
                                              <line x1="30" y1="80" x2="30" y2="60" stroke="#06b6d4" strokeWidth="2"/>
                                              <rect x="10" y="55" width="40" height="10" rx="3" fill="rgba(59,130,246,0.3)" stroke="#3b82f6" strokeWidth="2"/>
                                              <text x="30" y="50" textAnchor="middle" fontSize="10" fill="#3b82f6">{bsLeft.label}</text>
                                              <text x="30" y="42" textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.5)">{lM}g</text>
                                              {/* Right pan */}
                                              <line x1="190" y1="80" x2="190" y2="60" stroke="#06b6d4" strokeWidth="2"/>
                                              <rect x="170" y="55" width="40" height="10" rx="3" fill="rgba(185,28,92,0.3)" stroke="#b91c5c" strokeWidth="2"/>
                                              <text x="190" y="50" textAnchor="middle" fontSize="10" fill="#b91c5c">{bsRight.label}</text>
                                              <text x="190" y="42" textAnchor="middle" fontSize="9" fill="rgba(255,255,255,0.5)">{rM}g</text>
                                            </g>
                                          </svg>
                                          <div style={{ fontSize: '12px', color: 'hsl(var(--text-muted))' }}>
                                            {lM === rM ? 'balanced' : lM > rM ? `${bsLeft.label} is heavier` : `${bsRight.label} is heavier`}
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // CapacityDisplay renderer
                                    if (vt === 'CapacityDisplay') {
                                      const cdContainers = vp.containers || [];
                                      const cdMaxMl = Math.max(...cdContainers.map(c => c.capacity_mL || 0), 1000);
                                      const colors = ['#3b82f6', '#b91c5c', '#10b981', '#d97706'];
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)' }}>
                                          <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', alignItems: 'flex-end' }}>
                                            {cdContainers.map((c, i) => {
                                              const fillPct = (c.capacity_mL || 0) / cdMaxMl;
                                              const containerH = 80;
                                              const fillH = fillPct * containerH;
                                              const col = colors[i % colors.length];
                                              const displayVal = c.capacity_mL >= 1000 ? `${c.capacity_mL / 1000}L` : `${c.capacity_mL}mL`;
                                              return (
                                                <div key={i} style={{ textAlign: 'center' }}>
                                                  <div style={{ width: '48px', height: `${containerH}px`, border: `2px solid ${col}`, borderRadius: '4px 4px 6px 6px', background: 'rgba(255,255,255,0.03)', position: 'relative', overflow: 'hidden', marginBottom: '4px' }}>
                                                    <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: `${fillH}px`, background: `${col}40`, transition: 'height 0.4s' }} />
                                                  </div>
                                                  <div style={{ fontSize: '12px', fontWeight: 700, color: col }}>{displayVal}</div>
                                                  <div style={{ fontSize: '10px', color: 'hsl(var(--text-muted))' }}>{c.label}</div>
                                                </div>
                                              );
                                            })}
                                          </div>
                                        </div>
                                      );
                                    }
  
                                    // SymmetryDisplay renderer
                                    if (vt === 'SymmetryDisplay') {
                                      const sdShape = vp.shape || 'square';
                                      const sdAxis = vp.axis || 'vertical';
                                      const sdMode = vp.mode || 'show_axis';
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <svg width="140" height="120" viewBox="0 0 140 120">
                                            {sdShape === 'square' && <rect x="35" y="25" width="70" height="70" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" strokeWidth="2.5" rx="3"/>}
                                            {sdShape === 'isosceles_triangle' && <polygon points="70,15 20,105 120,105" fill="rgba(59,130,246,0.2)" stroke="#3b82f6" strokeWidth="2.5"/>}
                                            {sdShape === 'butterfly' && <>
                                              <path d="M70,60 C40,20 10,40 20,70 C30,90 60,75 70,60" fill="rgba(185,28,92,0.2)" stroke="#b91c5c" strokeWidth="2"/>
                                              <path d="M70,60 C100,20 130,40 120,70 C110,90 80,75 70,60" fill="rgba(185,28,92,0.2)" stroke="#b91c5c" strokeWidth="2"/>
                                            </>}
                                            {(sdMode === 'show_axis' || sdMode === 'complete') && sdAxis === 'vertical' && <line x1="70" y1="5" x2="70" y2="115" stroke="#d97706" strokeWidth="2" strokeDasharray="5,3"/>}
                                            {(sdMode === 'show_axis' || sdMode === 'complete') && sdAxis === 'horizontal' && <line x1="5" y1="60" x2="135" y2="60" stroke="#d97706" strokeWidth="2" strokeDasharray="5,3"/>}
                                          </svg>
                                          <div style={{ fontSize: '11px', color: '#d97706', marginTop: '4px' }}>{sdMode === 'show_axis' ? `${sdAxis} line of symmetry` : sdShape}</div>
                                        </div>
                                      );
                                    }
  
                                    // ProbabilityBag renderer — colored items in a bag
                                    if (vt === 'ProbabilityBag') {
                                      const pbItems = vp.items || []; // [{color, count, label?}]
                                      const pbHighlight = vp.highlight;
                                      const pbShowCounts = vp.show_counts !== false;
                                      const totalItems = pbItems.reduce((sum, it) => sum + (it.count || 0), 0);
                                      const colorMap = { red: '#ef4444', blue: '#3b82f6', green: '#22c55e', yellow: '#eab308', purple: '#a855f7', orange: '#f97316', white: '#f5f5f5', black: '#333' };
                                      // Generate circle positions in a "bag" shape
                                      const allCircles = [];
                                      pbItems.forEach((item) => {
                                        const c = colorMap[item.color] || item.color || '#888';
                                        for (let i = 0; i < (item.count || 0); i++) {
                                          allCircles.push({ color: c, label: item.label || item.color, isHighlighted: pbHighlight === item.color });
                                        }
                                      });
                                      // Shuffle for random placement
                                      for (let i = allCircles.length - 1; i > 0; i--) {
                                        const j = Math.floor(Math.random() * (i + 1));
                                        [allCircles[i], allCircles[j]] = [allCircles[j], allCircles[i]];
                                      }
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <svg width="160" height="130" viewBox="0 0 160 130">
                                            {/* Bag shape */}
                                            <path d="M30,30 Q30,10 50,10 L110,10 Q130,10 130,30 L135,110 Q135,125 115,125 L45,125 Q25,125 25,110 Z" fill="rgba(139,92,246,0.1)" stroke="#a78bfa" strokeWidth="2"/>
                                            <path d="M50,10 Q60,20 80,20 Q100,20 110,10" fill="none" stroke="#a78bfa" strokeWidth="2"/>
                                            {/* Items inside bag */}
                                            {allCircles.map((circ, idx) => {
                                              const cols = 4;
                                              const row = Math.floor(idx / cols);
                                              const col = idx % cols;
                                              const cx = 45 + col * 23 + (row % 2 === 0 ? 0 : 11);
                                              const cy = 45 + row * 22;
                                              return (
                                                <circle key={idx} cx={cx} cy={cy} r={9} fill={circ.color} stroke={circ.isHighlighted ? '#fbbf24' : 'rgba(255,255,255,0.3)'} strokeWidth={circ.isHighlighted ? 3 : 1.5}/>
                                              );
                                            })}
                                          </svg>
                                          {pbShowCounts && (
                                            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', marginTop: '8px', fontSize: '12px' }}>
                                              {pbItems.map((item, idx) => (
                                                <span key={idx} style={{ color: colorMap[item.color] || item.color, fontWeight: pbHighlight === item.color ? 800 : 500 }}>
                                                  {item.count} {item.label || item.color}
                                                </span>
                                              ))}
                                            </div>
                                          )}
                                        </div>
                                      );
                                    }
  
                                    // CoinDisplay renderer — simple heads/tails circles
                                    if (vt === 'CoinDisplay') {
                                      const cdShowBoth = vp.show_both !== false;
                                      const cdResult = vp.result; // 'heads' or 'tails' or undefined
                                      return (
                                        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(6,182,212,0.04)', border: '1px solid rgba(6,182,212,0.15)', textAlign: 'center' }}>
                                          <div style={{ display: 'flex', gap: '24px', justifyContent: 'center', alignItems: 'center' }}>
                                            {(cdShowBoth || cdResult === 'heads') && (
                                              <div style={{ textAlign: 'center' }}>
                                                <div style={{ width: '60px', height: '60px', borderRadius: '50%', background: 'linear-gradient(135deg, #fbbf24, #d97706)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: 800, color: '#fff', border: cdResult === 'heads' ? '4px solid #22c55e' : '3px solid rgba(255,255,255,0.3)' }}>H</div>
                                                <div style={{ fontSize: '11px', color: '#d97706', marginTop: '4px' }}>Heads</div>
                                              </div>
                                            )}
                                            {(cdShowBoth || cdResult === 'tails') && (
                                              <div style={{ textAlign: 'center' }}>
                                                <div style={{ width: '60px', height: '60px', borderRadius: '50%', background: 'linear-gradient(135deg, #94a3b8, #64748b)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: 800, color: '#fff', border: cdResult === 'tails' ? '4px solid #22c55e' : '3px solid rgba(255,255,255,0.3)' }}>T</div>
                                                <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>Tails</div>
                                              </div>
                                            )}
                                          </div>
                                          {cdShowBoth && !cdResult && <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', marginTop: '8px' }}>Each has an equal chance</div>}
                                        </div>
                                      );
                                    }
  
                                    // Fallback: show type name with debug params (not raw JSON dump)
                                    return (
                                      <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(255,255,255,0.03)', border: '1px dashed rgba(255,255,255,0.1)', textAlign: 'center' }}>
                                        <div style={{ fontSize: '12px', color: '#d97706', fontWeight: 700, marginBottom: '4px' }}>{vt}</div>
                                        <div style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', maxHeight: '80px', overflow: 'auto', textAlign: 'left' }}>{JSON.stringify(vp, null, 2)}</div>
                                      </div>
                                    );
                                  })()}
  
                                  {/* Step counter */}
                                  <div style={{ marginTop: '16px', fontSize: '12px', color: 'hsl(var(--text-muted))' }}>
                                    Step {Math.min(introStepIndex + 1, totalSteps)} of {totalSteps}
                                  </div>
                                </div>
                              )}
                            </div>
  
                            {/* Navigation */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '16px' }}>
                              {/* Progress dots for slides */}
                              <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                                {ml.slides.map((_, idx) => (
                                  <div
                                    key={idx}
                                    onClick={() => { setIntroSlideIndex(idx); setIntroStepIndex(0); }}
                                    style={{
                                      width: idx === introSlideIndex ? '20px' : '8px',
                                      height: '8px',
                                      borderRadius: '4px',
                                      cursor: 'pointer',
                                      transition: 'all 0.2s ease',
                                      background: idx === introSlideIndex ? '#06b6d4' : 'rgba(255,255,255,0.15)',
                                    }}
                                  />
                                ))}
                                <span style={{ fontSize: '11px', color: 'hsl(var(--text-muted))', marginLeft: '8px' }}>
                                  slide {introSlideIndex + 1}/{totalSlides}
                                </span>
                              </div>
  
                              {/* Nav buttons */}
                              <div style={{ display: 'flex', gap: '10px' }}>
                                {/* Previous */}
                                <button
                                  onClick={() => {
                                    if (isWorkedExample && introStepIndex > 0) {
                                      setIntroStepIndex(introStepIndex - 1);
                                    } else if (introSlideIndex > 0) {
                                      setIntroSlideIndex(introSlideIndex - 1);
                                      setIntroStepIndex(0);
                                    } else if (introMiniLessonIndex > 0) {
                                      const prevMl = introContent.mini_lessons[introMiniLessonIndex - 1];
                                      setIntroMiniLessonIndex(introMiniLessonIndex - 1);
                                      setIntroSlideIndex(prevMl.slides.length - 1);
                                      setIntroStepIndex(0);
                                    }
                                  }}
                                  disabled={introMiniLessonIndex === 0 && introSlideIndex === 0 && introStepIndex === 0}
                                  style={{
                                    padding: '8px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                                    cursor: 'pointer', border: 'none',
                                    background: 'rgba(255,255,255,0.06)', color: 'hsl(var(--text-muted))',
                                  }}
                                >
                                  Previous
                                </button>
  
                                {/* Next */}
                                <button
                                  onClick={() => {
                                    if (isWorkedExample && introStepIndex < totalSteps - 1) {
                                      setIntroStepIndex(introStepIndex + 1);
                                    } else if (introSlideIndex < totalSlides - 1) {
                                      setIntroSlideIndex(introSlideIndex + 1);
                                      setIntroStepIndex(0);
                                    } else if (introMiniLessonIndex < totalMiniLessons - 1) {
                                      setIntroMiniLessonIndex(introMiniLessonIndex + 1);
                                      setIntroSlideIndex(0);
                                      setIntroStepIndex(0);
                                    }
                                  }}
                                  disabled={introMiniLessonIndex === totalMiniLessons - 1 && introSlideIndex === totalSlides - 1 && (!isWorkedExample || introStepIndex >= totalSteps - 1)}
                                  style={{
                                    padding: '8px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                                    cursor: 'pointer', border: 'none',
                                    background: '#06b6d4', color: '#fff',
                                  }}
                                >
                                  {isWorkedExample && introStepIndex < totalSteps - 1 ? 'Next Step' : 'Next'}
                                </button>
                              </div>
                            </div>
  
                            {/* Metadata */}
                            <div style={{ marginTop: '16px', fontSize: '11px', color: 'hsl(var(--text-muted))' }}>
                              Seed: {introContent.seed} | Interest: {introContent.interest_applied || 'none'}
                            </div>
                          </div>
                        );
                      })()}
      </>
    );
  };



  const handleParentLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/parent/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: parentPassword })
      });
      if (res.ok) {
        setParentLoggedIn(true);
        setParentError('');
        if (selectedStudent) {
          fetchParentAnalytics(selectedStudent.id);
        }
        // Pre-load OpenCode models if that backend is already configured
        if (aiBackend === 'opencode' && opencodeModels.length === 0) {
          setModelsLoading(true);
          fetch(`${API_BASE}/parent/opencode-models`)
            .then(r => r.json())
            .then(d => setOpencodeModels(d.models || []))
            .catch(() => {})
            .finally(() => setModelsLoading(false));
        }
      } else {
        setParentError("Invalid parent portal password.");
      }
    } catch (e) {
      setParentError("Connection failed.");
    }
  };

  const fetchParentGraph = async (studentId, grade) => {
    try {
      const url = grade ? `${API_BASE}/parent/graph/${studentId}?grade=${grade}` : `${API_BASE}/parent/graph/${studentId}`;
      const res = await fetch(url);
      const data = await res.json();
      setParentGraphData(data);
    } catch (e) {
      console.error("Failed to load dynamic graph", e);
    }
  };

  const fetchParentAnalytics = async (studentId) => {
    try {
      const res = await fetch(`${API_BASE}/parent/analytics/${studentId}`);
      const data = await res.json();
      setAnalyticsData(data);
      
      // Populate editable fields
      setEditName(data.name);
      setEditElo(data.elo_rating);
      setEditAge(data.age);
      setEditGrade(data.grade);
      setEditInterests(data.interest_tags);
      setEditTelemetryEnabled(data.telemetry_enabled);
      
      // Trigger loading grade-aligned graph dynamically
      setParentSelectedGrade(String(selectedStudent ? selectedStudent.grade : 5));
      fetchParentGraph(studentId, selectedStudent ? String(selectedStudent.grade) : '5');
    } catch (e) {
      console.error("Failed to load analytics", e);
    }
  };

  const handleUpdateSettings = async (e) => {
    e.preventDefault();
    if (!analyticsData) return;
    try {
      const res = await fetch(`${API_BASE}/parent/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: analyticsData.student_id,
          name: editName,
          age: editAge,
          grade: editGrade,
          language_preference: selectedStudent ? selectedStudent.language_preference : 'en',
          interest_tags: editInterests,
          elo_rating: parseFloat(editElo),
          telemetry_enabled: editTelemetryEnabled
        })
      });
      if (res.ok) {
        const updated = await res.json();
        setSelectedStudent(updated);
        fetchParentAnalytics(updated.id);
        fetchProfiles();
      }
    } catch (e) {
      console.error("Failed to update profile settings", e);
    }
  };

  const handleToggleParentAuth = async () => {
    const newValue = !parentAuthRequired;
    setParentAuthRequired(newValue);
    try {
      await fetch(`${API_BASE}/parent/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password_auth_required: newValue })
      });
    } catch (e) {
      console.error("Failed to update parent auth settings", e);
    }
  };

  const handleAiBackendChange = async (newBackend) => {
    setAiBackend(newBackend);
    if (newBackend === 'opencode' && opencodeModels.length === 0) {
      setModelsLoading(true);
      try {
        const res = await fetch(`${API_BASE}/parent/opencode-models`);
        const data = await res.json();
        setOpencodeModels(data.models || []);
      } catch (e) {
        console.error("Failed to fetch OpenCode models", e);
      } finally {
        setModelsLoading(false);
      }
    }
    // Send both ai_backend AND the current model together so they stay in sync
    try {
      await fetch(`${API_BASE}/parent/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ai_backend: newBackend, opencode_model: opencodeModel }),
      });
    } catch (e) {
      console.error("Failed to save AI backend setting", e);
    }
  };

  const handleOpencodeModelChange = async (newModel) => {
    setOpencodeModel(newModel);
    // Always send both ai_backend and model together to ensure full propagation
    try {
      await fetch(`${API_BASE}/parent/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ai_backend: 'opencode', opencode_model: newModel }),
      });
      // Also update local state to ensure UI reflects opencode is active
      setAiBackend('opencode');
    } catch (e) {
      console.error("Failed to save OpenCode model setting", e);
    }
  };

  // Logout/Reset Session
  const handleLogout = async () => {
    if (selectedStudent && telemetrySessionId) {
      await syncTelemetry(0, 0, 0, 0, true); // End session
    }
    setSelectedStudent(null);
    setCurrentView('login');
    setTelemetrySessionId(null);
    setParentLoggedIn(false);
    setParentPassword('');
    setParentError('');
    setEditName('');
    setEditElo(1200);
    setEditAge(10);
    setEditGrade(5);
    setEditInterests('');
  };

  // Toggle Language
  const toggleLanguage = async () => {
    if (!selectedStudent) return;
    const newLang = selectedStudent.language_preference === 'en' ? 'tl' : 'en';
    
    // Quick API update
    try {
      const res = await fetch(`${API_BASE}/parent/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: selectedStudent.id,
          name: selectedStudent.name,
          age: selectedStudent.age,
          grade: selectedStudent.grade,
          language_preference: newLang,
          interest_tags: selectedStudent.interest_tags,
          telemetry_enabled: selectedStudent.telemetry_enabled
        })
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedStudent(data);
        fetchNextQuestion(data.id, selectedSubject, selectedSubdomain, true);
      }
    } catch (e) {
      console.error("Language change failed", e);
    }
  };

  return (
    <div className="app-container">
      {/* Navigation Menu */}
      <nav className="nav-bar">
        <div className="nav-brand">
          <BookOpen className="w-8 h-8" />
          <span>CCMed Mastery Engine</span>
        </div>
        
        <div className="flex items-center gap-6" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {selectedStudent && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
              {/* Telemetry Indicator */}
              <div 
                className="glass-card hover-glow" 
                onClick={() => setShowTelemetryModal(true)}
                style={{ 
                  padding: '8px 16px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '10px', 
                  borderRadius: '12px', 
                  cursor: 'pointer', 
                  transition: 'var(--transition-smooth)',
                  opacity: selectedStudent.telemetry_enabled ? 1 : 0.65
                }}
              >
                {selectedStudent.telemetry_enabled ? (
                  <>
                    <div className="telemetry-pulse"></div>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#10b981' }}>Telemetry Shield</span>
                  </>
                ) : (
                  <>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#64748b' }}></div>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8' }}>Telemetry Shield: OFF</span>
                  </>
                )}
              </div>

              {/* Language Switch */}
              <button 
                className="btn-secondary" 
                onClick={toggleLanguage}
                style={{ padding: '8px 16px', borderRadius: '12px', fontSize: '13px', display: 'flex', gap: '6px' }}
              >
                <Globe className="w-4 h-4" />
                <span>{selectedStudent.language_preference === 'en' ? 'English 🇺🇸' : 'Tagalog 🇵🇭'}</span>
              </button>

              {/* Sound Toggle */}
              <button
                className="btn-secondary"
                onClick={toggleSound}
                style={{ 
                  padding: '8px 16px', 
                  borderRadius: '12px', 
                  fontSize: '13px', 
                  display: 'flex', 
                  gap: '6px',
                  opacity: soundEnabled ? 1 : 0.65
                }}
                title={soundEnabled ? 'Sound effects on' : 'Sound effects off'}
              >
                {soundEnabled ? (
                  <>
                    <Volume2 className="w-4 h-4" />
                    <span>Sound On</span>
                  </>
                ) : (
                  <>
                    <VolumeX className="w-4 h-4" />
                    <span>Sound Off</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* View Toggles */}
          {currentView === 'login' ? (
             <button className="btn-secondary" onClick={async () => {
               try {
                 const res = await fetch(`${API_BASE}/parent/config`);
                 const config = await res.json();
                 setParentAuthRequired(config.password_auth_required);
                 setAiBackend(config.ai_backend || 'gemini');
                 setOpencodeModel(config.opencode_model || 'opencode/deepseek-v4-flash-free');
                 // Auto-load models list when entering parent portal with opencode active
                 if (config.ai_backend === 'opencode' && opencodeModels.length === 0) {
                   fetch(`${API_BASE}/parent/opencode-models`)
                     .then(r => r.json())
                     .then(d => setOpencodeModels(d.models || []))
                     .catch(() => {});
                 }
                 if (!config.password_auth_required) {
                   setParentLoggedIn(true);
                 } else {
                   setParentLoggedIn(false);
                 }
               } catch (e) {
                 console.error("Failed to fetch parent config on entry", e);
               }
               setCurrentView('parent');
               if (selectedStudent) {
                 fetchParentAnalytics(selectedStudent.id);
               }
             }}>
               <Settings className="w-5 h-5" />
               <span>Parent Portal</span>
             </button>
          ) : (
            <button className="btn-secondary" onClick={handleLogout}>
              <User className="w-5 h-5" />
              <span>Exit Portal</span>
            </button>
          )}
        </div>
      </nav>

      {/* Telemetry Active Screen warning alerts */}
      {telemetryWarning && (
        <div style={{ 
          background: 'rgba(239, 68, 68, 0.15)', 
          borderBottom: '1px solid #ef4444', 
          padding: '10px 40px', 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px',
          color: '#fca5a5',
          fontSize: '14px',
          fontWeight: 600
        }}>
          <AlertTriangle className="w-5 h-5 text-red-400" style={{ color: '#ef4444' }} />
          <span>{telemetryWarning}</span>
        </div>
      )}

      {/* MAIN LAYOUTS */}
      <main style={{ flex: 1, padding: '40px', maxWidth: '1400px', width: '100%', margin: '0 auto' }}>
        
        {/* --- VIEW 1: LOGIN & SEEDING PROFILE SCREEN --- */}
        {currentView === 'login' && (
          <>
            {/* Select Profile & PIN Entry */}
            <div className="glass-card">
              <h2 style={{ fontSize: '28px', marginBottom: '15px' }}>Enter Student Portal</h2>
              
              {students.length === 0 ? (
                <p style={{ color: 'hsl(var(--text-muted))', marginBottom: '20px' }}>No student profiles created yet. Create one below!</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', marginBottom: '25px' }}>
                  <label style={{ fontSize: '14px', fontWeight: 600, color: 'hsl(var(--text-muted))' }}>Select Student</label>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    {students.map(std => (
                      <button 
                        key={std.id}
                        onClick={() => handleSelectStudent(std)}
                        className={`option-btn ${selectedStudent?.id === std.id ? 'correct' : ''}`}
                        style={{ padding: '12px 18px', display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '4px' }}
                      >
                        <span style={{ fontWeight: 700 }}>{std.name}</span>
                        <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))' }}>Grade {std.grade} • ELO: {std.elo_rating}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {selectedStudent && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', animation: 'slide-up 0.3s ease-out' }}>
                  <label style={{ fontSize: '14px', fontWeight: 600 }}>Enter 4-6 digit numeric PIN to unlock:</label>
                  <input 
                    type="password" 
                    className="premium-input" 
                    placeholder="••••"
                    value={pinInput}
                    onChange={(e) => setPinInput(e.target.value)}
                    maxLength={6}
                    style={{ letterSpacing: '8px', textAlign: 'center', fontSize: '20px' }}
                  />
                  {pinError && <p style={{ color: '#fca5a5', fontSize: '13px' }}>{pinError}</p>}
                  <button className="btn-primary" onClick={() => handleStudentLogin(selectedStudent.id)} style={{ marginTop: '10px' }}>
                    <Lock className="w-5 h-5" />
                    <span>Unlock Portal</span>
                  </button>
                </div>
              )}

              {/* Onboarding Register profile manual */}
              <div style={{ marginTop: '40px', paddingTop: '30px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <h3 style={{ fontSize: '20px', marginBottom: '15px' }}>Create New Profile</h3>
                <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <input 
                    type="text" 
                    className="premium-input" 
                    placeholder="Student Full Name"
                    value={regName}
                    onChange={(e) => setRegName(e.target.value)}
                  />
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <input 
                      type="password" 
                      className="premium-input" 
                      placeholder="PIN (4-6 digits)"
                      value={regPin}
                      onChange={(e) => setRegPin(e.target.value)}
                      maxLength={6}
                    />
                    <input 
                      type="number" 
                      className="premium-input" 
                      placeholder="Age"
                      value={regAge}
                      onChange={(e) => setRegAge(e.target.value)}
                    />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                    <select 
                      className="premium-input" 
                      value={regGrade}
                      onChange={(e) => setRegGrade(e.target.value)}
                      style={{ background: 'rgba(0,0,0,0.4)', color: '#f8fafc', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', height: '42px', padding: '0 12px', fontSize: '14px' }}
                    >
                      <option value="0" style={{ background: '#0f172a' }}>Kindergarten (Grade 0)</option>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(g => (
                        <option key={g} value={g} style={{ background: '#0f172a' }}>Grade {g}</option>
                      ))}
                    </select>
                    <input 
                      type="text" 
                      className="premium-input" 
                      placeholder="Interests (comma separated)"
                      value={regInterests}
                      onChange={(e) => setRegInterests(e.target.value)}
                    />
                  </div>
                  <button type="submit" className="btn-secondary">Create Profile</button>
                </form>
              </div>
            </div>
        </>
      )}

        {/* --- VIEW 2: PRACTICE WORKSPACE SCREEN (WITH SOCRATIC SPLIT SCREEN) --- */}
        {/* --- VIEW 2: PRACTICE WORKSPACE SCREEN (WITH SOCRATIC SPLIT SCREEN) --- */}
        {currentView === 'practice' && selectedStudent && (
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
                          if (chatMessages.length === 0) {
                            const greeting = selectedStudent.language_preference === 'tl'
                              ? "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Paano kita matutulungan sa araling ito?"
                              : "Praise God and the Lord Jesus Christ, I'm your tutor today. How can I help you with this lesson?";
                            setChatMessages([
                              { role: 'assistant', content: greeting }
                            ]);
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
                    {aiBackend === 'opencode'
                      ? `OpenCode (${opencodeModel}) is generating a personalized story narrative...`
                      : 'Gemini CLI subagent is orchestrating a personalized story narrative...'}
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
                          if (chatMessages.length === 0) {
                            const greeting = selectedStudent.language_preference === 'tl'
                              ? "Purihin ang Diyos at ang Panginoong Hesukristo, ako ang iyong tutor ngayon. Paano kita matutulungan?"
                              : "Praise God and the Lord Jesus Christ, I'm your tutor today. How can I help you?";
                            setChatMessages([
                              { role: 'assistant', content: greeting }
                            ]);
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

                  {/* Worked Example Scaffolded decompositions (alternates when struggling) */}
                  {activeQuestion.is_worked_example && activeQuestion.worked_example_steps && (
                    <div className="glass-card" style={{ borderLeft: '4px solid hsl(var(--warning))', background: 'rgba(245, 158, 11, 0.05)', marginBottom: '30px', padding: '20px' }}>
                      <h4 style={{ color: '#fbbf24', display: 'flex', gap: '6px', alignItems: 'center', marginBottom: '10px' }}>
                        <Zap className="w-5 h-5" />
                        <span>Worked Example Guidance Scaffold Active</span>
                      </h4>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '15px' }}>
                        {activeQuestion.worked_example_steps.map((step, idx) => (
                          <div key={idx} style={{ padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
                            {step}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Visual Question Rendering OR MCQ Options */}
                  {activeQuestion.is_visual ? (
                    /* Visual Question Rendering */
                    <div style={{ marginBottom: '30px' }}>
                      {activeQuestion.visual_type === 'SortOrder' || activeQuestion.question_mode === 'ordering' ? (
                        <SortOrderInteractive 
                          params={activeQuestion.visual_params}
                          onAnswer={(answer) => setPracticeVisualAnswer(answer)}
                          disabled={!!answerResult}
                        />
                      ) : activeQuestion.answer_collection === 'mcq' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
                          {renderVisualInner(
                            activeQuestion.visual_type,
                            { ...activeQuestion.visual_params, is_interactive: false },
                            () => {},
                            true,
                            activeQuestion.skeleton_id
                          )}
                          {(activeQuestion.mcq_options || activeQuestion.options) && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', maxWidth: '400px' }}>
                              {(activeQuestion.mcq_options || activeQuestion.options).map(opt => {
                                const isSelected = practiceVisualAnswer === opt.key;
                                const isCorrectOpt = answerResult && opt.key === answerResult.correct_answer;
                                const isWrong = answerResult && isSelected && !answerResult.is_correct;
                                return (
                                  <button
                                    key={opt.key}
                                    className={`option-btn ${isWrong ? 'incorrect' : isCorrectOpt ? 'correct' : isSelected ? 'correct' : ''}`}
                                    onClick={() => { if (!answerResult) setPracticeVisualAnswer(opt.key); }}
                                    disabled={!!answerResult}
                                    style={{ textAlign: 'left' }}
                                  >
                                    <div className="option-badge">{isSelected && !answerResult ? '✓' : opt.key}</div>
                                    <span>{renderMath(opt.text || String(opt.value || ''))}</span>
                                  </button>
                                );
                              })}
                            </div>
                          )}
                          {answerResult && activeQuestion.visual_params?.reveal_display && (
                            <div style={{ 
                              marginTop: '12px', 
                              padding: '16px', 
                              background: answerResult.is_correct ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', 
                              borderRadius: '8px',
                              textAlign: 'center',
                            }}>
                              <div style={{ fontSize: '28px', letterSpacing: '4px', marginBottom: '8px' }}>
                                {activeQuestion.visual_params.reveal_display}
                              </div>
                              {activeQuestion.visual_params.reveal_text && (
                                <div style={{ fontSize: '16px', color: '#94a3b8' }}>
                                  {activeQuestion.visual_params.reveal_text} left
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ) : activeQuestion.visual_params?.is_interactive ? (
                        renderVisualInner(
                          activeQuestion.visual_type,
                          activeQuestion.visual_params,
                          (answer) => setPracticeVisualAnswer(answer),
                          !!answerResult,
                          activeQuestion.skeleton_id
                        )
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
                          {renderVisualInner(
                            activeQuestion.visual_type,
                            { ...activeQuestion.visual_params, is_interactive: false },
                            () => {},
                            true,
                            activeQuestion.skeleton_id
                          )}
                          <input
                            type="text"
                            className="premium-input"
                            placeholder="Enter your answer..."
                            value={practiceVisualAnswer ?? ''}
                            onChange={e => setPracticeVisualAnswer(e.target.value)}
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
                      {(activeQuestion.question_mode === 'cloze' || activeQuestion.question_mode === 'fill_in_blank') && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '300px' }}>
                          <input
                            type="text"
                            className="premium-input"
                            placeholder="Fill in the blank..."
                            value={practiceVisualAnswer ?? ''}
                            onChange={e => setPracticeVisualAnswer(e.target.value)}
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
                      {(activeQuestion.question_mode === 'numeric_input' || activeQuestion.question_mode === 'integer' || activeQuestion.question_mode === 'decimal') && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '300px' }}>
                          <input
                            type="number"
                            className="premium-input"
                            placeholder="Enter your answer..."
                            value={practiceVisualAnswer ?? ''}
                            onChange={e => setPracticeVisualAnswer(e.target.value)}
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

                      {/* True/False format */}
                      {activeQuestion.question_mode === 'true_false' && (
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', width: '100%', maxWidth: '400px' }}>
                          {['True', 'False'].map(val => {
                            const isSelected = practiceVisualAnswer === val;
                            const isCorrect = answerResult && answerResult.is_correct && isSelected;
                            const isWrong = answerResult && !answerResult.is_correct && isSelected;
                            const isCorrectAnswer = answerResult && !answerResult.is_correct && String(activeQuestion.correct_answer) === val;
                            return (
                              <button
                                key={val}
                                className={`option-btn ${isWrong ? 'incorrect' : (isCorrect || isCorrectAnswer) ? 'correct' : isSelected ? 'selected' : ''}`}
                                onClick={() => { if (!answerResult) setPracticeVisualAnswer(val); }}
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
                      {activeQuestion.question_mode === 'ordering' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '400px' }}>
                          <p style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', margin: 0, textAlign: 'center' }}>
                            Enter the values in the correct order, separated by commas:
                          </p>
                          <input
                            type="text"
                            className="premium-input"
                            placeholder="e.g., 1, 2, 3, 4"
                            value={practiceVisualAnswer ?? ''}
                            onChange={e => setPracticeVisualAnswer(e.target.value)}
                            disabled={!!answerResult}
                            style={{ 
                              padding: '14px 16px', 
                              fontSize: '16px', 
                              textAlign: 'center',
                              borderRadius: '10px',
                            }}
                          />
                        </div>
                      )}

                      {/* Error detect format */}
                      {activeQuestion.question_mode === 'error_detect' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%', maxWidth: '400px' }}>
                          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                            <button
                              className={`option-btn ${practiceVisualAnswer?.has_error === false ? 'correct' : ''}`}
                              onClick={() => { if (!answerResult) setPracticeVisualAnswer({ has_error: false, correct_value: '' }); }}
                              disabled={!!answerResult}
                              style={{ flex: 1, padding: '14px', fontSize: '16px', fontWeight: 600 }}
                            >
                              Yes, correct
                            </button>
                            <button
                              className={`option-btn ${practiceVisualAnswer?.has_error === true ? 'correct' : ''}`}
                              onClick={() => { if (!answerResult) setPracticeVisualAnswer({ has_error: true, correct_value: '' }); }}
                              disabled={!!answerResult}
                              style={{ flex: 1, padding: '14px', fontSize: '16px', fontWeight: 600 }}
                            >
                              No, incorrect
                            </button>
                          </div>
                          {practiceVisualAnswer?.has_error === true && (
                            <input
                              type="number"
                              className="premium-input"
                              placeholder="What is the correct answer?"
                              value={practiceVisualAnswer?.correct_value ?? ''}
                              onChange={e => setPracticeVisualAnswer({ ...practiceVisualAnswer, correct_value: e.target.value })}
                              disabled={!!answerResult}
                              style={{ 
                                padding: '14px 16px', 
                                fontSize: '18px', 
                                textAlign: 'center',
                                fontWeight: 600,
                                borderRadius: '10px',
                              }}
                            />
                          )}
                        </div>
                      )}

                      {/* Default MCQ format */}
                      {(!activeQuestion.question_mode || activeQuestion.question_mode === 'mcq') && activeQuestion.options && activeQuestion.options.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', maxWidth: '400px' }}>
                          {activeQuestion.options.map(opt => {
                            let btnClass = '';
                            if (answerResult) {
                              if (opt.key === answerResult.correct_answer) btnClass = 'correct';
                              else if (opt.key === selectedOptionKey) btnClass = 'incorrect';
                            } else if (selectedOptionKey === opt.key) {
                              btnClass = 'correct';
                            }
                            return (
                              <button
                                key={opt.key}
                                className={`option-btn ${btnClass}`}
                                onClick={() => handleOptionClick(opt.key)}
                                disabled={!!answerResult}
                                style={{ textAlign: 'left' }}
                              >
                                <div className="option-badge">{opt.key}</div>
                                <span>{renderMath(opt.text)}</span>
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  )}

                  {/* MCQ/Visual Submit/Result — only for non-writing mode */}
                  {activeQuestion.question_mode !== 'writing_prompt' && (<div>
                  {!answerResult ? (
                    <button
                      className="btn-primary"
                      onClick={handleAnswerSubmit}
                      disabled={
                        (!activeQuestion.is_visual && (!activeQuestion.question_mode || activeQuestion.question_mode === 'mcq')) 
                          ? !selectedOptionKey 
                          : (practiceVisualAnswer === null || practiceVisualAnswer === undefined || practiceVisualAnswer === '')
                      }
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
      )}

        {/* --- VIEW 3: PARENT CONTROL PANEL SCREEN --- */}
        {currentView === 'parent' && (() => {
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

                      {/* Backend selector tiles */}
                      <div style={{ display: 'flex', gap: '12px' }}>
                        {/* Gemini CLI tile */}
                        <div
                          onClick={() => handleAiBackendChange('gemini')}
                          style={{
                            flex: 1,
                            padding: '14px 16px',
                            borderRadius: '12px',
                            border: `2px solid ${aiBackend === 'gemini' ? '#10b981' : 'rgba(255,255,255,0.08)'}`,
                            background: aiBackend === 'gemini' ? 'rgba(16,185,129,0.08)' : 'rgba(255,255,255,0.03)',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            boxShadow: aiBackend === 'gemini' ? '0 0 14px rgba(16,185,129,0.25)' : 'none',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <div style={{
                              width: '14px', height: '14px', borderRadius: '50%',
                              border: `2px solid ${aiBackend === 'gemini' ? '#10b981' : 'rgba(255,255,255,0.3)'}`,
                              background: aiBackend === 'gemini' ? '#10b981' : 'transparent',
                              flexShrink: 0,
                            }} />
                            <span style={{ fontWeight: 600, fontSize: '15px', color: 'hsl(var(--text-main))' }}>Gemini CLI</span>
                          </div>
                          <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', paddingLeft: '22px' }}>
                            gemini-2.5-flash-lite · ACP bridge
                          </span>
                        </div>

                        {/* OpenCode tile */}
                        <div
                          onClick={() => handleAiBackendChange('opencode')}
                          style={{
                            flex: 1,
                            padding: '14px 16px',
                            borderRadius: '12px',
                            border: `2px solid ${aiBackend === 'opencode' ? '#a78bfa' : 'rgba(255,255,255,0.08)'}`,
                            background: aiBackend === 'opencode' ? 'rgba(167,139,250,0.08)' : 'rgba(255,255,255,0.03)',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            boxShadow: aiBackend === 'opencode' ? '0 0 14px rgba(167,139,250,0.25)' : 'none',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                            <div style={{
                              width: '14px', height: '14px', borderRadius: '50%',
                              border: `2px solid ${aiBackend === 'opencode' ? '#a78bfa' : 'rgba(255,255,255,0.3)'}`,
                              background: aiBackend === 'opencode' ? '#a78bfa' : 'transparent',
                              flexShrink: 0,
                            }} />
                            <span style={{ fontWeight: 600, fontSize: '15px', color: 'hsl(var(--text-main))' }}>OpenCode</span>
                          </div>
                          <span style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', paddingLeft: '22px' }}>
                            Any provider · select model below
                          </span>
                        </div>
                      </div>

                      {/* Model selector — shown only when OpenCode is selected */}
                      {aiBackend === 'opencode' && (
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
                                Active: <strong style={{ color: '#a78bfa' }}>{opencodeModel}</strong>
                              </span>
                            </>
                          )}
                        </div>
                      )}
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

                                  {/* Spine dropdown rendered below context dropdown */}
                                  {(() => {
                                    const spineVariant = labConfig.contextual_variants.find(v => v.name === 'spine');
                                    const contextVariant = labConfig.contextual_variants.find(v => v.name === 'context');
                                    const contextVal = contextVariant ? (labVariantValues['context'] || contextVariant.default) : null;
                                    const showSpine = spineVariant && contextVal === 'word_problem';
                                    if (!showSpine) return null;

                                    const selectedFormatter = labConfig.formatters?.find(f => f.name === labSelectedFormatter);
                                    const restrictions = selectedFormatter?.variant_restrictions;
                                    const spineVal = labVariantValues[spineVariant.name] || spineVariant.default;
                                    const isSpineRestricted = restrictions && restrictions[spineVariant.name] && !restrictions[spineVariant.name].includes(spineVal);

                                    return (
                                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxWidth: '200px' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                          <label style={{ fontSize: '11px', fontWeight: 700, color: 'hsl(var(--text-muted))', letterSpacing: '0.06em' }}>
                                            {spineVariant.label.toUpperCase()}
                                          </label>
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
                          <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(255,255,255,0.06)', color: 'hsl(var(--text-muted))', fontWeight: 600 }}>
difficulty: {Math.round(matatagQuestion.difficulty * 100)}%
                          </span>
                        </div>

                        {/* Active axis values summary */}
                        {Object.keys(matatagAxisValues).length > 0 && (
                          <div style={{ marginBottom: '16px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                            {Object.entries(matatagAxisValues).map(([k, v]) => (
                              <span key={k} style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(255,255,255,0.06)', color: 'hsl(var(--text-muted))' }}>
                                {k}: <strong style={{ color: 'hsl(var(--text))' }}>{v}</strong>
                              </span>
                            ))}
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

                        {/* Visual interactive component */}
                        <div style={{ marginBottom: '24px' }}>
                          {matatagQuestion.is_visual && (
                            <>
                              {matatagQuestion.visual_type === 'SortOrder' || matatagQuestion.question_mode === 'ordering' ? (
                                <SortOrderInteractive params={matatagQuestion.visual_params} onAnswer={setMatatagAnswer} disabled={!!matatagResult} />
                              ) : matatagQuestion.visual_type === 'NumberBond' ? (
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                                  {/* Number bond diagram: whole on top, two parts below, lines edge-to-edge */}
                                  <svg width="200" height="140" viewBox="0 0 200 140" style={{ overflow: 'visible' }}>
                                    {/* Lines from circle edge to circle edge */}
                                    <line x1="85.8" y1="54.1" x2="62.2" y2="94.3" stroke="#6366f1" strokeWidth="2.5" />
                                    <line x1="114.2" y1="54.1" x2="137.8" y2="94.3" stroke="#6366f1" strokeWidth="2.5" />
                                    
                                    {/* Whole circle (top) */}
                                    <circle cx="100" cy="30" r="28" fill={matatagQuestion.visual_params?.blank_position === 'whole' ? 'rgba(99,102,241,0.15)' : 'transparent'} stroke="#6366f1" strokeWidth="3" />
                                    <text x="100" y="36" textAnchor="middle" fill="#f1f5f9" fontSize="20" fontWeight="700">
                                      {matatagQuestion.visual_params?.blank_position === 'whole' ? '?' : matatagQuestion.visual_params?.whole}
                                    </text>
                                    
                                    {/* Part1 circle (bottom-left) */}
                                    <circle cx="50" cy="115" r="24" fill={matatagQuestion.visual_params?.blank_position === 'part1' ? 'rgba(16,185,129,0.15)' : 'transparent'} stroke="#10b981" strokeWidth="3" />
                                    <text x="50" y="121" textAnchor="middle" fill="#f1f5f9" fontSize="18" fontWeight="700">
                                      {matatagQuestion.visual_params?.blank_position === 'part1' ? '?' : matatagQuestion.visual_params?.part1}
                                    </text>
                                    
                                    {/* Part2 circle (bottom-right) */}
                                    <circle cx="150" cy="115" r="24" fill={matatagQuestion.visual_params?.blank_position === 'part2' ? 'rgba(16,185,129,0.15)' : 'transparent'} stroke="#10b981" strokeWidth="3" />
                                    <text x="150" y="121" textAnchor="middle" fill="#f1f5f9" fontSize="18" fontWeight="700">
                                      {matatagQuestion.visual_params?.blank_position === 'part2' ? '?' : matatagQuestion.visual_params?.part2}
                                    </text>
                                  </svg>
                                  {/* Input field for the missing value */}
                                  <input
                                    type="number"
                                    className="premium-input"
                                    placeholder="Enter the missing number..."
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
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
                              ) : matatagQuestion.answer_collection === 'mcq' ? (
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
                                  {renderVisualInner(
                                    matatagQuestion.visual_type,
                                    { ...matatagQuestion.visual_params, is_interactive: false },
                                    () => {},
                                    true,
                                    matatagQuestion.problem_id || matatagQuestion.skeleton_id
                                  )}
                                  {(matatagQuestion.format_data?.mcq_options || matatagQuestion.mcq_options) && (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', width: '100%', maxWidth: '400px' }}>
                                      {(matatagQuestion.format_data?.mcq_options || matatagQuestion.mcq_options).map(opt => {
                                        const isSelected = matatagAnswer === opt.key;
                                        const isCorrectOpt = matatagResult && (opt.value === parseInt(matatagResult.correct_answer) || opt.is_correct || opt.key === matatagResult.correct_answer);
                                        const isWrong = matatagResult && isSelected && !matatagResult.is_correct;
                                        return (
                                          <button
                                            key={opt.key}
                                            className={`option-btn ${isWrong ? 'incorrect' : isCorrectOpt ? 'correct' : isSelected ? 'correct' : ''}`}
                                            onClick={() => { if (!matatagResult) setMatatagAnswer(opt.key); }}
                                            disabled={!!matatagResult}
                                            style={{ textAlign: 'left' }}
                                          >
                                            <div className="option-badge">{isSelected && !matatagResult ? '✓' : opt.key}</div>
                                            <span>{opt.text || opt.value}</span>
                                          </button>
                                        );
                                      })}
                                    </div>
                                  )}
                                  {matatagResult && matatagQuestion.visual_params?.reveal_display && (
                                    <div style={{ 
                                      marginTop: '12px', 
                                      padding: '16px', 
                                      background: matatagResult.is_correct ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', 
                                      borderRadius: '8px',
                                      textAlign: 'center',
                                    }}>
                                      <div style={{ fontSize: '28px', letterSpacing: '4px', marginBottom: '8px' }}>
                                        {matatagQuestion.visual_params.reveal_display}
                                      </div>
                                      {matatagQuestion.visual_params.reveal_text && (
                                        <div style={{ fontSize: '16px', color: '#94a3b8' }}>
                                          {matatagQuestion.visual_params.reveal_text} left
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              ) : matatagQuestion.visual_params?.is_interactive ? (
                                renderVisualInner(
                                  matatagQuestion.visual_type,
                                  matatagQuestion.visual_params,
                                  (answer) => setMatatagAnswer(answer),
                                  !!matatagResult,
                                  matatagQuestion.problem_id || matatagQuestion.skeleton_id
                                )
                              ) : (
                                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', width: '100%' }}>
                                  {renderVisualInner(
                                    matatagQuestion.visual_type,
                                    { ...matatagQuestion.visual_params, is_interactive: false },
                                    () => {},
                                    true,
                                    matatagQuestion.problem_id || matatagQuestion.skeleton_id
                                  )}
                                  <input
                                    type="text"
                                    className="premium-input"
                                    placeholder="Enter your answer..."
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
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

                              {/* Fallback for other visual types with fill_in_blank answer collection */}
                              {!['NumberLine', 'ClockSet', 'PesoMoney', 'FillInTable', 'RuleDiscovery', 'BarChart', 'SortOrder', 'GridArea', 'Categorize', 'Calendar', 'NumberBond', 'EmojiPictorial', 'PlaceValueBlocks'].includes(matatagQuestion.visual_type) && 
                               matatagQuestion.answer_collection === 'fill_in_blank' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  <input
                                    type="text"
                                    className="premium-input"
                                    placeholder="Enter your answer..."
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
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
                            </>
                          )}

                          {/* Format-specific answer input (non-visual) */}
                          {!matatagQuestion.is_visual && (
                            <>
                              {/* MCQ format */}
                              {matatagQuestion.format === 'mcq' && matatagQuestion.mcq_options && matatagQuestion.mcq_options.length > 0 && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                  {matatagQuestion.mcq_options.map(opt => {
                                    const isSelected = matatagAnswer === opt.key;
                                    const isCorrectOpt = matatagResult && opt.text === matatagResult.correct_answer;
                                    const isWrong = matatagResult && isSelected && !matatagResult.is_correct;
                                    return (
                                      <button
                                        key={opt.key}
                                        className={`option-btn ${isWrong ? 'incorrect' : isCorrectOpt ? 'correct' : isSelected ? 'correct' : ''}`}
                                        onClick={() => { if (!matatagResult) setMatatagAnswer(opt.key); }}
                                        disabled={!!matatagResult}
                                        style={{ textAlign: 'left' }}
                                      >
                                        <div className="option-badge">{isSelected && !matatagResult ? '✓' : opt.key}</div>
                                        <span>{opt.text}</span>
                                      </button>
                                    );
                                  })}
                                </div>
                              )}

                              {/* Numeric input format */}
                              {(matatagQuestion.format === 'numeric_input' || matatagQuestion.answer_collection === 'numeric_input') && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  <input
                                    type="number"
                                    className="premium-input"
                                    placeholder="Enter your answer..."
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
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

                              {/* Cloze / fill-in-blank format */}
                              {(matatagQuestion.format === 'cloze' || matatagQuestion.answer_collection === 'fill_in_blank') && 
                               matatagQuestion.format !== 'numeric_input' && 
                               matatagQuestion.interaction_mode !== 'set' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  <input
                                    type="text"
                                    className="premium-input"
                                    placeholder="Fill in the blank..."
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
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

                              {/* True/False format */}
                              {matatagQuestion.format === 'true_false' && (
                                <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                                  {['True', 'False'].map(val => {
                                    const isSelected = matatagAnswer === val;
                                    const isCorrect = matatagResult && matatagResult.is_correct && isSelected;
                                    const isWrong = matatagResult && !matatagResult.is_correct && isSelected;
                                    const isCorrectAnswer = matatagResult && !matatagResult.is_correct && String(matatagQuestion.correct_answer) === val;
                                    return (
                                      <button
                                        key={val}
                                        className={`option-btn ${isWrong ? 'incorrect' : (isCorrect || isCorrectAnswer) ? 'correct' : isSelected ? 'selected' : ''}`}
                                        onClick={() => { if (!matatagResult) setMatatagAnswer(val); }}
                                        disabled={!!matatagResult}
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
                              {matatagQuestion.format === 'ordering' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  <p style={{ fontSize: '12px', color: 'hsl(var(--text-muted))', margin: 0 }}>
                                    Enter the values in the correct order, separated by commas:
                                  </p>
                                  <input
                                    type="text"
                                    className="premium-input"
                                    placeholder="e.g., 1, 2, 3, 4"
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
                                    style={{ 
                                      padding: '14px 16px', 
                                      fontSize: '16px', 
                                      textAlign: 'center',
                                      borderRadius: '10px',
                                    }}
                                  />
                                </div>
                              )}

                              {/* Error detect format - two-step */}
                              {matatagQuestion.format === 'error_detect' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  {/* Step 1: Is the answer correct? */}
                                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                                    <button
                                      className={`option-btn ${matatagAnswer?.has_error === false ? 'correct' : ''}`}
                                      onClick={() => { if (!matatagResult) setMatatagAnswer({ has_error: false, correct_value: '' }); }}
                                      disabled={!!matatagResult}
                                      style={{ flex: 1, padding: '14px', fontSize: '16px', fontWeight: 600 }}
                                    >
                                      Yes, correct
                                    </button>
                                    <button
                                      className={`option-btn ${matatagAnswer?.has_error === true ? 'correct' : ''}`}
                                      onClick={() => { if (!matatagResult) setMatatagAnswer({ has_error: true, correct_value: '' }); }}
                                      disabled={!!matatagResult}
                                      style={{ flex: 1, padding: '14px', fontSize: '16px', fontWeight: 600 }}
                                    >
                                      No, incorrect
                                    </button>
                                  </div>
                                  {/* Step 2: If incorrect, what's the correct answer? */}
                                  {matatagAnswer?.has_error === true && (
                                    <input
                                      type="number"
                                      className="premium-input"
                                      placeholder="What is the correct answer?"
                                      value={matatagAnswer?.correct_value ?? ''}
                                      onChange={e => setMatatagAnswer({ ...matatagAnswer, correct_value: e.target.value })}
                                      disabled={!!matatagResult}
                                      style={{ 
                                        padding: '14px 16px', 
                                        fontSize: '18px', 
                                        textAlign: 'center',
                                        fontWeight: 600,
                                        borderRadius: '10px',
                                      }}
                                      autoFocus
                                    />
                                  )}
                                </div>
                              )}

                              {/* Number bond format (read mode - fill in missing part) */}
                              {(matatagQuestion.format === 'read_fill_in_blank' || matatagQuestion.format === 'number_bond') && matatagQuestion.format !== 'cloze' && (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                  <input
                                    type="number"
                                    className="premium-input"
                                    placeholder="Enter the missing number..."
                                    value={matatagAnswer ?? ''}
                                    onChange={e => setMatatagAnswer(e.target.value)}
                                    disabled={!!matatagResult}
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
                            </>
                          )}
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

      </main>

      {/* Telemetry Info Modal Overlay */}
      {showTelemetryModal && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(5, 8, 22, 0.85)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            animation: 'fade-in 0.3s ease-out'
          }}
          onClick={() => setShowTelemetryModal(false)}
        >
          <div 
            className="glass-card animate-scale-up" 
            style={{
              maxWidth: '550px',
              width: '90%',
              padding: '40px',
              position: 'relative',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)',
              border: '1px solid rgba(16, 185, 129, 0.25)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close Button */}
            <button 
              onClick={() => setShowTelemetryModal(false)}
              style={{
                position: 'absolute',
                top: '20px',
                right: '20px',
                background: 'none',
                border: 'none',
                color: 'hsl(var(--text-muted))',
                fontSize: '24px',
                cursor: 'pointer',
                transition: 'var(--transition-smooth)'
              }}
              onMouseEnter={(e) => e.target.style.color = '#f8fafc'}
              onMouseLeave={(e) => e.target.style.color = 'hsl(var(--text-muted))'}
            >
              &times;
            </button>

            {/* Modal Header */}
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <div style={{ width: '64px', height: '64px', borderRadius: '16px', background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 15px', boxShadow: '0 8px 24px rgba(16, 185, 129, 0.3)' }}>
                <Shield className="w-8 h-8 text-white" />
              </div>
              <h3 style={{ fontSize: '24px', fontWeight: 800, color: '#f8fafc' }}>Active Telemetry Shield</h3>
              <p style={{ color: 'hsl(var(--text-muted))', fontSize: '13px', marginTop: '6px' }}>
                CCMed integrates advanced real-time psychometric pacing controls to guarantee an authentic, distraction-free environment.
              </p>
            </div>

            {/* Rules list */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '30px' }}>
              
              {/* Rule 1: Tab Focus */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <User className="w-5 h-5 text-emerald-400" style={{ color: '#34d399' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>Anti-Distraction Focus Guard</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Pauses academic timers and increments a "tab-out" counter if a student switches tabs or minimizes the CCMed window.
                  </p>
                </div>
              </div>

              {/* Rule 2: Idle Pacing */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <RefreshCw className="w-5 h-5 text-amber-400" style={{ color: '#fbbf24' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>120-Second Idle Pacing Sensor</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Pauses progress and increments the student's background idle duration if no keyboard or mouse actions are recorded for 2 minutes.
                  </p>
                </div>
              </div>

              {/* Rule 3: Guessing Prevention */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(59, 130, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Zap className="w-5 h-5 text-blue-400" style={{ color: '#60a5fa' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>Rapid-Guess Defense Filter</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Flags submissions made under 3s (Math) or 1.5s (ELA) as potential guesses. Guessed answers won't increment streaks or advance mastery.
                  </p>
                </div>
              </div>

              {/* Rule 4: Spam Protection */}
              <div style={{ display: 'flex', gap: '15px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <AlertTriangle className="w-5 h-5 text-red-400" style={{ color: '#f87171' }} />
                </div>
                <div>
                  <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>Multi-Click Spam Lockout</h4>
                  <p style={{ fontSize: '13px', color: 'hsl(var(--text-muted))', marginTop: '2px' }}>
                    Temporarily blocks choices and displays a calming caution alert if the student performs 4 or more rapid clicks within 1.5 seconds.
                  </p>
                </div>
              </div>

            </div>

            {/* Close Button */}
            <button className="btn-primary" onClick={() => setShowTelemetryModal(false)} style={{ width: '100%', padding: '14px', background: '#10b981', borderColor: '#10b981' }}>
              <span>Acknowledge & Close</span>
            </button>
          </div>
        </div>
      )}

      {/* Question Flagging Modal Overlay */}
      {showFlagModal && (
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
                onClick={handleFlagQuestion}
                disabled={isFlagging}
                style={{ flex: 2, background: '#ef4444', borderColor: '#ef4444' }}
              >
                {isFlagging ? 'Flagging...' : '🚩 Submit Flag'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
