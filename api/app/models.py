"""
Database models for Talent Pool Management System
Uses String(36) for UUIDs to work with both SQLite and PostgreSQL.
"""
import uuid
import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Date, Numeric, Enum, ForeignKey,
    JSON, Integer, UniqueConstraint, Index, Float
)
from sqlalchemy.orm import relationship
from app.database import Base


def new_uuid():
    return str(uuid.uuid4())


# ─── Enums ────────────────────────────────────────────────────────────────────

class SourceChannel(str, enum.Enum):
    linkedin = "LinkedIn"
    indeed = "Indeed"
    referral = "Referral"
    agency = "Agency"
    website = "Website"
    direct = "Direct"
    other = "Other"


class CareerLevel(str, enum.Enum):
    entry = "Entry"
    mid = "Mid"
    senior = "Senior"
    lead = "Lead"
    managerial = "Managerial"


class EmploymentType(str, enum.Enum):
    full_time = "Full-time"
    contract = "Contract"
    remote = "Remote"
    onsite = "Onsite"


class SyncStatus(str, enum.Enum):
    not_synced = "Not Synced"
    synced = "Synced"
    sync_failed = "Sync Failed"


class ConfidenceFlag(str, enum.Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class RequisitionStatus(str, enum.Enum):
    open = "Open"
    approved = "Approved"
    closed = "Closed"


class UserRole(str, enum.Enum):
    super_admin = "Super Admin"
    hr_admin = "HR Admin"
    recruiter = "Recruiter"
    technical_team = "Technical Team"
    requester = "Requester"
    viewer = "Viewer"


class FilterScope(str, enum.Enum):
    personal = "personal"
    team = "team"
    global_scope = "global"


# ─── User & Auth ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(512), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    is_active = Column(Boolean, default=True)
    team = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    saved_filters = relationship("SavedFilter", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")


# ─── Candidate ────────────────────────────────────────────────────────────────

class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(String(36), primary_key=True, default=new_uuid)
    full_name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), index=True)
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    city = Column(String(100), index=True)
    source_channel = Column(Enum(SourceChannel))
    source_job_post_id = Column(String(100))
    date_received = Column(DateTime, default=datetime.utcnow)
    applied_designation = Column(String(255))
    department_tag = Column(String(100), index=True)
    career_level = Column(Enum(CareerLevel), index=True)
    employment_type = Column(Enum(EmploymentType))
    matched_open_requisition_id = Column(String(36), ForeignKey("requisitions.requisition_id"), nullable=True)
    data_retention_expiry = Column(Date)
    tags = Column(JSON, default=list)
    notes_internal = Column(Text)
    duplicate_check_hash = Column(String(64), index=True)
    is_duplicate_of = Column(String(36), ForeignKey("candidates.candidate_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    employment_history = relationship("EmploymentHistory", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="candidate", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="candidate", cascade="all, delete-orphan")
    sync_status = relationship("SyncStatusRecord", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="candidate", cascade="all, delete-orphan")
    matched_requisition = relationship("Requisition", foreign_keys=[matched_open_requisition_id])


# ─── Employment History ───────────────────────────────────────────────────────

class EmploymentHistory(Base):
    __tablename__ = "employment_history"

    employment_history_id = Column(String(36), primary_key=True, default=new_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255))
    title = Column(String(255))
    duration = Column(String(100))
    description = Column(Text)

    candidate = relationship("Candidate", back_populates="employment_history")


# ─── Skills ───────────────────────────────────────────────────────────────────

class Skill(Base):
    __tablename__ = "skills"

    skill_id = Column(String(36), primary_key=True, default=new_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    jd_keyword_match = Column(Boolean, default=False)

    candidate = relationship("Candidate", back_populates="skills")


# ─── Scoring ──────────────────────────────────────────────────────────────────

class Score(Base):
    __tablename__ = "scores"

    score_id = Column(String(36), primary_key=True, default=new_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False, index=True)
    requisition_id = Column(String(36), ForeignKey("requisitions.requisition_id"), nullable=True)
    ranking_score = Column(Numeric(5, 2), nullable=False)
    score_breakdown_json = Column(JSON, default=dict)
    score_model_version = Column(String(100))
    score_generated_at = Column(DateTime, default=datetime.utcnow)
    confidence_flag = Column(Enum(ConfidenceFlag), default=ConfidenceFlag.medium)

    candidate = relationship("Candidate", back_populates="scores")
    requisition = relationship("Requisition", back_populates="scores")


# ─── Sync Status ──────────────────────────────────────────────────────────────

class SyncStatusRecord(Base):
    __tablename__ = "sync_status"

    sync_id = Column(String(36), primary_key=True, default=new_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), unique=True, nullable=False)
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.not_synced, index=True)
    sync_threshold_met = Column(Boolean, default=False)
    erpnext_applicant_id = Column(String(100))
    synced_at = Column(DateTime, nullable=True)
    sync_error_log = Column(Text, nullable=True)

    candidate = relationship("Candidate", back_populates="sync_status")


# ─── Documents ────────────────────────────────────────────────────────────────

class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(String(36), primary_key=True, default=new_uuid)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False, index=True)
    resume_file_url = Column(String(1000))
    resume_version = Column(Integer, default=1)
    additional_docs_json = Column(JSON, default=list)
    original_filename = Column(String(255))
    file_size = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="documents")


# ─── Job Requisition ──────────────────────────────────────────────────────────

class Requisition(Base):
    __tablename__ = "requisitions"

    requisition_id = Column(String(36), primary_key=True, default=new_uuid)
    erpnext_requisition_id = Column(String(100), unique=True, nullable=True)
    designation = Column(String(255), nullable=False)
    department = Column(String(100), index=True)
    location = Column(String(100))
    status = Column(Enum(RequisitionStatus), default=RequisitionStatus.open, index=True)
    description = Column(Text)
    required_skills = Column(JSON, default=list)
    experience_years = Column(Float, nullable=True)
    employment_type = Column(Enum(EmploymentType), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scores = relationship("Score", back_populates="requisition")


# ─── Saved Filters ────────────────────────────────────────────────────────────

class SavedFilter(Base):
    __tablename__ = "saved_filters"

    filter_id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(255), nullable=False)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    scope = Column(Enum(FilterScope), default=FilterScope.personal)
    filter_config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="saved_filters")


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True, default=new_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(String(100))
    details = Column(JSON, default=dict)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


# ─── LLM Prompt Versions ─────────────────────────────────────────────────────

class LLMPromptVersion(Base):
    __tablename__ = "llm_prompt_versions"

    prompt_id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(255), nullable=False)
    prompt_type = Column(String(50), nullable=False)
    version = Column(Integer, default=1)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── System Settings ──────────────────────────────────────────────────────────

class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_id = Column(String(36), primary_key=True, default=new_uuid)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# --- Application Form ---

class ApplicationForm(Base):
    __tablename__ = "application_forms"

    form_id = Column(String(36), primary_key=True, default=new_uuid)
    requisition_id = Column(String(36), ForeignKey("requisitions.requisition_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    custom_fields = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requisition = relationship("Requisition")
    submissions = relationship("FormSubmission", back_populates="form", cascade="all, delete-orphan")


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    submission_id = Column(String(36), primary_key=True, default=new_uuid)
    form_id = Column(String(36), ForeignKey("application_forms.form_id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id"), nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    cover_letter = Column(Text)
    custom_answers = Column(JSON, default=dict)
    resume_filename = Column(String(255))
    submitted_at = Column(DateTime, default=datetime.utcnow)

    form = relationship("ApplicationForm", back_populates="submissions")
    candidate = relationship("Candidate")
