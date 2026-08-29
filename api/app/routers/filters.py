"""
Advanced filtering / query builder endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
import math
from app.database import get_db
from app.models import (
    Candidate, Skill, Score, SavedFilter, User, FilterScope
)
from app.schemas import (
    FilterQuery, SavedFilterCreate, SavedFilterResponse,
    CandidateListItem, PaginatedCandidates
)
from app.auth import get_current_user, require_permission

router = APIRouter(prefix="/api/filters", tags=["Filters"])


def _build_filter_condition(condition, db_model=Candidate):
    """Convert a filter condition to a SQLAlchemy criterion."""
    from app.models import SourceChannel, CareerLevel, EmploymentType
    field_map = {
        "full_name": Candidate.full_name,
        "email": Candidate.email,
        "phone": Candidate.phone,
        "city": Candidate.city,
        "department_tag": Candidate.department_tag,
        "career_level": Candidate.career_level,
        "employment_type": Candidate.employment_type,
        "source_channel": Candidate.source_channel,
        "applied_designation": Candidate.applied_designation,
        "tags": Candidate.tags,
    }

    column = field_map.get(condition.field)
    if column is None:
        return None

    op = condition.operator
    val = condition.value

    if op == "equals":
        return column == val
    elif op == "not_equals":
        return column != val
    elif op == "contains":
        return column.ilike(f"%{val}%")
    elif op == "starts_with":
        return column.ilike(f"{val}%")
    elif op == "gt":
        return column > val
    elif op == "lt":
        return column < val
    elif op == "between":
        return and_(column >= val, column <= condition.value2)
    elif op == "in_list":
        if isinstance(val, str):
            val = [v.strip() for v in val.split(",")]
        return column.in_(val)
    elif op == "is_empty":
        return column.is_(None)
    return None


def _build_filter_query(filter_config: dict):
    """Build SQLAlchemy where clause from filter config."""
    conditions = []

    groups = filter_config.get("groups", [])
    join_logic = filter_config.get("join_logic", "OR")

    group_clauses = []
    for group in groups:
        logic = group.get("logic", "AND")
        group_conditions = []
        for cond in group.get("conditions", []):
            criterion = _build_filter_condition(cond)
            if criterion is not None:
                group_conditions.append(criterion)

        if group_conditions:
            if logic == "AND":
                group_clauses.append(and_(*group_conditions))
            else:
                group_clauses.append(or_(*group_conditions))

    if not group_clauses:
        return None

    if join_logic == "AND":
        return and_(*group_clauses)
    else:
        return or_(*group_clauses)


@router.post("/apply", response_model=PaginatedCandidates)
async def apply_filter(
    body: FilterQuery,
    page: int = 1,
    page_size: int = 25,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:read")),
):
    """Apply a filter query to the candidate database."""
    where_clause = _build_filter_query(body.model_dump())

    query = select(Candidate).options(
        selectinload(Candidate.skills),
        selectinload(Candidate.scores),
        selectinload(Candidate.sync_status),
    )
    count_query = select(func.count(Candidate.candidate_id))

    if where_clause is not None:
        query = query.where(where_clause)
        count_query = count_query.where(where_clause)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    sort_column = getattr(Candidate, sort_by, Candidate.created_at)
    query = query.order_by(desc(sort_column) if sort_order == "desc" else sort_column.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    candidates = result.scalars().unique().all()

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


@router.post("", response_model=SavedFilterResponse, status_code=201)
async def save_filter(
    body: SavedFilterCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("filters:write")),
):
    saved = SavedFilter(
        name=body.name,
        user_id=user.user_id,
        scope=body.scope,
        filter_config=body.filter_config.model_dump(),
    )
    db.add(saved)
    await db.flush()
    await db.refresh(saved)
    return SavedFilterResponse.model_validate(saved)


@router.get("", response_model=list[SavedFilterResponse])
async def list_filters(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("filters:read")),
):
    """List filters visible to current user (personal + global, or all for super_admin)."""
    from app.models import UserRole
    if user.role == UserRole.super_admin:
        result = await db.execute(select(SavedFilter).order_by(SavedFilter.created_at.desc()))
    else:
        result = await db.execute(
            select(SavedFilter)
            .where(or_(SavedFilter.user_id == user.user_id, SavedFilter.scope == FilterScope.global_scope))
            .order_by(SavedFilter.created_at.desc())
        )
    return [SavedFilterResponse.model_validate(f) for f in result.scalars().all()]


@router.delete("/{filter_id}", status_code=204)
async def delete_filter(
    filter_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("filters:delete")),
):
    result = await db.execute(select(SavedFilter).where(SavedFilter.filter_id == filter_id))
    filt = result.scalar_one_or_none()
    if not filt:
        raise HTTPException(status_code=404, detail="Filter not found")
    if filt.user_id != user.user_id and user.role.value != "Super Admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this filter")
    await db.delete(filt)
    await db.flush()
