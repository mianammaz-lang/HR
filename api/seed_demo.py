"""Seed demo data for Talent Pool Management System."""
import asyncio, sys, random
sys.stdout.reconfigure(encoding="utf-8")

from app.database import AsyncSessionLocal, engine, init_db
from app.models import (
    Candidate, EmploymentHistory, Skill, Score, SyncStatusRecord,
    Requisition
)
from app.models import (
    new_uuid, SourceChannel, CareerLevel, EmploymentType,
    SyncStatus, ConfidenceFlag, RequisitionStatus
)
from datetime import datetime, timedelta

CANDIDATES = [
    {"name": "Ahmed Al-Rashid", "email": "ahmed.rashid@gmail.com", "phone": "+971501234567", "city": "Dubai", "dept": "Engineering", "level": "Senior", "title": "Senior Python Developer"},
    {"name": "Fatima Hassan", "email": "fatima.h@outlook.com", "phone": "+971552345678", "city": "Abu Dhabi", "dept": "Marketing", "level": "Managerial", "title": "Marketing Director"},
    {"name": "Omar Khalil", "email": "omar.khalil@yahoo.com", "phone": "+971563456789", "city": "Dubai", "dept": "Engineering", "level": "Mid", "title": "Full Stack Developer"},
    {"name": "Sara Al-Mansouri", "email": "sara.m@gmail.com", "phone": "+971574567890", "city": "Sharjah", "dept": "HR", "level": "Senior", "title": "HR Manager"},
    {"name": "Khalid Al-Farsi", "email": "khalid.f@outlook.com", "phone": "+971585678901", "city": "Dubai", "dept": "Finance", "level": "Lead", "title": "Financial Analyst"},
    {"name": "Mariam Saleh", "email": "mariam.s@gmail.com", "phone": "+966501234567", "city": "Riyadh", "dept": "Engineering", "level": "Senior", "title": "DevOps Engineer"},
    {"name": "Yusuf Nasser", "email": "yusuf.n@yahoo.com", "phone": "+971509876543", "city": "Dubai", "dept": "Engineering", "level": "Entry", "title": "Junior Developer"},
    {"name": "Layla Ibrahim", "email": "layla.i@gmail.com", "phone": "+97336123456", "city": "Manama", "dept": "Marketing", "level": "Mid", "title": "Digital Marketing Specialist"},
    {"name": "Hassan Ali", "email": "hassan.ali@outlook.com", "phone": "+97455123456", "city": "Doha", "dept": "Engineering", "level": "Managerial", "title": "Engineering Manager"},
    {"name": "Noura Al-Ketbi", "email": "noura.k@gmail.com", "phone": "+971523456789", "city": "Abu Dhabi", "dept": "Finance", "level": "Senior", "title": "Senior Accountant"},
    {"name": "Tariq Mohammed", "email": "tariq.m@yahoo.com", "phone": "+971545678901", "city": "Dubai", "dept": "Engineering", "level": "Mid", "title": "React Developer"},
    {"name": "Reem Al-Shamsi", "email": "reem.s@gmail.com", "phone": "+971567890123", "city": "Sharjah", "dept": "HR", "level": "Mid", "title": "Recruiter"},
    {"name": "Bilal Ahmad", "email": "bilal.a@outlook.com", "phone": "+923001234567", "city": "Dubai", "dept": "Engineering", "level": "Senior", "title": "Cloud Architect"},
    {"name": "Aisha Patel", "email": "aisha.p@gmail.com", "phone": "+971590123456", "city": "Dubai", "dept": "Marketing", "level": "Senior", "title": "Brand Manager"},
    {"name": "Zayed Al-Nuaimi", "email": "zayed.n@yahoo.com", "phone": "+971501112233", "city": "Abu Dhabi", "dept": "Engineering", "level": "Lead", "title": "Tech Lead"},
    {"name": "Dana Khaled", "email": "dana.k@gmail.com", "phone": "+971552223344", "city": "Dubai", "dept": "Finance", "level": "Entry", "title": "Junior Financial Analyst"},
    {"name": "Rashed Bin Salem", "email": "rashed.bs@outlook.com", "phone": "+971563334455", "city": "Ras Al Khaimah", "dept": "Engineering", "level": "Senior", "title": "Backend Developer"},
    {"name": "Mona Farouk", "email": "mona.f@gmail.com", "phone": "+201012345678", "city": "Dubai", "dept": "Marketing", "level": "Mid", "title": "Content Strategist"},
    {"name": "Sultan Al-Dhaheri", "email": "sultan.d@yahoo.com", "phone": "+971584445566", "city": "Al Ain", "dept": "Engineering", "level": "Managerial", "title": "VP Engineering"},
    {"name": "Huda Mirza", "email": "huda.m@outlook.com", "phone": "+971595556677", "city": "Dubai", "dept": "HR", "level": "Senior", "title": "Talent Acquisition Lead"},
]

