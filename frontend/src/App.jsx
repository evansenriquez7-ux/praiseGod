// Force frontend rebuild hash to bypass Firebase Hosting 400 identical version error
import TelemetryModal from './components/Modals/TelemetryModal';
import FlagModal from './components/Modals/FlagModal';
import LoginView from './views/LoginView';
import PracticeView from './views/PracticeView';
import ParentDashboard from './views/ParentDashboard';
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
import { API_BASE } from './api/apiClient.js';
import { renderMath } from './utils/mathUtils.js';
import { renderVisualInner } from './utils/renderUtils.jsx';

function App() {
  // Global App States
  const [currentView, setCurrentView] = useState('login'); // 'login', 'practice', 'parent'
  const [isLoadingProfiles, setIsLoadingProfiles] = useState(true);
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
  const [verbalTracks, setVerbalTracks] = useState([]);
  const [loadingVerbalTracks, setLoadingVerbalTracks] = useState(false);
  const [writingCoachActive, setWritingCoachActive] = useState(false);


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
    const [showFlagModal, setShowFlagModal] = useState(false);
    
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
  const socraticAbortControllerRef = useRef(null);

  // Auto-scroll chat container to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, sendingChat]);

  useEffect(() => {
    if (socraticAbortControllerRef.current) {
      socraticAbortControllerRef.current.abort();
      socraticAbortControllerRef.current = null;
    }
    setSocraticActive(false);
    setChatMessages([]);
    setSendingChat(false);
  }, [introSlideIndex, introMiniLessonIndex]);

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
          setAiBackend('gemini');
          setOpencodeModel(config.gemini_model || 'gemma-4-31b-it');
          // Pre-load model list
          fetch(`${API_BASE}/parent/gemini-models`)
            .then(r => r.json())
            .then(d => setOpencodeModels(d.models || []))
            .catch(() => {});
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
      setIsLoadingProfiles(false);
    };
    verifyServerAndLoad();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/students/profiles`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setStudents(data);
      } else {
        console.error("Profiles response not an array:", data);
        setStudents([]);
      }
    } catch (e) {
      console.error("Failed to fetch profiles", e);
    } finally {
      setIsLoadingProfiles(false);
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
    setSelectedSubdomain(nodeId);
    setIntroContent(null);
    setIntroMiniLessonIndex(0);
    setIntroSlideIndex(0);
    setIntroStepIndex(0);
    setSocraticActive(false); // Always start closed as requested
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
    if (socraticAbortControllerRef.current) {
      socraticAbortControllerRef.current.abort();
      socraticAbortControllerRef.current = null;
    }
    setChatMessages([]);
    setSendingChat(false);
    setSocraticActive(false);
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
      
      // Auto-trigger removed: Socratic Tutor now only opens when Ask Tutor is clicked
      
      // No auto triggers
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

    if (socraticAbortControllerRef.current) {
      socraticAbortControllerRef.current.abort();
    }
    socraticAbortControllerRef.current = new AbortController();

    try {
      const res = await fetch(`${API_BASE}/socratic/chat`, {
        method: 'POST',
        signal: socraticAbortControllerRef.current.signal,
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
      if (e.name !== 'AbortError') {
        console.error("Socratic chatbot exchange failed", e);
      }
    } finally {
      // Only clear loading state if this wasn't aborted
      if (!socraticAbortControllerRef.current?.signal.aborted) {
        setSendingChat(false);
      }
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
              allowedCtxs[v.name] = [...v.options];
            });
          }
          if (allowedFmts.length === 0) {
            const allFmtNames = (data.formatters || []).map(f => f.name);
            allowedFmts.push(...allFmtNames);
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
  
                                {/* Next or Start Practice */}
                                {(() => {
                                  const isLastSlide = introMiniLessonIndex === totalMiniLessons - 1 && introSlideIndex === totalSlides - 1 && (!isWorkedExample || introStepIndex >= totalSteps - 1);
                                  if (isLastSlide) {
                                    return (
                                      <button
                                        onClick={() => {
                                          const nodeId = selectedSubdomain || introContent?.node_key;
                                          if (nodeId) {
                                            setSelectedSubject('Matatag');
                                            setSelectedSubdomain(nodeId);
                                            setPracticeViewType('workspace');
                                            setQuestionQueue([]);
                                            fetchNextQuestion(selectedStudent.id, 'Matatag', nodeId, true);
                                          }
                                        }}
                                        style={{
                                          padding: '8px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                                          cursor: 'pointer', border: 'none',
                                          background: '#10b981', color: '#fff',
                                        }}
                                      >
                                        ✏️ Move to Practice Problems
                                      </button>
                                    );
                                  }
                                  return (
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
                                      style={{
                                        padding: '8px 16px', borderRadius: '8px', fontSize: '13px', fontWeight: 600,
                                        cursor: 'pointer', border: 'none',
                                        background: '#06b6d4', color: '#fff',
                                      }}
                                    >
                                      {isWorkedExample && introStepIndex < totalSteps - 1 ? 'Next Step' : 'Next'}
                                    </button>
                                  );
                                })()}
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

  const handleOpencodeModelChange = async (newModel) => {
    setOpencodeModel(newModel);
    try {
      await fetch(`${API_BASE}/parent/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ai_backend: 'gemini', gemini_model: newModel }),
      });
      setAiBackend('gemini');
    } catch (e) {
      console.error("Failed to save Gemini model setting", e);
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
          <LoginView
            isLoadingProfiles={isLoadingProfiles}
            students={students}
            handleSelectStudent={handleSelectStudent}
            selectedStudent={selectedStudent}
            pinInput={pinInput} setPinInput={setPinInput}
            pinError={pinError}
            handleStudentLogin={handleStudentLogin}
            handleRegister={handleRegister}
            regName={regName} setRegName={setRegName}
            regPin={regPin} setRegPin={setRegPin}
            regAge={regAge} setRegAge={setRegAge}
            regGrade={regGrade} setRegGrade={setRegGrade}
            regInterests={regInterests} setRegInterests={setRegInterests}
          />
        )}

        {/* --- VIEW 2: PRACTICE WORKSPACE SCREEN --- */}
        {currentView === 'practice' && selectedStudent && (
          <PracticeView
            practiceViewType={practiceViewType} setPracticeViewType={setPracticeViewType} setCurrentView={setCurrentView}
            activeQuestion={activeQuestion} practiceVisualAnswer={practiceVisualAnswer} setPracticeVisualAnswer={setPracticeVisualAnswer}
            selectedOptionKey={selectedOptionKey} setSelectedOptionKey={setSelectedOptionKey} handleAnswerSubmit={handleAnswerSubmit}
            socraticActive={socraticActive}
            chatMessages={chatMessages} setChatMessages={setChatMessages} sendingChat={sendingChat} setSendingChat={setSendingChat}
            selectedStudent={selectedStudent} socraticAbortControllerRef={socraticAbortControllerRef} API_BASE={API_BASE}
            setSelectedStudent={setSelectedStudent} setSocraticActive={setSocraticActive} setShowFlagModal={setShowFlagModal} renderIntroViewer={renderIntroViewer}
            studentInterestInput={studentInterestInput} setStudentInterestInput={setStudentInterestInput} interestSaveStatus={interestSaveStatus} setInterestSaveStatus={setInterestSaveStatus} handleSaveInterests={handleSaveInterests} setSelectedSubject={setSelectedSubject} fetchMatatagTracks={fetchMatatagTracks} fetchMatatagNodes={fetchMatatagNodes} matatagNodes={matatagNodes} loadingMathTracks={loadingMathTracks} mathTracks={mathTracks} setSelectedSubdomain={setSelectedSubdomain} setQuestionQueue={setQuestionQueue} fetchNextQuestion={fetchNextQuestion} selectedSubject={selectedSubject} loadingVerbalTracks={loadingVerbalTracks} verbalTracks={verbalTracks} loadingMatatagTracks={loadingMatatagTracks} selectedRoadmapNode={selectedRoadmapNode} setSelectedRoadmapNode={setSelectedRoadmapNode} fetchIntroForStudent={fetchIntroForStudent} writingCoachActive={writingCoachActive} introContent={introContent} handleLogout={handleLogout} loadingQuestion={loadingQuestion} aiBackend={aiBackend} opencodeModel={opencodeModel} handleSkipPlacement={handleSkipPlacement} tabSwitchCount={tabSwitchCount} idleSeconds={idleSeconds} guessCount={guessCount} answerResult={answerResult} handleOptionClick={handleOptionClick} chatEndRef={chatEndRef} handleSendMessage={handleSendMessage} chatInput={chatInput} setChatInput={setChatInput} selectedSubdomain={selectedSubdomain}
          />
        )}
        {/* --- VIEW 3: PARENT CONTROL PANEL SCREEN --- */}
        {currentView === 'parent' && (
          <ParentDashboard
            {...{parentLoggedIn, handleParentLogin, parentPassword, setParentPassword, parentError,
            parentActiveTab, setParentActiveTab, students,
            editName, setEditName, editElo, setEditElo, editAge, setEditAge, editGrade, setEditGrade, editInterests, setEditInterests,
            socraticActive, setSocraticActive, chatMessages, setChatMessages, sendingChat, setSendingChat,
            selectedStudent, setCurrentView, socraticAbortControllerRef,
            renderIntroViewer, introNodes, introInterests, introSelectedNode, setIntroSelectedNode, introSelectedInterest, setIntroSelectedInterest, generateIntroContent, introLoading,
            setSelectedStudent, setTelemetrySessionId, setParentLoggedIn, setParentError,
            matatagNodeId, matatagNodes,
            fetchMatatagNodes, fetchIntroNodes, fetchIntroInterests,
            modelsLoading, modelFilter, setModelFilter, setAnalyticsData, _resetMatatagState, labAllowedDifficulties, labVariantValues, labSelectedFormatter, setLabSelectedInterest, fetchParentGraph, opencodeModel, parentAuthRequired, matatagNodeSearch, setLabAllowedContexts, fetchParentAnalytics, labDifficultyScalars, setEditTelemetryEnabled, fetchProfiles, fetchMatatagQuestion, opencodeModels, fetchMatatagAxes, labAllowedFormatters, saveLabConfig, labInterests, handleUpdateSettings, setLabAllowedFormatters, matatagAxisValues, activeQuestion, parentSelectedGrade, setMatatagNodeId, setParentSubjectFilter, setParentSelectedGrade, setLabAllowedDifficulties, matatagQuestion, handleToggleParentAuth, matatagResult, parentSubjectFilter, labSelectedInterest, setMatatagNodeSearch, analyticsData, matatagLoading, labConfig, labConfigLoading, setMatatagAnswer, matatagAnswer, editTelemetryEnabled, labAllowedContexts, submitMatatagAnswer, handleOpencodeModelChange, parentGraphData, fetchLabConfig}}
          />
        )}
      </main>


      <TelemetryModal 
        showTelemetryModal={showTelemetryModal} 
        setShowTelemetryModal={setShowTelemetryModal} 
      />
      <FlagModal 
        showFlagModal={showFlagModal}
        setShowFlagModal={setShowFlagModal}
        selectedStudent={selectedStudent}
        activeQuestion={activeQuestion}
        selectedOptionKey={selectedOptionKey}
        practiceVisualAnswer={practiceVisualAnswer}
      />
    </div>
  );
}

export default App;
