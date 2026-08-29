"""
Pydantic schemas for request validation and response serialization.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Dict
from datetime import datetime, date
from uuid import UUID
from app.models import (
    SourceChannel, CareerLevel, EmploymentType, SyncStatus,
    ConfidenceFlag, RequisitionStatus, UserRole, FilterScope
)


# ─── Auth ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role: UserRole = UserRole.viewer
    team: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    team: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str
    role: UserRole
    team: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Candidate ────────────────────────────────────────────────────────────────

class EmploymentHistoryItem(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class SkillItem(BaseModel):
    skill_name: str
    jd_keyword_match: bool = False


class CandidateCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    city: Optional[str] = None
    source_channel: Optional[SourceChannel] = None
    source_job_post_id: Optional[str] = None
    applied_designation: Optional[str] = None
    department_tag: Optional[str] = None
    career_level: Optional[CareerLevel] = None
    employment_type: Optional[EmploymentType] = None
    matched_open_requisition_id: Optional[UUID] = None
    tags: List[str] = []
    notes_internal: Optional[str] = None
    employment_history: List[EmploymentHistoryItem] = []
    skills: List[SkillItem] = []


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    city: Optional[str] = None
    source_channel: Optional[SourceChannel] = None
    applied_designation: Optional[str] = None
    department_tag: Optional[str] = None
    career_level: Optional[CareerLevel] = None
    employment_type: Optional[EmploymentType] = None
    matched_open_requisition_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    notes_internal: Optional[str] = None


class SkillResponse(BaseModel):
    skill_id: UUID
    skill_name: str
    jd_keyword_match: bool

    class Config:
        from_attributes = True


class EmploymentHistoryResponse(BaseModel):
    employment_history_id: UUID
    company: Optional[str]
    title: Optional[str]
    duration: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class ScoreResponse(BaseModel):
    score_id: UUID
    ranking_score: float
    score_breakdown_json: Dict[str, Any]
    score_model_version: Optional[str]
    score_generated_at: datetime
    confidence_flag: Optional[ConfidenceFlag]
    requisition_id: Optional[UUID]

    class Config:
        from_attributes = True


class SyncStatusResponse(BaseModel):
    sync_id: UUID
    sync_status: SyncStatus
    sync_threshold_met: bool
    erpnext_applicant_id: Optional[str]
    synced_at: Optional[datetime]
    sync_error_log: Optional[str]

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    doc_id: UUID
    resume_file_url: Optional[str]
    resume_version: int
    original_filename: Optional[str]
    file_size: Optional[int]
    uploaded_at: datetime

    class Config:
        from_attributes = True


class CandidateResponse(BaseModel):
    candidate_id: UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    city: Optional[str]
    source_channel: Optional[SourceChannel]
    date_received: Optional[datetime]
    applied_designation: Optional[str]
    department_tag: Optional[str]
    career_level: Optional[CareerLevel]
    employment_type: Optional[EmploymentType]
    matched_open_requisition_id: Optional[UUID]
    tags: Optional[List[str]]
    notes_internal: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Related data
    skills: List[SkillResponse] = []
    employment_history: List[EmploymentHistoryResponse] = []
    scores: List[ScoreResponse] = []
    sync_status: Optional[SyncStatusResponse] = None
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True


class CandidateListItem(BaseModel):
    """Lightweight candidate for table listings."""
    candidate_id: UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    city: Optional[str]
    source_channel: Optional[SourceChannel]
    department_tag: Optional[str]
    career_level: Optional[CareerLevel]
    employment_type: Optional[EmploymentType]
    applied_designation: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    # Aggregated fields
    latest_score: Optional[float] = None
    confidence_flag: Optional[ConfidenceFlag] = None
    sync_status: Optional[SyncStatus] = None
    skill_names: List[str] = []

    class Config:
        from_attributes = True


class PaginatedCandidates(BaseModel):
    items: List[CandidateListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Requisition ──────────────────────────────────────────────────────────────

class RequisitionCreate(BaseModel):
    designation: str
    department: Optional[str] = None
    location: Optional[str] = None
    status: RequisitionStatus = RequisitionStatus.open
    description: Optional[str] = None
    required_skills: List[str] = []
    experience_years: Optional[float] = None
    employment_type: Optional[EmploymentType] = None


class RequisitionUpdate(BaseModel):
    designation: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    status: Optional[RequisitionStatus] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    experience_years: Optional[float] = None


class RequisitionResponse(BaseModel):
    requisition_id: UUID
    erpnext_requisition_id: Optional[str]
    designation: str
    department: Optional[str]
    location: Optional[str]
    status: RequisitionStatus
    description: Optional[str]
    required_skills: Optional[List[str]]
    experience_years: Optional[float]
    employment_type: Optional[EmploymentType]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Scoring ──────────────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    candidate_id: UUID
    requisition_id: UUID


class BulkScoreRequest(BaseModel):
    candidate_ids: List[UUID]
    requisition_id: UUID


# ─── Filtering ────────────────────────────────────────────────────────────────

class FilterCondition(BaseModel):
    field: str
    operator: str  # equals, not_equals, contains, starts_with, gt, lt, between, in_list, is_empty
    value: Any
    value2: Optional[Any] = None  # for 'between'


class FilterGroup(BaseModel):
    logic: str = "AND"  # AND / OR
    conditions: List[FilterCondition]


class FilterQuery(BaseModel):
    groups: List[FilterGroup]
    join_logic: str = "OR"  # How groups are joined


class SavedFilterCreate(BaseModel):
    name: str
    scope: FilterScope = FilterScope.personal
    filter_config: FilterQuery


class SavedFilterResponse(BaseModel):
    filter_id: UUID
    name: str
    scope: FilterScope
    filter_config: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── ERPNext Settings ─────────────────────────────────────────────────────────

class ERPNextSettings(BaseModel):
    url: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    default_company: Optional[str] = None
    default_job_applicant_doctype: Optional[str] = None
    sync_threshold: float = 60.0


class ERPNextTestResult(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# ─── LLM Settings ─────────────────────────────────────────────────────────────

class LLMSettingsUpdate(BaseModel):
    api_key: Optional[str] = None
    auto_discovery: Optional[bool] = None
    primary_model: Optional[str] = None
    fallback_model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None


class LLMModel(BaseModel):
    id: str
    name: str
    provider: str
    context_length: int
    is_free: bool
    pricing: Optional[Dict[str, str]] = None


class LLMSettingsResponse(BaseModel):
    api_key_set: bool
    auto_discovery: bool
    primary_model: Optional[str]
    fallback_model: Optional[str]
    max_tokens: int
    temperature: float
    system_prompt: Optional[str]
    available_models: List[LLMModel] = []


# ─── Analytics ────────────────────────────────────────────────────────────────

class AnalyticsResponse(BaseModel):
    total_candidates: int
    candidates_by_source: Dict[str, int]
    candidates_by_department: Dict[str, int]
    candidates_by_location: Dict[str, int]
    candidates_by_career_level: Dict[str, int]
    average_score: Optional[float]
    score_distribution: Dict[str, int]
    sync_stats: Dict[str, int]
    confidence_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


# ─── Pagination ───────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 25
    sort_by: Optional[str] = None
    sort_order: str = "desc"  # asc or desc


class SortParams(BaseModel):
    field: str
    order: str = "desc"


# ─── Dashboard ────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_candidates: int
    total_requisitions: int
    synced_candidates: int
    pending_sync: int
    average_score: Optional[float]
    high_confidence_count: int


# Rebuild forward refs
TokenResponse.model_rebuild()
