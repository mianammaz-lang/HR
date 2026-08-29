"""
Analytics dashboard endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import (
    Candidate, Score, SyncStatusRecord, Requisition,
    User, AuditLog, SyncStatus, ConfidenceFlag, SourceChannel,
    CareerLevel
)
from app.schemas import AnalyticsResponse, DashboardStats
from app.auth import require_permission

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("analytics:read")),
):
    total_candidates = (await db.execute(select(func.count(Candidate.candidate_id)))).scalar() or 0
    total_reqs = (await db.execute(select(func.count(Requisition.requisition_id)))).scalar() or 0

    synced = (await db.execute(
        select(func.count(SyncStatusRecord.sync_id)).where(SyncStatusRecord.sync_status == SyncStatus.synced)
    )).scalar() or 0

    pending = (await db.execute(
        select(func.count(SyncStatusRecord.sync_id)).where(SyncStatusRecord.sync_status == SyncStatus.not_synced)
    )).scalar() or 0

    avg_score_result = await db.execute(select(func.avg(Score.ranking_score)))
    avg_score = avg_score_result.scalar()

    high_conf = (await db.execute(
        select(func.count(Score.score_id)).where(Score.confidence_flag == ConfidenceFlag.high)
    )).scalar() or 0

    return DashboardStats(
        total_candidates=total_candidates,
        total_requisitions=total_reqs,
        synced_candidates=synced,
        pending_sync=pending,
        average_score=round(float(avg_score), 1) if avg_score else None,
        high_confidence_count=high_conf,
    )


@router.get("", response_model=AnalyticsResponse)
async def full_analytics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("analytics:read")),
):
    total = (await db.execute(select(func.count(Candidate.candidate_id)))).scalar() or 0

    # By source
    source_result = await db.execute(
        select(Candidate.source_channel, func.count()).where(Candidate.source_channel.isnot(None)).group_by(Candidate.source_channel)
    )
    by_source = {row[0].value if row[0] else "Unknown": row[1] for row in source_result.all()}

    # By department
    dept_result = await db.execute(
        select(Candidate.department_tag, func.count()).where(Candidate.department_tag.isnot(None)).group_by(Candidate.department_tag)
    )
    by_dept = {row[0]: row[1] for row in dept_result.all()}

    # By location
    loc_result = await db.execute(
        select(Candidate.city, func.count()).where(Candidate.city.isnot(None)).group_by(Candidate.city)
    )
    by_loc = {row[0]: row[1] for row in loc_result.all()}

    # By career level
    level_result = await db.execute(
        select(Candidate.career_level, func.count()).where(Candidate.career_level.isnot(None)).group_by(Candidate.career_level)
    )
    by_level = {row[0].value if row[0] else "Unknown": row[1] for row in level_result.all()}

    # Average score
    avg_result = await db.execute(select(func.avg(Score.ranking_score)))
    avg_score = avg_result.scalar()

    # Score distribution
    score_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    score_dist_result = await db.execute(select(Score.ranking_score))
    for (score_val,) in score_dist_result.all():
        s = float(score_val)
        if s <= 20: score_ranges["0-20"] += 1
        elif s <= 40: score_ranges["21-40"] += 1
        elif s <= 60: score_ranges["41-60"] += 1
        elif s <= 80: score_ranges["61-80"] += 1
        else: score_ranges["81-100"] += 1

    # Sync stats
    sync_result = await db.execute(
        select(SyncStatusRecord.sync_status, func.count()).group_by(SyncStatusRecord.sync_status)
    )
    sync_stats = {row[0].value: row[1] for row in sync_result.all()}

    # Confidence distribution
    conf_result = await db.execute(
        select(Score.confidence_flag, func.count()).where(Score.confidence_flag.isnot(None)).group_by(Score.confidence_flag)
    )
    conf_dist = {row[0].value: row[1] for row in conf_result.all()}

    # Recent activity
    recent = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
    )
    recent_activity = [
        {
            "action": l.action,
            "entity_type": l.entity_type,
            "created_at": l.created_at.isoformat(),
            "details": l.details,
        }
        for l in recent.scalars().all()
    ]

    return AnalyticsResponse(
        total_candidates=total,
        candidates_by_source=by_source,
        candidates_by_department=by_dept,
        candidates_by_location=by_loc,
        candidates_by_career_level=by_level,
        average_score=round(float(avg_score), 1) if avg_score else None,
        score_distribution=score_ranges,
        sync_stats=sync_stats,
        confidence_distribution=conf_dist,
        recent_activity=recent_activity,
    )
