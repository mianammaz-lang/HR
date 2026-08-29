"""
ERPNext integration service: sync candidates, import requisitions.
"""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models import (
    Candidate, Requisition, SyncStatusRecord, SyncStatus,
    Skill, RequisitionStatus
)


class ERPNextService:

    def _get_auth(self):
        return (settings.ERP_API_KEY, settings.ERP_API_SECRET)

    def _get_base_url(self) -> str:
        url = settings.ERP_NEXT_URL or ""
        return url.rstrip("/")

    async def test_connection(self) -> Dict[str, Any]:
        """Test ERPNext connection."""
        if not settings.ERP_NEXT_URL:
            return {"success": False, "message": "ERPNext URL not configured"}
        if not settings.ERP_API_KEY or not settings.ERP_API_SECRET:
            return {"success": False, "message": "ERPNext API credentials not configured"}

        try:
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                response = await client.get(
                    f"{self._get_base_url}/api/resource/User",
                    auth=self._get_auth(),
                    params={"limit_page_length": 1},
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Connected successfully", "details": response.json()}
                else:
                    return {"success": False, "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}

    async def sync_candidate_to_erpnext(self, candidate: Candidate, db: AsyncSession) -> Dict[str, Any]:
        """Sync a candidate to ERPNext as a Job Applicant."""
        sync_result = await db.execute(
            select(SyncStatusRecord).where(SyncStatusRecord.candidate_id == candidate.candidate_id)
        )
        sync_record = sync_result.scalar_one_or_none()

        if not sync_record:
            sync_record = SyncStatusRecord(candidate_id=candidate.candidate_id)
            db.add(sync_record)
            await db.flush()

        if not settings.ERP_NEXT_URL or not settings.ERP_API_KEY:
            sync_record.sync_status = SyncStatus.sync_failed
            sync_record.sync_error_log = "ERPNext not configured"
            await db.flush()
            return {"success": False, "message": "ERPNext not configured"}

        doctype = settings.DEFAULT_JOB_APPLICANT_DOCTYPE or "Job Applicant"

        payload = {
            "applicant_name": candidate.full_name,
            "email_address": candidate.email or "",
            "phone_number": candidate.phone or "",
            "designation": candidate.applied_designation or "",
            "source": candidate.source_channel.value if candidate.source_channel else "",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.post(
                    f"{self._get_base_url}/api/resource/{doctype}",
                    auth=self._get_auth(),
                    json=payload,
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    applicant_id = data.get("data", {}).get("name", "")
                    sync_record.sync_status = SyncStatus.synced
                    sync_record.erpnext_applicant_id = applicant_id
                    sync_record.synced_at = datetime.utcnow()
                    sync_record.sync_error_log = None
                else:
                    sync_record.sync_status = SyncStatus.sync_failed
                    sync_record.sync_error_log = f"HTTP {response.status_code}: {response.text[:500]}"

        except Exception as e:
            sync_record.sync_status = SyncStatus.sync_failed
            sync_record.sync_error_log = str(e)

        await db.flush()
        return {"success": sync_record.sync_status == SyncStatus.synced}

    async def import_requisitions(self, db: AsyncSession) -> int:
        """Import job requisitions from ERPNext."""
        if not settings.ERP_NEXT_URL or not settings.ERP_API_KEY:
            return 0

        doctype = "Job Opening"
        imported = 0

        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                response = await client.get(
                    f"{self._get_base_url}/api/resource/{doctype}",
                    auth=self._get_auth(),
                    params={"limit_page_length": 100, "filters": '[["status","=","Open"]]'},
                )

                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("data", []):
                        erp_id = item.get("name", "")
                        # Check if already exists
                        existing = await db.execute(
                            select(Requisition).where(Requisition.erpnext_requisition_id == erp_id)
                        )
                        if existing.scalar_one_or_none():
                            continue

                        req = Requisition(
                            erpnext_requisition_id=erp_id,
                            designation=item.get("job_title", ""),
                            department=item.get("department", ""),
                            location=item.get("location", ""),
                            status=RequisitionStatus.open,
                            description=item.get("description", ""),
                        )
                        db.add(req)
                        imported += 1

                    await db.flush()

        except Exception:
            pass

        return imported

    async def retry_failed_syncs(self, db: AsyncSession) -> int:
        """Retry all failed syncs."""
        result = await db.execute(
            select(SyncStatusRecord).where(SyncStatusRecord.sync_status == SyncStatus.sync_failed)
        )
        failed = result.scalars().all()
        retried = 0

        for sync_record in failed:
            cand_result = await db.execute(
                select(Candidate).where(Candidate.candidate_id == sync_record.candidate_id)
            )
            candidate = cand_result.scalar_one_or_none()
            if candidate:
                await self.sync_candidate_to_erpnext(candidate, db)
                retried += 1

        return retried
