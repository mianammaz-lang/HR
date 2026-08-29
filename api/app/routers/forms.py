"""
Application Forms: public candidate forms + admin management.
Also: ERP sync status column + manual send to ERP.
"""
import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    ApplicationForm, FormSubmission, Candidate, Requisition,
    Skill, EmploymentHistory, SyncStatusRecord, Document,
    AuditLog, SystemSetting, SyncStatus, CareerLevel, EmploymentType
)
from app.auth import get_current_user, require_permission
from app.services.cv_parser import BuiltInCVParser
from app.config import UPLOAD_DIR

router = APIRouter(prefix="/api", tags=["Application Forms"])


# --- Schemas ---

class FormCreate(BaseModel):
    requisition_id: str
    title: str
    description: Optional[str] = None
    expires_at: Optional[str] = None
    custom_fields: Optional[list] = []

class FormUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[str] = None
    custom_fields: Optional[list] = None


# --- Admin Endpoints ---

@router.get("/admin/forms", response_model=list)
async def list_forms(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("requisitions:read")),
):
    result = await db.execute(
        select(ApplicationForm).options(
            selectinload(ApplicationForm.requisition)
        ).order_by(ApplicationForm.created_at.desc())
    )
    forms = result.scalars().all()
    items = []
    for f in forms:
        sub_count = (await db.execute(
            select(func.count(FormSubmission.submission_id)).where(FormSubmission.form_id == f.form_id)
        )).scalar() or 0
        items.append({
            "form_id": f.form_id,
            "title": f.title,
            "description": f.description,
            "requisition_id": f.requisition_id,
            "requisition_title": f.requisition.designation if f.requisition else None,
            "is_active": f.is_active,
            "expires_at": f.expires_at.isoformat() if f.expires_at else None,
            "submissions_count": sub_count,
            "created_at": f.created_at.isoformat(),
        })
    return items


@router.post("/admin/forms", status_code=201)
async def create_form(
    body: FormCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("requisitions:write")),
):
    req = (await db.execute(select(Requisition).where(Requisition.requisition_id == body.requisition_id))).scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requisition not found")

    expires = None
    if body.expires_at:
        expires = datetime.fromisoformat(body.expires_at)

    form = ApplicationForm(
        requisition_id=body.requisition_id,
        title=body.title,
        description=body.description or f"Apply for {req.designation}",
        expires_at=expires,
        custom_fields=body.custom_fields or [],
    )
    db.add(form)
    await db.flush()
    await db.refresh(form)
    return {"form_id": form.form_id, "title": form.title, "is_active": form.is_active}


@router.put("/admin/forms/{form_id}")
async def update_form(
    form_id: str,
    body: FormUpdate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("requisitions:write")),
):
    form = (await db.execute(select(ApplicationForm).where(ApplicationForm.form_id == form_id))).scalar_one_or_none()
    if not form:
        raise HTTPException(404, "Form not found")
    for key, val in body.model_dump(exclude_unset=True).items():
        if key == "expires_at" and val:
            val = datetime.fromisoformat(val)
        setattr(form, key, val)
    await db.flush()
    return {"status": "ok"}


@router.delete("/admin/forms/{form_id}", status_code=204)
async def delete_form(
    form_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("requisitions:delete")),
):
    form = (await db.execute(select(ApplicationForm).where(ApplicationForm.form_id == form_id))).scalar_one_or_none()
    if not form:
        raise HTTPException(404, "Form not found")
    await db.delete(form)
    await db.flush()


@router.get("/admin/forms/{form_id}/submissions")
async def list_submissions(
    form_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("requisitions:read")),
):
    result = await db.execute(
        select(FormSubmission).where(FormSubmission.form_id == form_id).order_by(FormSubmission.submitted_at.desc())
    )
    subs = result.scalars().all()
    return [
        {
            "submission_id": s.submission_id,
            "full_name": s.full_name,
            "email": s.email,
            "phone": s.phone,
            "linkedin_url": s.linkedin_url,
            "cover_letter": s.cover_letter,
            "resume_filename": s.resume_filename,
            "candidate_id": s.candidate_id,
            "submitted_at": s.submitted_at.isoformat(),
        }
        for s in subs
    ]


# --- Public Endpoints ---

@router.get("/apply/{form_id}")
async def get_public_form(form_id: str, db: AsyncSession = Depends(get_db)):
    form = (await db.execute(
        select(ApplicationForm).options(
            selectinload(ApplicationForm.requisition)
        ).where(ApplicationForm.form_id == form_id)
    )).scalar_one_or_none()

    if not form or not form.is_active:
        raise HTTPException(404, "Application form not found or inactive")
    if form.expires_at and form.expires_at < datetime.utcnow():
        raise HTTPException(410, "This application form has expired")

    req = form.requisition
    return {
        "form_id": form.form_id,
        "title": form.title,
        "description": form.description,
        "expires_at": form.expires_at.isoformat() if form.expires_at else None,
        "requisition": {
            "designation": req.designation,
            "department": req.department,
            "location": req.location,
            "description": req.description,
            "required_skills": req.required_skills,
            "experience_years": req.experience_years,
            "employment_type": req.employment_type.value if req.employment_type else None,
        },
        "custom_fields": form.custom_fields,
    }


