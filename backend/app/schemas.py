from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Parent Schemas ---
class ParentLoginRequest(BaseModel):
    password: str

class ParentLoginResponse(BaseModel):
    success: bool
    token: str

class ParentSettingsUpdateRequest(BaseModel):
    student_id: int
    name: str
    age: int
    grade: int
    language_preference: str
    interest_tags: str
    elo_rating: Optional[float] = None
    telemetry_enabled: Optional[bool] = True

class UpdateInterestsRequest(BaseModel):
    interest_tags: str  # Student-added interests (additive on top of parent-set tags)

# --- Student Schemas ---
class StudentRegisterRequest(BaseModel):
    name: str
    pin: str = Field(..., min_length=4, max_length=6, description="4-6 digit numeric PIN")
    age: int
    grade: int
    language_preference: str = "en"
    interest_tags: str = "basketball,bible"

class StudentLoginRequest(BaseModel):
    student_id: int
    pin: str

class StudentProfileResponse(BaseModel):
    id: int
    name: str
    age: int
    grade: int
    language_preference: str
    interest_tags: str
    student_interest_tags: str = ""
    elo_rating: float
    telemetry_enabled: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

# --- Telemetry Schemas ---
class TelemetrySessionStartRequest(BaseModel):
    student_id: int

class TelemetrySessionStartResponse(BaseModel):
    session_id: int
    success: bool

class TelemetrySessionUpdateRequest(BaseModel):
    session_id: int
    tab_switch_count: int
    idle_seconds: int
    spam_click_count: int
    guess_count: int
    ended: bool = False

class TelemetrySessionResponse(BaseModel):
    success: bool

# --- Practice Schemas ---
class QuestionOption(BaseModel):
    key: str # e.g. "A", "B", "C", "D"
    text: str # Text of option

class QuestionResponse(BaseModel):
    skill_id: str
    skeleton_id: str
    stem: str
    options: List[QuestionOption]
    is_worked_example: bool = False
    worked_example_steps: Optional[List[str]] = None
    is_placement: bool = False
    placement_progress: Optional[int] = None # Question index 1-15
    question_mode: str = "mcq"  # "mcq", "writing_prompt", "numeric_input", "cloze", "multi_select", "ordering", "plotter_bar", "read_bar", "number_line", "clock_set", etc.
    standard_description: Optional[str] = None
    domain: Optional[str] = None
    is_testy: bool = False  # True for experimental Problem Lab questions — no ELO/mastery updates
    # Visual skeleton fields (optional - only present for visual questions)
    visual_type: Optional[str] = None  # "NumberLine", "ClockSet", "BarChart", etc.
    visual_params: Optional[Dict[str, Any]] = None  # Type-specific rendering parameters
    is_visual: bool = False  # True if this is a visual skeleton question
    answer_collection: str = "mcq" # How the frontend should collect the answer

class VisualQuestionResponse(BaseModel):
    """Extended response for visual skeleton problems with interactive UI params"""
    skill_id: str                        # Competency text (truncated for display)
    skeleton_id: str                     # Stateless ID: e.g., "nl_4_12345_m"
    stem: str                            # Problem statement
    visual_type: str                     # "NumberLine", "ClockSet", "PesoMoney", etc.
    visual_params: Dict[str, Any]        # Type-specific rendering parameters
    question_mode: str                   # UI routing: "number_line", "clock_set", etc.
    all_traps: Dict[str, Any]            # Comprehensive trap catalog (3-4 selected by frontend)
    competency_text: Optional[str] = None  # Full MATATAG competency
    grade: Optional[int] = None          # Inferred grade
    difficulty: float = 0.5              # Scalar difficulty: 0.0-1.5+ (or legacy int 1-4)
    is_testy: bool = True                # Always True for visual skeletons

class PlacementSkipRequest(BaseModel):
    student_id: int
    subject: str

