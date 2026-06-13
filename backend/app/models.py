import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.database import Base

class ParentAccount(Base):
    __tablename__ = "parent_accounts"

    id = Column(Integer, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)
    password_auth_required = Column(Boolean, default=False)
    ai_backend = Column(String, default="gemini")          # "gemini" | "opencode"
    opencode_model = Column(String, default="opencode/deepseek-v4-flash-free")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    pin_hash = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    grade = Column(Integer, nullable=False)
    language_preference = Column(String, default="en") # "en" or "tl"
    interest_tags = Column(String, default="basketball,bible") # Comma-separated interests — set by parent
    student_interest_tags = Column(String, default="")         # Additional interests added by the student
    elo_rating = Column(Float, default=1200.0) # Active student ELO (legacy/fallback)
    elo_math = Column(Float, default=1200.0)
    elo_reading = Column(Float, default=1200.0)
    elo_writing = Column(Float, default=1200.0)
    elo_language = Column(Float, default=1200.0)
    elo_matatag = Column(Float, default=1200.0)  # MATATAG (Philippine curriculum)
    
    # Placement Completion Flags
    placement_done_math = Column(Boolean, default=False)
    placement_done_reading = Column(Boolean, default=False)
    placement_done_writing = Column(Boolean, default=False)
    placement_done_language = Column(Boolean, default=False)
    placement_done_matatag = Column(Boolean, default=False)  # MATATAG placement
    
    telemetry_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    mastery_states = relationship("MasteryState", back_populates="student", cascade="all, delete-orphan")
    telemetry_sessions = relationship("TelemetrySession", back_populates="student", cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="student", cascade="all, delete-orphan")
    spaced_repetition_cards = relationship("SpacedRepetition", back_populates="student", cascade="all, delete-orphan")

class SkillNode(Base):
    __tablename__ = "skill_nodes"

    id = Column(String, primary_key=True, index=True) # Common Core format like "4.NF.B.4.b" or "math_1a_rjb_cpt1"
    statement_code = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    grade_level = Column(String, nullable=True)
    subject = Column(String, default="Math")

    # Mapped exercises or raw references
    metadata_json = Column(JSON, nullable=True) 

class SkillEdge(Base):
    __tablename__ = "skill_edges"
    __table_args__ = (
        UniqueConstraint('source_id', 'target_id', 'relation_type', name='uq_edge_triple'),
    )

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String, ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String, ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String, default="prerequisites_for") # "prerequisites_for", "part_of"

class MasteryState(Base):
    __tablename__ = "mastery_states"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String, ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="locked") # "locked", "active", "mastered", "review"
    consecutive_correct = Column(Integer, default=0)
    consecutive_incorrect = Column(Integer, default=0)
    elo_rating = Column(Float, default=1200.0) # Concept/Skill ELO for difficulty matching
    next_review_at = Column(DateTime, nullable=True)

    student = relationship("StudentProfile", back_populates="mastery_states")
    skill = relationship("SkillNode")

class TelemetrySession(Base):
    __tablename__ = "telemetry_sessions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    tab_switch_count = Column(Integer, default=0)
    idle_seconds = Column(Integer, default=0)
    spam_click_count = Column(Integer, default=0)
    guess_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    student = relationship("StudentProfile", back_populates="telemetry_sessions")

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String, ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False)
    skeleton_id = Column(String, nullable=False)
    stem = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=False)
    selected_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    trap_selected = Column(String, nullable=True) # Tracks which trap model was activated
    telemetry_flagged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("StudentProfile", back_populates="attempts")
    skill = relationship("SkillNode")

class SpacedRepetition(Base):
    __tablename__ = "spaced_repetition"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String, ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False)
    repetitions = Column(Integer, default=0)
    interval_days = Column(Float, default=1.0)
    ease_factor = Column(Float, default=2.5)
    due_date = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("StudentProfile", back_populates="spaced_repetition_cards")
    skill = relationship("SkillNode")

class NodeIntroView(Base):
    __tablename__ = "node_intro_views"
    __table_args__ = (
        UniqueConstraint('student_id', 'node_key', name='uq_student_node_intro'),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    node_key = Column(String(20), nullable=False, index=True)  # e.g. "g1_na_q1"
    viewed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    student = relationship("StudentProfile")


class QuestionFlag(Base):
    __tablename__ = "question_flags"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(String, ForeignKey("skill_nodes.id", ondelete="CASCADE"), nullable=False)
    skeleton_id = Column(String, nullable=False)
    stem = Column(Text, nullable=False)
    correct_answer = Column(String, nullable=True)
    selected_answer = Column(String, nullable=True)
    reason = Column(String, nullable=False) # "incorrect", "double_answer", "typo", "other"
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("StudentProfile")
    skill = relationship("SkillNode")


class CompetencyConfiguration(Base):
    __tablename__ = "competency_configurations"

    node_id = Column(String(50), primary_key=True, index=True)
    allowed_difficulties = Column(JSON, nullable=True)
    allowed_contexts = Column(JSON, nullable=True)
    allowed_formatters = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
