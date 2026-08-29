"""
AI Service: OpenRouter integration for CV parsing, scoring, and semantic search.
"""
import httpx
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models import (
    Candidate, Requisition, Score, Skill, EmploymentHistory,
    LLMPromptVersion, ConfidenceFlag, SyncStatusRecord, SyncStatus
)


class AIService:
    BASE_URL = "https://openrouter.ai/api/v1"

    async def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://talentpool.app",
            "X-Title": "Talent Pool Management System",
        }

    async def _get_model(self) -> str:
        """Get the best available model (primary, fallback, or a free default)."""
        if settings.OPENROUTER_PRIMARY_MODEL:
            return settings.OPENROUTER_PRIMARY_MODEL
        if settings.OPENROUTER_FALLBACK_MODEL:
            return settings.OPENROUTER_FALLBACK_MODEL
        # Default free model
        return "mistralai/mistral-7b-instruct:free"

    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to the OpenRouter LLM API."""
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OpenRouter API key not configured")

        model = await self._get_model()
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": settings.OPENROUTER_MAX_TOKENS,
                    "temperature": settings.OPENROUTER_TEMPERATURE,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def fetch_free_models(self) -> List[Dict[str, Any]]:
        """Fetch available free models from OpenRouter."""
        if not settings.OPENROUTER_API_KEY:
            return []

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/models",
                headers=await self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

        free_models = []
        for model in data.get("data", []):
            pricing = model.get("pricing", {})
            prompt_price = float(pricing.get("prompt", "1"))
            completion_price = float(pricing.get("completion", "1"))

            is_free = prompt_price == 0 and completion_price == 0
            provider = model.get("id", "").split("/")[0] if "/" in model.get("id", "") else "unknown"

            free_models.append({
                "id": model.get("id"),
                "name": model.get("name", model.get("id")),
                "provider": provider,
                "context_length": model.get("context_length", 4096),
                "is_free": is_free,
                "pricing": pricing,
            })

        return free_models

    async def parse_cv(self, cv_text: str) -> Dict[str, Any]:
        """Parse CV text using LLM to extract structured information."""
        system_prompt = """You are an expert CV/resume parser. Extract structured information from the provided CV text.
Return ONLY a valid JSON object with these fields:
{
    "full_name": "string",
    "email": "string or null",
    "phone": "string or null",
    "linkedin_url": "string or null",
    "city": "string or null",
    "skills": ["skill1", "skill2"],
    "employment_history": [
        {"company": "string", "title": "string", "duration": "string", "description": "string"}
    ],
    "career_level": "Entry|Mid|Senior|Lead|Managerial",
    "applied_designation": "most recent or target job title",
    "department_tag": "Engineering|Marketing|Sales|Finance|HR|Operations|IT|Other",
    "tags": ["relevant", "tags"],
    "education": "summary of education"
}
Return ONLY the JSON, no other text."""

        result = await self._call_llm(system_prompt, f"Parse this CV:\n\n{cv_text}")

        # Extract JSON from response
        try:
            # Try to find JSON in the response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            return json.loads(result.strip())
        except json.JSONDecodeError:
            # Fallback: try to find any JSON object
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(result[start:end])
            raise ValueError("Failed to parse LLM response as JSON")

    async def score_candidate(
        self,
        candidate: Candidate,
        requisition: Requisition,
        db: AsyncSession,
    ) -> Score:
        """Score a candidate against a job requisition using AI."""

        # Build candidate profile string
        skills_result = await db.execute(select(Skill).where(Skill.candidate_id == candidate.candidate_id))
        skills = skills_result.scalars().all()
        history_result = await db.execute(
            select(EmploymentHistory).where(EmploymentHistory.candidate_id == candidate.candidate_id)
        )
        history = history_result.scalars().all()

        candidate_profile = f"""
Name: {candidate.full_name}
Email: {candidate.email or 'N/A'}
Phone: {candidate.phone or 'N/A'}
City: {candidate.city or 'N/A'}
Career Level: {candidate.career_level.value if candidate.career_level else 'N/A'}
Employment Type: {candidate.employment_type.value if candidate.employment_type else 'N/A'}
Department: {candidate.department_tag or 'N/A'}
Applied Designation: {candidate.applied_designation or 'N/A'}
Skills: {', '.join(s.skill_name for s in skills)}
Employment History:
{chr(10).join(f"- {h.title or 'N/A'} at {h.company or 'N/A'} ({h.duration or 'N/A'}): {h.description or ''}" for h in history)}
"""

        requisition_text = f"""
Designation: {requisition.designation}
Department: {requisition.department or 'N/A'}
Location: {requisition.location or 'N/A'}
Required Skills: {', '.join(requisition.required_skills) if requisition.required_skills else 'N/A'}
Experience: {requisition.experience_years or 'N/A'} years
Description: {requisition.description or 'N/A'}
"""

        system_prompt = """You are an expert recruitment AI. Score a candidate against a job requisition.