@router.post("/apply/{form_id}", status_code=201)
async def submit_application(
    form_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    form = (await db.execute(
        select(ApplicationForm).where(ApplicationForm.form_id == form_id)
    )).scalar_one_or_none()

    if not form or not form.is_active:
        raise HTTPException(404, "Form not found or inactive")
    if form.expires_at and form.expires_at < datetime.utcnow():
        raise HTTPException(410, "This form has expired")

    # Accept both JSON and multipart
    ct = request.headers.get("content-type", "")
    full_name = email = phone = linkedin_url = cover_letter = ""
    custom_answers = {}
    resume_filename = None

    if "multipart" in ct:
        form_data = await request.form()
        full_name = form_data.get("full_name", "")
        email = form_data.get("email", "")
        phone = form_data.get("phone", "")
        linkedin_url = form_data.get("linkedin_url", "")
        cover_letter = form_data.get("cover_letter", "")
        for key in form_data:
            if key.startswith("custom_"):
                custom_answers[key] = form_data[key]

        # Handle resume upload
        resume_file = form_data.get("resume")
        resume_filename = None
        saved_resume_path = None
        if resume_file and hasattr(resume_file, "read"):
            content = await resume_file.read()
            if content:
                resume_filename = resume_file.filename
                fid = str(uuid.uuid4())
                ext = resume_filename.rsplit(".", 1)[-1] if "." in resume_filename else "pdf"
                saved_resume_path = os.path.join(UPLOAD_DIR, fid + "." + ext)
                with open(saved_resume_path, "wb") as fobj:
                    fobj.write(content)
    else:
        body = await request.json()
        full_name = body.get("full_name", "")
        email = body.get("email", "")
        phone = body.get("phone", "")
        linkedin_url = body.get("linkedin_url", "")
        cover_letter = body.get("cover_letter", "")
        custom_answers = body.get("custom_answers", {})
        saved_resume_path = None

    if not full_name:
        raise HTTPException(400, "Full name is required")

    dup_hash = None
    if email or phone:
        dup_hash = hashlib.sha256((email.strip().lower() + phone.strip()).encode()).hexdigest()

    is_dup = None
    if dup_hash:
        ex = (await db.execute(select(Candidate).where(Candidate.duplicate_check_hash == dup_hash))).scalar_one_or_none()
        if ex:
            is_dup = ex.candidate_id

    req_obj = (await db.execute(select(Requisition).where(Requisition.requisition_id == form.requisition_id))).scalar_one_or_none()

    candidate = Candidate(
        full_name=full_name, email=email, phone=phone, linkedin_url=linkedin_url,
        applied_designation=req_obj.designation if req_obj else "",
        department_tag=req_obj.department if req_obj else "",
        matched_open_requisition_id=form.requisition_id,
        duplicate_check_hash=dup_hash, is_duplicate_of=is_dup,
        tags=["Applied via form"],
    )
    db.add(candidate)
    await db.flush()

    submission = FormSubmission(
        form_id=form.form_id, candidate_id=candidate.candidate_id,
        full_name=full_name, email=email, phone=phone, linkedin_url=linkedin_url,
        cover_letter=cover_letter, custom_answers=custom_answers,
        resume_filename=resume_filename,
    )
    db.add(submission)
    db.add(SyncStatusRecord(candidate_id=candidate.candidate_id))

    if resume_filename:
        db.add(Document(candidate_id=candidate.candidate_id, original_filename=resume_filename, resume_file_url=saved_resume_path or f"form:{resume_filename}"))

    if cover_letter:
        parser = BuiltInCVParser()
        parsed = parser.parse(cover_letter)
        for s in parsed.get("skills", [])[:20]:
            db.add(Skill(candidate_id=candidate.candidate_id, skill_name=s))

    return {"status": "ok", "message": "Application submitted", "candidate_id": str(candidate.candidate_id)}


# --- Manual ERP Sync ---

class ManualERPSync(BaseModel):
    candidate_ids: list[str]

@router.post("/admin/sync-erp")
async def manual_sync_to_erp(
    body: ManualERPSync,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("sync:manage")),
):
    from app.services.erpnext_service import ERPNextService
    erp = ERPNextService()
    results = []
    for cid in body.candidate_ids:
        cand = (await db.execute(select(Candidate).where(Candidate.candidate_id == cid))).scalar_one_or_none()
        if not cand:
            results.append({"candidate_id": cid, "status": "not_found"})
            continue
        sync = (await db.execute(select(SyncStatusRecord).where(SyncStatusRecord.candidate_id == cid))).scalar_one_or_none()
        if sync and sync.sync_status == SyncStatus.synced:
            results.append({"candidate_id": cid, "status": "already_synced", "erpnext_id": sync.erpnext_applicant_id})
            continue
        res = await erp.sync_candidate_to_erpnext(cand, db)
        sync = (await db.execute(select(SyncStatusRecord).where(SyncStatusRecord.candidate_id == cid))).scalar_one_or_none()
        results.append({
            "candidate_id": cid,
            "status": "synced" if res.get("success") else "failed",
            "erpnext_id": sync.erpnext_applicant_id if sync else None,
            "error": sync.sync_error_log if sync and sync.sync_error_log else None,
        })
    return {"results": results}

# --- Public Resume Download (for form-submitted candidates) ---

@router.get("/apply/resume/{doc_id}")
async def public_download_resume(doc_id: str, db: AsyncSession = Depends(get_db)):
    """Public resume download - anyone with the link can view."""
    from fastapi.responses import FileResponse
    result = await db.execute(select(Document).where(Document.doc_id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc or not doc.resume_file_url:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(doc.resume_file_url):
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
    return FileResponse(
        doc.resume_file_url,
        filename=doc.original_filename or "resume",
        media_type="application/octet-stream",
    )