SKILLS = {
    "Engineering": ["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Docker", "Kubernetes", "AWS", "FastAPI", "Django", "TypeScript", "MongoDB", "Redis", "Git", "CI/CD", "Linux", "Terraform"],
    "Marketing": ["SEO", "Google Analytics", "Social Media", "Content Marketing", "Email Marketing", "HubSpot", "Salesforce", "Brand Strategy", "PPC", "Copywriting", "CRM"],
    "Finance": ["Excel", "SQL", "Financial Modeling", "SAP", "IFRS", "GAAP", "Risk Analysis", "Bloomberg", "Power BI", "Tableau", "Python"],
    "HR": ["Recruitment", "HRIS", "BambooHR", "Workday", "Employee Relations", "Performance Management", "Labor Law", "ATS", "Training & Development"],
}

COMPANIES = ["ADNOC", "Emirates NBD", "Mubadala", "DP World", "Etisalat", "ADIB", "FAB", "ENOC", "DAMAC", "Emaar", "Aramco", "SABIC", "QNB", "Google", "Microsoft", "Amazon", "Careem", "Noon"]

TITLES = {
    "Engineering": ["Software Engineer", "Senior Developer", "Tech Lead", "DevOps Engineer", "Full Stack Developer", "Backend Developer"],
    "Marketing": ["Marketing Manager", "Digital Marketing Specialist", "Brand Manager", "Content Strategist", "SEO Specialist"],
    "Finance": ["Financial Analyst", "Senior Accountant", "Finance Manager", "Risk Analyst", "Investment Analyst"],
    "HR": ["HR Manager", "Recruiter", "Talent Acquisition Specialist", "HR Business Partner", "HR Director"],
}

