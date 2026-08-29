"""
Settings management: ERPNext, LLM, system settings.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import SystemSetting, LLMPromptVersion, User, AuditLog
from app.schemas import ERPNextSettings, ERPNextTestResult, LLMSettingsUpdate, LLMSettingsResponse, LLMModel
from app.auth import require_permission
from app.config import settings
from app.services.erpnext_service import ERPNextService
from app.services.ai_service import AIService

router = APIRouter(prefix="/api/settings", tags=["Settings"])


# ─── ERPNext Settings ─────────────────────────────────────────────────────────

@router.get("/erpnext", response_model=ERPNextSettings)
async def get_erpnext_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:read")),
):
    erp_url = await _get_setting(db, "erp_next_url", settings.ERP_NEXT_URL)
    api_key = await _get_setting(db, "erp_api_key", settings.ERP_API_KEY)
    api_secret = await _get_setting(db, "erp_api_secret", settings.ERP_API_SECRET)
    company = await _get_setting(db, "erp_default_company", "")
    doctype = await _get_setting(db, "erp_job_applicant_doctype", "Job Applicant")
    threshold = await _get_setting(db, "sync_threshold", settings.DEFAULT_SYNC_THRESHOLD)

    return ERPNextSettings(
        url=erp_url or "",
        api_key=api_key or "",
        api_secret="***" if api_secret else "",
        default_company=company or "",
        default_job_applicant_doctype=doctype or "",
        sync_threshold=float(threshold) if threshold else 60.0,
    )


@router.put("/erpnext", response_model=ERPNextSettings)
async def update_erpnext_settings(
    body: ERPNextSettings,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:write")),
):
    await _set_setting(db, "erp_next_url", body.url)
    if body.api_key and body.api_key != "***":
        await _set_setting(db, "erp_api_key", body.api_key)
    if body.api_secret and body.api_secret != "***":
        await _set_setting(db, "erp_api_secret", body.api_secret)
    await _set_setting(db, "erp_default_company", body.default_company)
    await _set_setting(db, "erp_job_applicant_doctype", body.default_job_applicant_doctype)
    await _set_setting(db, "sync_threshold", body.sync_threshold)
    return body


@router.post("/erpnext/test", response_model=ERPNextTestResult)
async def test_erpnext_connection(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:write")),
):
    erp = ERPNextService()
    result = await erp.test_connection()
    return ERPNextTestResult(**result)


@router.post("/erpnext/import-requisitions")
async def import_requisitions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:write")),
):
    erp = ERPNextService()
    count = await erp.import_requisitions(db)
    return {"imported": count}


@router.post("/erpnext/retry-syncs")
async def retry_failed_syncs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:write")),
):
    erp = ERPNextService()
    retried = await erp.retry_failed_syncs(db)
    return {"retried": retried}


# ─── LLM Settings ─────────────────────────────────────────────────────────────

@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:read")),
):
    auto_discovery = await _get_setting(db, "llm_auto_discovery", True)
    primary_model = await _get_setting(db, "llm_primary_model", settings.OPENROUTER_PRIMARY_MODEL)
    fallback_model = await _get_setting(db, "llm_fallback_model", settings.OPENROUTER_FALLBACK_MODEL)
    max_tokens = await _get_setting(db, "llm_max_tokens", settings.OPENROUTER_MAX_TOKENS)
    temperature = await _get_setting(db, "llm_temperature", settings.OPENROUTER_TEMPERATURE)
    system_prompt = await _get_setting(db, "llm_system_prompt", "")

    available = []
    if settings.OPENROUTER_API_KEY and auto_discovery:
        try:
            ai = AIService()
            available = await ai.fetch_free_models()
        except Exception:
            pass

    return LLMSettingsResponse(
        api_key_set=bool(settings.OPENROUTER_API_KEY),
        auto_discovery=bool(auto_discovery),
        primary_model=primary_model,
        fallback_model=fallback_model,
        max_tokens=int(max_tokens) if max_tokens else 4096,
        temperature=float(temperature) if temperature else 0.3,
        system_prompt=system_prompt or "",
        available_models=[LLMModel(**m) for m in available],
    )


@router.put("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(
    body: LLMSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("settings:write")),
):
    if body.api_key is not None:
        settings.OPENROUTER_API_KEY = body.api_key
    if body.auto_discovery is not None:
        await _set_setting(db, "llm_auto_discovery", body.auto_discovery)
    if body.primary_model is not None:
        await _set_setting(db, "llm_primary_model", body.primary_model)
    if body.fallback_model is not None:
        await _set_setting(db, "llm_fallback_model", body.fallback_model)
    if body.max_tokens is not None:
        await _set_setting(db, "llm_max_tokens", body.max_tokens)
    if body.temperature is not None:
        await _set_setting(db, "llm_temperature", body.temperature)
    if body.system_prompt is not None:
        await _set_setting(db, "llm_system_prompt", body.system_prompt)

    return await get_llm_settings(db=db, user=user)


@router.get("/llm/models")
async def list_llm_models(
    user: User = Depends(require_permission("settings:read")),
):
    ai = AIService()
    models = await ai.fetch_free_models()
    return {"models": models, "total": len(models)}


@router.get("/llm/prompts")
async def list_prompt_versions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("prompts:read")),
):
    result = await db.execute(select(LLMPromptVersion).order_by(LLMPromptVersion.created_at.desc()))
    prompts = result.scalars().all()
    return [
        {
            "prompt_id": str(p.prompt_id),
            "name": p.name,
            "prompt_type": p.prompt_type,
            "version": p.version,
            "is_active": p.is_active,
            "system_prompt": p.system_prompt,
            "user_prompt_template": p.user_prompt_template,
        }
        for p in prompts
    ]


# ─── Audit Logs ───────────────────────────────────────────────────────────────

@router.get("/audit-logs")
async def get_audit_logs(
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission("audit:read")),
):
    from app.models import AuditLog
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    count_result = await db.execute(select(func.count(AuditLog.log_id)))
    total = count_result.scalar() or 0

    return {
        "items": [
            {
                "log_id": str(l.log_id),
                "user_id": str(l.user_id) if l.user_id else None,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "details": l.details,
                "created_at": l.created_at.isoformat(),
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ─── Helpers ──────────────────────────────────────────────────────────────────

async def _get_setting(db: AsyncSession, key: str, default=None):
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        return setting.value
    return default


async def _set_setting(db: AsyncSession, key: str, value):
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        db.add(SystemSetting(key=key, value=value))
    await db.flush()
