"""
Built-in CV Parser — extracts candidate info from PDF/DOCX/TXT without any external API.

Uses regex patterns, section detection, and a curated skills dictionary.
"""
import re
from typing import Dict, Any, List, Optional, Tuple


# ─── Skills Dictionary ────────────────────────────────────────────────────────

SKILLS_DB = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php",
    "swift", "kotlin", "go", "rust", "scala", "r", "matlab", "perl", "haskell",
    "elixir", "dart", "lua", "sql", "nosql",
    # Frontend
    "react", "reactjs", "react.js", "angular", "angularjs", "vue", "vuejs", "vue.js",
    "next.js", "nextjs", "nuxt", "svelte", "html", "css", "sass", "scss", "tailwind",
    "bootstrap", "jquery", "webpack", "vite",
    # Backend
    "node.js", "nodejs", "express", "expressjs", "django", "flask", "fastapi",
    "spring", "spring boot", "laravel", "rails", "ruby on rails", "asp.net",
    "graphql", "rest", "rest api", "restful",
    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "oracle", "sqlite", "mssql", "sql server", "dynamodb", "cassandra",
    "neo4j", "firebase", "supabase", "mariadb",
    # Cloud & DevOps
    "aws", "amazon web services", "azure", "gcp", "google cloud",
    "docker", "kubernetes", "k8s", "jenkins", "ci/cd", "terraform",
    "ansible", "puppet", "vagrant", "nginx", "apache", "linux", "unix",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence",
    "prometheus", "grafana", "datadog", "splunk",
    # Data & AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "data science", "data analysis", "data engineering", "data visualization",
    "etl", "airflow", "spark", "hadoop", "kafka", "tableau", "power bi",
    "computer vision", "opencv", "transformers", "llm", "openai",
    "ai", "artificial intelligence",
    # Mobile
    "ios", "android", "flutter", "react native", "xamarin", "ionic",
    "swiftui", "jetpack compose",
    # Testing
    "selenium", "cypress", "jest", "pytest", "junit", "tdd", "bdd",
    "unit testing", "integration testing", "automation testing",
    # Design
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "ui/ux", "ux design", "ui design", "user experience", "user interface",
    # Business / Soft
    "agile", "scrum", "kanban", "pmp", "six sigma", "lean",
    "project management", "stakeholder management", "leadership",
    "communication", "problem solving", "team management",
    "strategic planning", "business development", "negotiation",
    # Finance / ERP
    "erp", "erpnext", "sap", "oracle erp", "salesforce", "hubspot",
    "quickbooks", "xero", "financial modeling", "budgeting",
    "accounting", "ifrs", "gaap", "audit", "compliance",
    # HR / Recruitment
    "recruitment", "talent acquisition", "hris", "workday", "bamboohr",
    "applicant tracking", "ats", "onboarding", "compensation",
    "employee relations", "performance management",
    # Marketing
    "seo", "sem", "ppc", "google ads", "facebook ads", "social media",
    "content marketing", "email marketing", "marketing automation",
    "hubspot", "marketo", "mailchimp", "google analytics",
    # Cybersecurity
    "cybersecurity", "penetration testing", "ethical hacking", "siem",
    "firewall", "encryption", "owasp", "iso 27001", "gdpr",
}

# ─── Section Headers ──────────────────────────────────────────────────────────

SECTION_PATTERNS = {
    "experience": [
        r"(?i)^\s*(work\s+experience|professional\s+experience|employment\s+history|experience|career\s+history|work\s+history)",
    ],
    "education": [
        r"(?i)^\s*(education|academic\s+background|qualifications|degrees|education\s+and\s+training)",
    ],
    "skills": [
        r"(?i)^\s*(skills?|technical\s+skills?|core\s+competencies|technologies|key\s+skills?|proficiencies)",
    ],
    "summary": [
        r"(?i)^\s*(summary|profile|about\s+me|objective|professional\s+summary|career\s+objective|personal\s+profile)",
    ],
    "certifications": [
        r"(?i)^\s*(certifications?|licenses?|certificates?|professional\s+development)",
    ],
    "languages": [
        r"(?i)^\s*(languages?|foreign\s+languages?)",
    ],
    "projects": [
        r"(?i)^\s*(projects?|portfolio|key\s+projects?)",
    ],
}


