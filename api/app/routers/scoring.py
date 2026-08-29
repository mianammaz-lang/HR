"""
Scoring endpoints: trigger AI scoring for candidates against requisitions.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Candidate, Requisition, Score, User
from app.schemas import ScoreRequest, BulkScoreRequest, ScoreResponse
from app.auth import require_permission
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/scoring", tags=["Scoring"])


@router.post("/score", response_model=ScoreResponse)
async def score_candidate(
    body: ScoreRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("scoring:run")),
):
    # Get candidate
    result = await db.execute(select(Candidate).where(Candidate.candidate_id == body.candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Get requisition
    result = await db.execute(select(Requisition).where(Requisition.requisition_id == body.requisition_id))
    requisition = result.scalar_one_or_none()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")

    # Call AI scoring service
    ai = AIService()
    score_result = await ai.score_candidate(candidate, requisition, db)

    return ScoreResponse.model_validate(score_result)


@router.post("/bulk", response_model=list[ScoreResponse])
async def bulk_score(
    body: BulkScoreRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("scoring:run")),
):
    result = await db.execute(select(Requisition).where(Requisition.requisition_id == body.requisition_id))
    requisition = result.scalar_one_or_none()
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")

    ai = AIService()
    scores = []
    for cid in body.candidate_ids:
        result = await db.execute(select(Candidate).where(Candidate.candidate_id == cid))
        candidate = result.scalar_one_or_none()
        if candidate:
            score_result = await ai.score_candidate(candidate, requisition, db)
            scores.append(ScoreResponse.model_validate(score_result))

    return scores


@router.get("/history/{candidate_id}", response_model=list[ScoreResponse])
async def score_history(
    candidate_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("scoring:read")),
):
    result = await db.execute(
        select(Score)
        .where(Score.candidate_id == candidate_id)
        .order_by(Score.score_generated_at.desc())
    )
    scores = result.scalars().all()
    return [ScoreResponse.model_validate(s) for s in scores]
