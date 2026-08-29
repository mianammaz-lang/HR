"""
Candidate CRUD, listing, pagination, and export endpoints.
"""
import math
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import selectinload
from openpyxl import Workbook
from app.database import get_db
from app.models import (
    Candidate, Skill, EmploymentHistory, Score, SyncStatusRecord,
    Document, UserRole, User, AuditLog
)
from app.schemas import (
    CandidateCreate, CandidateUpdate, CandidateResponse,
    CandidateListItem, PaginatedCandidates, PaginationParams
)
from app.auth import get_current_user, require_permission, has_permission

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


@router.get("", response_model=PaginatedCandidates)
async def list_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    search: str = Query(None),
    department: str = Query(None),
    career_level: str = Query(None),
    source: str = Query(None),
    city: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:read")),
):
    # Build base query with counts
    query = select(Candidate).options(
        selectinload(Candidate.skills),
        selectinload(Candidate.scores),
        selectinload(Candidate.sync_status),
    )

    count_query = select(func.count(Candidate.candidate_id))

    # Apply filters
    filters = []
    if search:
        search_filter = or_(
            Candidate.full_name.ilike(f"%{search}%"),
            Candidate.email.ilike(f"%{search}%"),
            Candidate.phone.ilike(f"%{search}%"),
            Candidate.applied_designation.ilike(f"%{search}%"),
        )
        filters.append(search_filter)
    if department:
        filters.append(Candidate.department_tag == department)
    if career_level:
        filters.append(Candidate.career_level == career_level)
    if source:
        filters.append(Candidate.source_channel == source)
    if city:
        filters.append(Candidate.city == city)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_column = getattr(Candidate, sort_by, Candidate.created_at)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    candidates = result.scalars().unique().all()

    # Build list items
    items = []
    for c in candidates:
        latest_score = None
        confidence = None
        sync = None
        if c.scores:
            latest = max(c.scores, key=lambda s: s.score_generated_at)
            latest_score = float(latest.ranking_score)
            confidence = latest.confidence_flag
        if c.sync_status:
            sync = c.sync_status.sync_status

        items.append(CandidateListItem(
            candidate_id=c.candidate_id,
            full_name=c.full_name,
            email=c.email,
            phone=c.phone,
            city=c.city,
            source_channel=c.source_channel,
            department_tag=c.department_tag,
            career_level=c.career_level,
            employment_type=c.employment_type,
            applied_designation=c.applied_designation,
            tags=c.tags,
            created_at=c.created_at,
            latest_score=latest_score,
            confidence_flag=confidence,
            sync_status=sync,
            skill_names=[s.skill_name for s in c.skills],
        ))

    return PaginatedCandidates(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/export")
async def export_candidates(
    format: str = Query("csv", regex="^(csv|excel)$"),
    search: str = Query(None),
    department: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:read")),
):
    """Export candidates as CSV or Excel."""
    query = select(Candidate).options(
        selectinload(Candidate.skills),
        selectinload(Candidate.scores),
        selectinload(Candidate.employment_history),
    )

    if search:
        query = query.where(or_(
            Candidate.full_name.ilike(f"%{search}%"),
            Candidate.email.ilike(f"%{search}%"),
        ))
    if department:
        query = query.where(Candidate.department_tag == department)

    result = await db.execute(query.order_by(desc(Candidate.created_at)))
    candidates = result.scalars().unique().all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Candidates"

    headers = [
        "ID", "Full Name", "Email", "Phone", "LinkedIn", "City",
        "Source", "Department", "Career Level", "Employment Type",
        "Designation", "Score", "Confidence", "Skills", "Tags",
        "Date Received", "Created At"
    ]
    ws.append(headers)

    for c in candidates:
        score = None
        confidence = None
        if c.scores:
            latest = max(c.scores, key=lambda s: s.score_generated_at)
            score = float(latest.ranking_score)
            confidence = latest.confidence_flag.value if latest.confidence_flag else None

        ws.append([
            str(c.candidate_id),
            c.full_name,
            c.email or "",
            c.phone or "",
            c.linkedin_url or "",
            c.city or "",
            c.source_channel.value if c.source_channel else "",
            c.department_tag or "",
            c.career_level.value if c.career_level else "",
            c.employment_type.value if c.employment_type else "",
            c.applied_designation or "",
            score,
            confidence or "",
            ", ".join(s.skill_name for s in c.skills),
            ", ".join(c.tags) if c.tags else "",
            c.date_received.isoformat() if c.date_received else "",
            c.created_at.isoformat(),
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    media_type = "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    filename = "candidates_export.xlsx"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:read")),
):
    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.skills),
            selectinload(Candidate.employment_history),
            selectinload(Candidate.scores),
            selectinload(Candidate.sync_status),
            selectinload(Candidate.documents),
        )
        .where(Candidate.candidate_id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return CandidateResponse.model_validate(candidate)


@router.post("", response_model=CandidateResponse, status_code=201)
async def create_candidate(
    body: CandidateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:write")),
):
    import hashlib

    candidate = Candidate(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        linkedin_url=body.linkedin_url,
        city=body.city,
        source_channel=body.source_channel,
        source_job_post_id=body.source_job_post_id,
        applied_designation=body.applied_designation,
        department_tag=body.department_tag,
        career_level=body.career_level,
        employment_type=body.employment_type,
        matched_open_requisition_id=body.matched_open_requisition_id,
        tags=body.tags,
        notes_internal=body.notes_internal,
    )

    # Calculate duplicate hash
    if body.email or body.phone:
        raw = (body.email or "").strip().lower() + (body.phone or "").strip()
        candidate.duplicate_check_hash = hashlib.sha256(raw.encode()).hexdigest()

    db.add(candidate)
    await db.flush()

    # Add skills
    for skill in body.skills:
        db.add(Skill(candidate_id=candidate.candidate_id, skill_name=skill.skill_name, jd_keyword_match=skill.jd_keyword_match))

    # Add employment history
    for hist in body.employment_history:
        db.add(EmploymentHistory(
            candidate_id=candidate.candidate_id,
            company=hist.company,
            title=hist.title,
            duration=hist.duration,
            description=hist.description,
        ))

    # Create sync status record
    db.add(SyncStatusRecord(candidate_id=candidate.candidate_id))

    await db.flush()
    await db.refresh(candidate)

    # Log audit
    db.add(AuditLog(
        user_id=user.user_id,
        action="candidate_created",
        entity_type="candidate",
        entity_id=str(candidate.candidate_id),
        details={"full_name": candidate.full_name},
    ))
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.skills),
            selectinload(Candidate.employment_history),
            selectinload(Candidate.scores),
            selectinload(Candidate.sync_status),
            selectinload(Candidate.documents),
        )
        .where(Candidate.candidate_id == candidate.candidate_id)
    )
    candidate = result.scalar_one()
    return CandidateResponse.model_validate(candidate)