# ─── Parser Class ─────────────────────────────────────────────────────────────

class BuiltInCVParser:
    """Extract structured candidate data from raw CV text."""

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse CV text and return structured data."""
        text = self._clean_text(text)
        sections = self._detect_sections(text)

        return {
            "full_name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "linkedin_url": self._extract_linkedin(text),
            "city": self._extract_city(text, sections),
            "skills": self._extract_skills(text, sections),
            "employment_history": self._extract_employment(text, sections),
            "education": self._extract_education(text, sections),
            "career_level": self._guess_career_level(text, sections),
            "department_tag": self._guess_department(text, sections),
            "applied_designation": self._extract_designation(text, sections),
            "tags": self._extract_tags(text, sections),
        }

    # ─── Text Cleaning ────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        # Normalize whitespace
        text = re.sub(r'\r\n', '\n', text)
        text = re.sub(r'[\t ]+', ' ', text)
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    # ─── Section Detection ────────────────────────────────────────────────

    def _detect_sections(self, text: str) -> Dict[str, Tuple[int, str]]:
        """Detect sections and return {section_name: (start_pos, section_text)}."""
        lines = text.split('\n')
        sections = {}
        current_section = None
        current_start = 0
        current_lines = []

        for i, line in enumerate(lines):
            matched = False
            for section_name, patterns in SECTION_PATTERNS.items():
                for pattern in patterns:
                    if re.match(pattern, line.strip()):
                        # Save previous section
                        if current_section:
                            sections[current_section] = (current_start, '\n'.join(current_lines))
                        current_section = section_name
                        current_start = i
                        current_lines = []
                        matched = True
                        break
                if matched:
                    break
            if not matched and current_section:
                current_lines.append(line)

        if current_section:
            sections[current_section] = (current_start, '\n'.join(current_lines))

        return sections

    def _get_section_text(self, sections: Dict, name: str) -> str:
        if name in sections:
            return sections[name][1]
        return ""

    # ─── Name Extraction ──────────────────────────────────────────────────

    def _extract_name(self, text: str) -> str:
        """Extract candidate name — usually first non-empty line."""
        lines = text.split('\n')
        for line in lines[:15]:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            # Skip lines that look like headers/sections
            if re.match(r'(?i)^(curriculum vitae|resume|cv|contact|phone|email|address|linkedin)', line):
                continue
            if '@' in line or re.match(r'^\+?\d', line):
                continue
            # Name pattern: 2-4 words, each capitalized, no digits
            name_match = re.match(r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,3})$', line)
            if name_match:
                return name_match.group(1).strip()
            # Fallback: first meaningful line
            if len(line.split()) >= 2 and len(line) <= 60:
                # Clean it
                cleaned = re.sub(r'[^a-zA-Z\s\-\']', '', line).strip()
                if cleaned and len(cleaned.split()) >= 2:
                    return cleaned
        return "Unknown"

    # ─── Email Extraction ─────────────────────────────────────────────────

    def _extract_email(self, text: str) -> Optional[str]:
        pattern = r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text)
        return match.group(0).lower() if match else None

    # ─── Phone Extraction ─────────────────────────────────────────────────

    def _extract_phone(self, text: str) -> Optional[str]:
        # International patterns
        patterns = [
            r'(?:\+971|00971|971)\s*\d{2,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',  # UAE
            r'(?:\+966|00966|966)\s*\d{1,2}[\s\-]?\d{3,4}[\s\-]?\d{4}',    # Saudi
            r'(?:\+973|00973|973)\s*\d{4}[\s\-]?\d{4}',                      # Bahrain
            r'(?:\+974|00974|974)\s*\d{4}[\s\-]?\d{4}',                      # Qatar
            r'(?:\+968|00968|968)\s*\d{4}[\s\-]?\d{4}',                      # Oman
            r'(?:\+20|0020|20)\s*\d{10}',                                      # Egypt
            r'(?:\+44|0044)\s*\d{10}',                                         # UK
            r'(?:\+1|001)\s*\d{10}',                                           # US
            r'(?:\+\d{1,3}|00\d{1,3})\s*\d{6,14}',                           # Generic international
            r'0\d{2,3}[\s\-]?\d{3,4}[\s\-]?\d{3,4}',                         # Local formats
            r'\d{3,4}[\s\-]\d{3,4}[\s\-]\d{3,4}',                            # Generic
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group(0).strip()
        return None

    # ─── LinkedIn Extraction ──────────────────────────────────────────────

    def _extract_linkedin(self, text: str) -> Optional[str]:
        pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9\-_%]+/?'
        match = re.search(pattern, text)
        if match:
            url = match.group(0)
            if not url.startswith('http'):
                url = 'https://www.' + url
            return url
        return None

    # ─── City / Location Extraction ───────────────────────────────────────

    def _extract_city(self, text: str, sections: Dict) -> Optional[str]:
        """Try to extract city from header or location fields."""
        header = '\n'.join(text.split('\n')[:10])
        # Common Gulf/MENA cities
        cities = [
            "Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah",
            "Fujairah", "Umm Al Quwain", "Al Ain",
            "Riyadh", "Jeddah", "Dammam", "Mecca", "Medina",
            "Manama", "Riffa", "Muharraq",
            "Doha", "Al Wakrah",
            "Muscat", "Salalah",
            "Kuwait City", "Hawalli",
            "Cairo", "Alexandria",
            "Amman", "Zarqa",
            "Beirut", "Tripoli",
            "London", "Manchester", "Birmingham",
            "New York", "San Francisco", "Los Angeles", "Chicago",
            "Toronto", "Vancouver",
            "Singapore", "Hong Kong",
            "Bangalore", "Mumbai", "Delhi", "Hyderabad",
            "Karachi", "Lahore", "Islamabad",
        ]
        # Check header first
        for city in cities:
            if re.search(r'\b' + re.escape(city) + r'\b', header, re.IGNORECASE):
                return city
        # Check "Location:" or "Address:" lines
        loc_match = re.search(r'(?i)(?:location|address|city|based in)\s*[:;]?\s*(.+)', text[:500])
        if loc_match:
            candidate = loc_match.group(1).strip()[:50]
            for city in cities:
                if re.search(r'\b' + re.escape(city) + r'\b', candidate, re.IGNORECASE):
                    return city
            # Return whatever was after "Location:" if it's short
            if len(candidate.split()) <= 4:
                return candidate
        return None

    # ─── Skills Extraction ────────────────────────────────────────────────

    def _extract_skills(self, text: str, sections: Dict) -> List[str]:
        """Extract skills from the skills section + entire text."""
        found = set()

        # Primary: skills section
        skills_text = self._get_section_text(sections, "skills")
        if skills_text:
            for skill in SKILLS_DB:
                if re.search(r'\b' + re.escape(skill) + r'\b', skills_text, re.IGNORECASE):
                    found.add(skill.title())

        # Secondary: scan full text if not enough from section
        if len(found) < 3:
            for skill in SKILLS_DB:
                if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
                    found.add(skill.title())

        # Deduplicate and sort
        result = sorted(set(s.title() for s in found))
        return result

    # ─── Employment History Extraction ────────────────────────────────────

    def _extract_employment(self, text: str, sections: Dict) -> List[Dict]:
        """Extract work history entries."""
        exp_text = self._get_section_text(sections, "experience")
        if not exp_text:
            # Try to find it in the full text
            exp_text = text

        entries = []
        lines = exp_text.split('\n')

        current_entry = None
        # Date patterns
        date_pattern = r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s.]?\s*\d{4}|\d{4})\s*[-–—to]+\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s.]?\s*\d{4}|\d{4}|[Pp]resent|[Cc]urrent|Now)'
        company_title_pattern = r'(?:(.+?)\s*[-–—|,]\s*(.+?))?\s*$'

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry and current_entry.get("title"):
                    entries.append(current_entry)
                    current_entry = None
                continue

            # Check if this line contains a date range
            date_match = re.search(date_pattern, line, re.IGNORECASE)

            if date_match:
                if current_entry and current_entry.get("title"):
                    entries.append(current_entry)

                duration = date_match.group(0)
                before_date = line[:date_match.start()].strip()
                before_date = re.sub(r'[-–—|,]+$', '', before_date).strip()

                # Try to split "Title | Company" or "Title at Company" etc.
                title = ""
                company = ""
                if ' | ' in before_date:
                    parts = [p.strip() for p in before_date.split(' | ') if p.strip()]
                    if len(parts) >= 2:
                        title = parts[0]
                        company = parts[1]
                    else:
                        title = parts[0] if parts else before_date
                elif ' at ' in before_date:
                    parts = before_date.rsplit(' at ', 1)
                    title = parts[0].strip()
                    company = parts[1].strip()
                elif ' - ' in before_date or ' \u2013 ' in before_date:
                    sep = ' - ' if ' - ' in before_date else ' \u2013 '
                    parts = before_date.split(sep, 1)
                    company = parts[0].strip()
                    title = parts[1].strip() if len(parts) > 1 else ""
                else:
                    title = before_date

                current_entry = {
                    "company": company,
                    "title": title,
                    "duration": duration,
                    "description": "",
                }
            elif current_entry:
                # Accumulate description
                if current_entry.get("description"):
                    current_entry["description"] += " " + line
                else:
                    current_entry["description"] = line
                # If no title yet, try to extract from first description line
                if not current_entry.get("title") and len(line.split()) >= 2 and len(line) < 80:
                    current_entry["title"] = line

        if current_entry and current_entry.get("title"):
            entries.append(current_entry)

        # Limit to most recent 10
        return entries[:10]

    # ─── Education Extraction ─────────────────────────────────────────────

    def _extract_education(self, text: str, sections: Dict) -> str:
        """Extract education as a text summary."""
        edu_text = self._get_section_text(sections, "education")
        if not edu_text:
            # Try pattern matching
            edu_match = re.search(r'(?i)(education[\s\S]*?)(?:skills|experience|certifications|references|$)', text, re.DOTALL)
            if edu_match:
                edu_text = edu_match.group(1)

        if not edu_text:
            return ""

        # Clean up
        lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
        # Take first 5 lines of education section
        return '\n'.join(lines[:5])

    # ─── Career Level Inference ───────────────────────────────────────────

    def _guess_career_level(self, text: str, sections: Dict) -> str:
        """Guess career level from title/keywords."""
        lower_text = text.lower()

        # Check for explicit levels
        level_signals = {
            "Managerial": ["director", "vp", "vice president", "chief", "c-level", "head of", "general manager", "managing director", "ceo", "cto", "cfo", "coo"],
            "Lead": ["lead", "principal", "staff", "architect", "tech lead", "team lead", "group manager"],
            "Senior": ["senior", "sr.", "sr ", "lead", "principal", "head"],
            "Mid": ["mid-level", "intermediate", "specialist", "consultant", "analyst"],
            "Entry": ["junior", "jr.", "jr ", "intern", "trainee", "graduate", "entry level", "associate", "assistant"],
        }

        # Check title specifically
        exp_text = self._get_section_text(sections, "experience")
        titles = []
        for line in (exp_text or lower_text).split('\n')[:10]:
            titles.append(line.lower())

        for level, keywords in level_signals.items():
            for kw in keywords:
                for t in titles:
                    if kw in t:
                        return level

        # Fallback: count years of experience
        year_pattern = r'(\d{4})\s*[-–—to]+\s*(\d{4}|present|current)'
        years = re.findall(year_pattern, lower_text, re.IGNORECASE)
        if years:
            try:
                start_year = int(years[0][0])
                total_years = 2026 - start_year
                if total_years >= 12:
                    return "Senior"
                elif total_years >= 5:
                    return "Mid"
                else:
                    return "Entry"
            except ValueError:
                pass

        return "Mid"

    # ─── Department Guessing ──────────────────────────────────────────────

    def _guess_department(self, text: str, sections: Dict) -> str:
        """Guess department from skills and context."""
        lower_text = text.lower()
        dept_keywords = {
            "Engineering": ["developer", "engineer", "software", "programming", "full stack", "backend", "frontend", "devops", "sre"],
            "IT": ["it ", "infrastructure", "sysadmin", "network", "helpdesk", "support engineer"],
            "Marketing": ["marketing", "digital marketing", "seo", "content", "social media", "brand"],
            "Sales": ["sales", "business development", "account manager", "revenue"],
            "Finance": ["finance", "accounting", "financial", "audit", "treasury", "controller"],
            "HR": ["human resources", "recruitment", "talent", "people operations", "hr "],
            "Operations": ["operations", "supply chain", "logistics", "procurement"],
        }
        scores = {}
        for dept, kws in dept_keywords.items():
            count = sum(1 for kw in kws if kw in lower_text)
            if count > 0:
                scores[dept] = count
        if scores:
            return max(scores, key=scores.get)
        return "Other"

    # ─── Designation Extraction ───────────────────────────────────────────

    def _extract_designation(self, text: str, sections: Dict) -> Optional[str]:
        """Extract job title / designation from most recent experience."""
        exp_text = self._get_section_text(sections, "experience")
        if not exp_text:
            exp_text = text

        lines = exp_text.split('\n')
        date_pattern = r'(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s.]?\s*\d{4}|\d{4})\s*[-–—to]+\s*(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*[\s.]?\s*\d{4}|\d{4}|[Pp]resent|[Cc]urrent|Now)'

        for line in lines[:15]:
            line = line.strip()
            if not line:
                continue
            if re.search(date_pattern, line, re.IGNORECASE):
                # This line has a date — extract the title part
                before_date = re.split(date_pattern, line, flags=re.IGNORECASE)[0].strip()
                before_date = re.sub(r'[-–—|,]+$', '', before_date).strip()
                # Handle "Title | Company" format — take first segment as title
                if ' | ' in before_date:
                    parts = [p.strip() for p in before_date.split(' | ') if p.strip()]
                    return parts[0] if parts else before_date
                if ' at ' in before_date:
                    return before_date.rsplit(' at ', 1)[0].strip()
                elif ' - ' in before_date:
                    parts = before_date.split(' - ', 1)
                    return parts[1].strip() if len(parts) > 1 and parts[1].strip() else parts[0].strip()
                elif before_date:
                    return before_date

        # Fallback: look for title-like lines near the top
        for line in lines[:5]:
            line = line.strip()
            if line and not re.search(r'(?i)^(experience|work|professional|employment)', line):
                if len(line.split()) <= 6 and len(line) < 60:
                    return line
        return None

    # ─── Tags Extraction ──────────────────────────────────────────────────

    def _extract_tags(self, text: str, sections: Dict) -> List[str]:
        """Extract relevant tags from the CV."""
        tags = set()
        lower = text.lower()

        # Industry tags
        industries = {
            "Banking": ["bank", "banking", "financial services", "fintech"],
            "Healthcare": ["health", "hospital", "medical", "pharma"],
            "Oil & Gas": ["oil", "gas", "petroleum", "energy"],
            "Real Estate": ["real estate", "property", "construction"],
            "E-commerce": ["ecommerce", "e-commerce", "marketplace", "retail"],
            "Telecom": ["telecom", "telecommunications"],
            "Consulting": ["consulting", "advisory"],
            "Government": ["government", "public sector", "municipality"],
            "Education": ["education", "university", "school", "training"],
        }
        for tag, keywords in industries.items():
            if any(kw in lower for kw in keywords):
                tags.add(tag)

        # Employment type tags
        if "remote" in lower or "work from home" in lower or "wfh" in lower:
            tags.add("Remote")
        if "contract" in lower or "freelance" in lower or "consultant" in lower:
            tags.add("Contract")

        return sorted(tags)[:10]
