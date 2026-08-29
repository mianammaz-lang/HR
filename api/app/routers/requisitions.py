"""
Job Requisition CRUD endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models import Requisition, User
from app.schemas import RequisitionCreate, RequisitionUpdate, RequisitionResponse
from app.auth import require_permission

router = APIRouter(prefix="/api/requisitions", tags=["Requisitions"])


@router.get("", response_model=list[RequisitionResponse])
async def list_requisitions(
    status: str = Query(None),
    department: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("requisitions:read")),
):
    query = select(Requisition)
    if status:
        query = query.where(Requisition.status == status)
    if department:
        query = query.where(Requisition.department == department)
    result = await db.execute(query.order_by(desc(Requisition.created_at)))
    return [RequisitionResponse.model_validate(r) for r in result.scalars().all()]


@router.get("/{req_id}", response_model=RequisitionResponse)
async def get_requisition(
    req_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("requisitions:read")),
):
    result = await db.execute(select(Requisition).where(Requisition.requisition_id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return RequisitionResponse.model_validate(req)


@router.post("", response_model=RequisitionResponse, status_code=201)
async def create_requisition(
    body: RequisitionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("requisitions:write")),
):
    req = Requisition(
        designation=body.designation,
        department=body.department,
        location=body.location,
        status=body.status,
        description=body.description,
        required_skills=body.required_skills,
        experience_years=body.experience_years,
        employment_type=body.employment_type,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return RequisitionResponse.model_validate(req)


@router.put("/{req_id}", response_model=RequisitionResponse)
async def update_requisition(
    req_id: str,
    body: RequisitionUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("requisitions:write")),
):
    result = await db.execute(select(Requisition).where(Requisition.requisition_id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")
    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(req, key, val)
    await db.flush()
    await db.refresh(req)
    return RequisitionResponse.model_validate(req)


@router.delete("/{req_id}", status_code=204)
async def delete_requisition(
    req_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("requisitions:delete")),
):
    result = await db.execute(select(Requisition).where(Requisition.requisition_id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Requisition not found")
    await db.delete(req)
    await db.flush()