@router.put("/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    candidate_id: str,
    body: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:write")),
):
    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.skills),
            selectinload(Candidate.employment_history),
            selectinload(Candidate.scores),
            selectinload(Candidate.sync_status),
            selectinload(Candidate.documents),
        )
        .where(Candidate.candidate_id == candidate_id)
    )
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(candidate, key, val)

    # Recalculate duplicate hash if email or phone changed
    if "email" in update_data or "phone" in update_data:
        import hashlib
        raw = (candidate.email or "").strip().lower() + (candidate.phone or "").strip()
        candidate.duplicate_check_hash = hashlib.sha256(raw.encode()).hexdigest()

    await db.flush()
    await db.refresh(candidate)

    db.add(AuditLog(
        user_id=user.user_id,
        action="candidate_updated",
        entity_type="candidate",
        entity_id=str(candidate.candidate_id),
        details=update_data,
    ))
    await db.flush()

    result = await db.execute(
        select(Candidate)
        .options(
            selectinload(Candidate.skills),
            selectinload(Candidate.employment_history),
            selectinload(Candidate.scores),
            selectinload(Candidate.sync_status),
            selectinload(Candidate.documents),
        )
        .where(Candidate.candidate_id == candidate.candidate_id)
    )
    candidate = result.scalar_one()
    return CandidateResponse.model_validate(candidate)


@router.delete("/{candidate_id}", status_code=204)
async def delete_candidate(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:delete")),
):
    result = await db.execute(select(Candidate).where(Candidate.candidate_id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    await db.delete(candidate)
    await db.flush()

    db.add(AuditLog(
        user_id=user.user_id,
        action="candidate_deleted",
        entity_type="candidate",
        entity_id=str(candidate_id),
    ))
    await db.flush()