REQUISITIONS = [
    {"designation": "Senior Python Developer", "department": "Engineering", "location": "Dubai", "description": "Senior Python developer with FastAPI and PostgreSQL experience.", "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"], "exp": 5},
    {"designation": "Marketing Director", "department": "Marketing", "location": "Abu Dhabi", "description": "Experienced Marketing Director for GCC region.", "skills": ["Brand Strategy", "Digital Marketing", "SEO", "Google Analytics"], "exp": 8},
    {"designation": "Financial Analyst", "department": "Finance", "location": "Dubai", "description": "Detail-oriented financial analyst. Banking experience preferred.", "skills": ["Excel", "SQL", "Financial Modeling", "Power BI", "IFRS"], "exp": 3},
    {"designation": "DevOps Engineer", "department": "Engineering", "location": "Riyadh", "description": "Infrastructure engineer. Kubernetes and Terraform required.", "skills": ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD"], "exp": 4},
    {"designation": "HR Manager", "department": "HR", "location": "Dubai", "description": "Experienced HR professional. GCC experience preferred.", "skills": ["Recruitment", "HRIS", "Employee Relations", "Labor Law"], "exp": 6},
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        count_result = await db.execute(select(func.count()).select_from(Candidate))
        count_val = count_result.scalar_one()
        if count_val > 0:
            print(f"Already has {count_val} candidates. Skipping.")
            await engine.dispose()
            return

        # Requisitions
        req_ids = []
        for r in REQUISITIONS:
            req = Requisition(
                requisition_id=new_uuid(), designation=r["designation"],
                department=r["department"], location=r["location"],
                description=r["description"], required_skills=r["skills"],
                experience_years=r["exp"], status=RequisitionStatus.open,
            )
            db.add(req)
            req_ids.append(req.requisition_id)
        await db.flush()
        print(f"Created {len(req_ids)} requisitions")

        # Candidates
        for i, c in enumerate(CANDIDATES):
            cid = new_uuid()
            dept = c["dept"]
            lvl = c["level"]

            db.add(Candidate(
                candidate_id=cid, full_name=c["name"], email=c["email"],
                phone=c["phone"], city=c["city"],
                source_channel=random.choice(list(SourceChannel)),
                date_received=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                applied_designation=c["title"], department_tag=dept,
                career_level=CareerLevel(lvl),
                employment_type=random.choice(list(EmploymentType)),
                tags=["Demo"], duplicate_check_hash=new_uuid()[:16],
            ))

            # Skills
            pool = SKILLS.get(dept, SKILLS["Engineering"])
            for sk in random.sample(pool, min(random.randint(4, 7), len(pool))):
                db.add(Skill(skill_id=new_uuid(), candidate_id=cid, skill_name=sk, jd_keyword_match=random.choice([True, False])))

            # Employment history
            for j in range(random.randint(1, 3)):
                ya = random.randint(1, 12)
                start = datetime.now() - timedelta(days=365 * (ya + random.randint(1, 3)))
                end = datetime.now() - timedelta(days=365 * ya) if j > 0 else None
                dur = f"{start.strftime('%b %Y')} - {'Present' if end is None else end.strftime('%b %Y')}"
                db.add(EmploymentHistory(
                    employment_history_id=new_uuid(), candidate_id=cid,
                    company=random.choice(COMPANIES),
                    title=random.choice(TITLES.get(dept, TITLES["Engineering"])),
                    duration=dur, description=f"Role in {dept.lower()}",
                ))

            # Score
            sv = round(random.uniform(35, 95), 2)
            conf = "High" if sv > 75 else ("Medium" if sv > 50 else "Low")
            db.add(Score(
                score_id=new_uuid(), candidate_id=cid,
                requisition_id=random.choice(req_ids),
                ranking_score=sv,
                score_breakdown_json={
                    "skill_match": round(random.uniform(30, 100), 1),
                    "experience_match": round(random.uniform(40, 100), 1),
                    "education_match": round(random.uniform(50, 100), 1),
                    "location_match": round(random.uniform(60, 100), 1),
                    "keyword_match": round(random.uniform(20, 95), 1),
                },
                score_model_version="v1.0-demo",
                confidence_flag=ConfidenceFlag(conf),
            ))

            # Sync status
            synced = sv >= 60 and conf != "Low"
            db.add(SyncStatusRecord(
                sync_id=new_uuid(), candidate_id=cid,
                sync_status=SyncStatus.synced if synced else SyncStatus.not_synced,
                sync_threshold_met=sv >= 60,
                erpnext_applicant_id=f"HR-APP-{1000+i}" if synced else None,
                synced_at=datetime.utcnow() - timedelta(days=random.randint(0, 10)) if synced else None,
            ))

        await db.commit()

        c = (await db.execute(select(func.count()).select_from(Candidate))).scalar_one()
        s = (await db.execute(select(func.count()).select_from(Score))).scalar_one()
        r = (await db.execute(select(func.count()).select_from(Requisition))).scalar_one()
        print(f"Total: {c} candidates, {s} scores, {r} requisitions")

    await engine.dispose()
    print("Demo data seeded!")


if __name__ == "__main__":
    asyncio.run(seed())