Return ONLY a valid JSON object:
{
    "ranking_score": 0-100 (number),
    "skill_match": 0-100 (percentage of skills that match),
    "experience_match": 0-100 (how well experience aligns),
    "education_match": 0-100 (education relevance),
    "location_match": 0-100 (location suitability),
    "keyword_match": 0-100 (keyword density match),
    "confidence": "High|Medium|Low",
    "reasoning": "Brief explanation of the score"
}
Return ONLY the JSON, no other text."""

        user_prompt = f"""Score this candidate against the job requisition:

CANDIDATE PROFILE:
{candidate_profile}

JOB REQUISITION:
{requisition_text}"""

        result = await self._call_llm(system_prompt, user_prompt)

        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            score_data = json.loads(result.strip())
        except json.JSONDecodeError:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                score_data = json.loads(result[start:end])
            else:
                score_data = {"ranking_score": 50, "confidence": "Low", "reasoning": "Failed to parse AI response"}

        confidence_map = {"High": ConfidenceFlag.high, "Medium": ConfidenceFlag.medium, "Low": ConfidenceFlag.low}

        score = Score(
            candidate_id=candidate.candidate_id,
            requisition_id=requisition.requisition_id,
            ranking_score=min(100, max(0, float(score_data.get("ranking_score", 50)))),
            score_breakdown_json={
                "skill_match": score_data.get("skill_match", 0),
                "experience_match": score_data.get("experience_match", 0),
                "education_match": score_data.get("education_match", 0),
                "location_match": score_data.get("location_match", 0),
                "keyword_match": score_data.get("keyword_match", 0),
                "reasoning": score_data.get("reasoning", ""),
            },
            score_model_version=await self._get_model(),
            confidence_flag=confidence_map.get(score_data.get("confidence", "Medium"), ConfidenceFlag.medium),
        )

        db.add(score)
        await db.flush()
        await db.refresh(score)

        # Auto-sync check
        await self._check_sync(candidate, score, db)

        return score

    async def _check_sync(self, candidate: Candidate, score: Score, db: AsyncSession):
        """Check if candidate meets sync threshold and queue for ERPNext sync."""
        sync_result = await db.execute(select(SyncStatusRecord).where(SyncStatusRecord.candidate_id == candidate.candidate_id))
        sync_record = sync_result.scalar_one_or_none()

        if not sync_record:
            sync_record = SyncStatusRecord(candidate_id=candidate.candidate_id)
            db.add(sync_record)
            await db.flush()

        threshold = settings.DEFAULT_SYNC_THRESHOLD
        meets_threshold = float(score.ranking_score) >= threshold
        confidence_ok = score.confidence_flag != ConfidenceFlag.low

        sync_record.sync_threshold_met = meets_threshold

        if meets_threshold and confidence_ok and sync_record.sync_status == SyncStatus.not_synced:
            # Queue for ERPNext sync
            from app.services.erpnext_service import ERPNextService
            erp = ERPNextService()
            await erp.sync_candidate_to_erpnext(candidate, db)

    async def semantic_search(self, query: str, db: AsyncSession, limit: int = 10) -> List[Candidate]:
        """Semantic search using AI-powered relevance scoring."""
        system_prompt = """You are a recruitment search assistant. Given a natural language query about candidates,
generate a structured search profile. Return ONLY valid JSON:
{
    "skills": ["required skills"],
    "experience_years": number or null,
    "career_level": "Entry|Mid|Senior|Lead|Managerial" or null,
    "department": "department name" or null,
    "location": "city/region" or null,
    "keywords": ["additional keywords"]
}"""

        result = await self._call_llm(system_prompt, f"Parse this recruitment search query: {query}")
        try:
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            search_profile = json.loads(result.strip())
        except (json.JSONDecodeError, IndexError):
            search_profile = {"keywords": query.split()}

        # Build SQL filters based on extracted profile
        filters = []
        if search_profile.get("department"):
            filters.append(Candidate.department_tag.ilike(f"%{search_profile['department']}%"))
        if search_profile.get("career_level"):
            filters.append(Candidate.career_level == search_profile["career_level"])
        if search_profile.get("location"):
            filters.append(Candidate.city.ilike(f"%{search_profile['location']}%"))

        query_stmt = select(Candidate)
        if filters:
            from sqlalchemy import and_
            query_stmt = query_stmt.where(and_(*filters))

        # If skills are specified, also search by skill
        if search_profile.get("skills"):
            skill_filters = []
            for skill in search_profile["skills"]:
                skill_filters.append(
                    Candidate.candidate_id.in_(
                        select(Skill.candidate_id).where(Skill.skill_name.ilike(f"%{skill}%"))
                    )
                )
            if skill_filters:
                from sqlalchemy import or_
                query_stmt = query_stmt.where(or_(*skill_filters))

        query_stmt = query_stmt.limit(limit)
        result = await db.execute(query_stmt)
        return result.scalars().all()
