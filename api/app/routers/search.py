"""
Semantic search endpoints using AI-powered candidate search.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.database import get_db
from app.models import Candidate, User
from app.schemas import CandidateListItem
from app.auth import require_permission
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/semantic", response_model=list[CandidateListItem])
async def semantic_search(
    q: str = Query(..., description="Natural language search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("candidates:read")),
):
    """AI-powered semantic search over candidates."""
    ai = AIService()
    candidates = await ai.semantic_search(q, db, limit=limit)

    items = []
    for c in candidates:
        # Load relationships
        result = await db.execute(
            select(Candidate)
            .options(
                selectinload(Candidate.skills),
                selectinload(Candidate.scores),
                selectinload(Candidate.sync_status),
            )
            .where(Candidate.candidate_id == c.candidate_id)
        )
        c_full = result.scalar_one()

        latest_score = None
        confidence = None
        sync = None
        if c_full.scores:
            latest = max(c_full.scores, key=lambda s: s.score_generated_at)
            latest_score = float(latest.ranking_score)
            confidence = latest.confidence_flag
        if c_full.sync_status:
            sync = c_full.sync_status.sync_status

        items.append(CandidateListItem(
            candidate_id=c_full.candidate_id,
            full_name=c_full.full_name,
            email=c_full.email,
            phone=c_full.phone,
            city=c_full.city,
            source_channel=c_full.source_channel,
            department_tag=c_full.department_tag,
            career_level=c_full.career_level,
            employment_type=c_full.employment_type,
            applied_designation=c_full.applied_designation,
            tags=c_full.tags,
            created_at=c_full.created_at,
            latest_score=latest_score,
            confidence_flag=confidence,
            sync_status=sync,
            skill_names=[s.skill_name for s in c_full.skills],
        ))

    return items