class AnswerSubmitRequest(BaseModel):
    student_id: int
    session_id: Optional[int] = None
    skill_id: str
    skeleton_id: str
    stem: str
    correct_answer: str
    selected_answer: str
    response_time_ms: int
    telemetry_flagged: bool = False

class AnswerSubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    selected_answer: str
    explanation: str # Thematic explanation of correct answer
    trap_selected: Optional[str] = None # Name of trap if triggered
    new_student_elo: float
    new_skill_elo: float
    mastery_status: str # "locked", "active", "mastered", "review"

class QuestionFlagRequest(BaseModel):
    student_id: int
    skill_id: str
    skeleton_id: str
    stem: str
    correct_answer: Optional[str] = None
    selected_answer: Optional[str] = None
    reason: str
    comment: Optional[str] = None

# --- Socratic Schemas ---
class SocraticChatMessage(BaseModel):
    role: str # "user" or "assistant"
    content: str

class SocraticChatRequest(BaseModel):
    student_id: int
    skill_id: str
    message: str
    history: List[SocraticChatMessage]
    # Live question context — always preferred over stale DB lookup
    question_text: Optional[str] = None   # exact stem the student sees
    student_answer: Optional[str] = None  # what the student typed/selected
    is_intro: Optional[bool] = False      # True when tutor is in intro-viewer mode

class SocraticChatResponse(BaseModel):
    reply: str
    resolved: bool = False # Set to true when tutor feels student understands

# --- Analytics Schemas ---
class SkillMasterySummary(BaseModel):
    skill_id: str
    title: str
    code: str
    grade_level: str
    status: str
    elo_rating: float
    consecutive_correct: int

class SessionSummary(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_minutes: float
    tab_switch_count: int
    idle_seconds: int
    spam_click_count: int
    guess_count: int

class ParentAnalyticsResponse(BaseModel):
    student_id: int
    name: str
    elo_rating: float
    age: int
    grade: int
    interest_tags: str
    telemetry_enabled: bool
    mastery_ratio: float # percent mastered e.g. 0.45
    skills: List[SkillMasterySummary]
    sessions: List[SessionSummary]
    total_attempts: int
    correct_attempts: int

# --- Writing Schemas ---
class WritingGradeRequest(BaseModel):
    student_id: int
    skill_id: str
    skeleton_id: str
    student_text: str
    session_id: int

class TraitScores(BaseModel):
    ideas: int
    organization: int
    voice: int
    word_choice: int
    sentence_fluency: int
    conventions: int
    composite: float
    verdict: str  # "exceeds", "meets", "developing", "beginning"
    trait_feedback: Dict[str, str]

class WritingGradeResponse(BaseModel):
    trait_scores: TraitScores
    new_student_elo: float
    can_resubmit: bool  # True if verdict is "developing" or "beginning"

class WritingChatRequest(BaseModel):
    student_id: int
    skill_id: str
    skeleton_id: str
    message: str
    history: List[SocraticChatMessage]

class WritingChatResponse(BaseModel):
    reply: str

class AdminGraphNode(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    grade_level: Optional[str] = ""
    subject: str
    metadata: Optional[Dict[str, Any]] = None
    node_type: Optional[str] = "Standard"
    parent_id: Optional[str] = None
    source: str = "Unknown"
    is_example: bool = False
    pedagogical_context: Optional[str] = None

class AdminGraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str # 'prerequisite' or 'hierarchy'

class AdminGraphResponse(BaseModel):
    nodes: List[AdminGraphNode]
    edges: List[AdminGraphEdge]

# --- Dynamic Knowledge Graph schemas ---
class GraphNode(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    subject: str
    status: str  # "mastered", "active", "locked"
    elo_rating: float

class GraphTrack(BaseModel):
    key: str
    title: str
    color: str
    subject: str
    nodes: List[GraphNode]

class StudentParentGraphResponse(BaseModel):
    student_id: int
    name: str
    grade_level: str
    tracks: List[GraphTrack]

