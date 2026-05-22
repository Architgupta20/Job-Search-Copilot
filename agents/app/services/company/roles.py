"""Target job profiles and title-matching patterns."""

import re

PEOPLE_PER_ROLE = 10

# Tech & data
TECH_ROLES = [
    "AI Engineer",
    "ML Engineer",
    "GenAI Engineer",
    "LLM Engineer",
    "Data Scientist",
    "Applied Scientist",
    "Research Scientist",
    "Data Engineer",
    "MLOps Engineer",
    "Data Analyst",
    "Analytics Engineer",
    "Software Engineer",
    "Backend Engineer",
    "Full Stack Engineer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Platform Engineer",
    "Solutions Architect",
    "UX Designer",
    "Product Designer",
]

# Product & program
PRODUCT_ROLES = [
    "Product Manager",
    "Technical Program Manager",
    "Project Manager",
    "Program Manager",
]

# Engineering leadership
LEADERSHIP_ROLES = [
    "Engineering Manager",
    "Director of Engineering",
    "VP Engineering",
    "CTO",
]

# Non-tech / business
NON_TECH_ROLES = [
    "HR Manager",
    "Recruiter",
    "Talent Acquisition",
    "Marketing Manager",
    "Growth Marketing",
    "Sales Manager",
    "Account Executive",
    "Business Development",
    "Customer Success Manager",
    "Operations Manager",
    "Finance Manager",
    "Financial Analyst",
    "Business Analyst",
    "Management Consultant",
    "Legal Counsel",
    "Office Manager",
    "Executive Assistant",
    "Supply Chain Manager",
    "Content Manager",
    "Communications Manager",
    "Quantitative Analyst",
]

TARGET_ROLES: list[str] = TECH_ROLES + PRODUCT_ROLES + LEADERSHIP_ROLES + NON_TECH_ROLES

ROLE_PATTERNS: dict[str, re.Pattern[str]] = {
    # Tech
    "AI Engineer": re.compile(r"ai engineer|artificial intelligence engineer", re.I),
    "ML Engineer": re.compile(r"ml engineer|machine learning engineer", re.I),
    "GenAI Engineer": re.compile(r"gen\s*ai|generative ai engineer|genai engineer", re.I),
    "LLM Engineer": re.compile(r"llm engineer|large language model", re.I),
    "Data Scientist": re.compile(r"data scientist", re.I),
    "Applied Scientist": re.compile(r"applied scientist", re.I),
    "Research Scientist": re.compile(r"research scientist", re.I),
    "Data Engineer": re.compile(r"data engineer", re.I),
    "MLOps Engineer": re.compile(r"mlops|ml ops", re.I),
    "Data Analyst": re.compile(r"data analyst", re.I),
    "Analytics Engineer": re.compile(r"analytics engineer", re.I),
    "Software Engineer": re.compile(r"software engineer|software developer", re.I),
    "Backend Engineer": re.compile(r"backend engineer|back-end engineer", re.I),
    "Full Stack Engineer": re.compile(r"full[\s-]?stack engineer|full[\s-]?stack developer", re.I),
    "DevOps Engineer": re.compile(r"devops|site reliability engineer|\bsre\b", re.I),
    "Cloud Engineer": re.compile(r"cloud engineer", re.I),
    "Platform Engineer": re.compile(r"platform engineer", re.I),
    "Solutions Architect": re.compile(r"solutions architect", re.I),
    "UX Designer": re.compile(r"ux designer|user experience designer", re.I),
    "Product Designer": re.compile(r"product designer", re.I),
    # Product
    "Product Manager": re.compile(r"product manager|\bpm\b", re.I),
    "Technical Program Manager": re.compile(r"technical program manager|\btpm\b", re.I),
    "Project Manager": re.compile(r"project manager", re.I),
    "Program Manager": re.compile(r"program manager", re.I),
    # Leadership
    "Engineering Manager": re.compile(r"engineering manager", re.I),
    "Director of Engineering": re.compile(r"director of engineering|engineering director", re.I),
    "VP Engineering": re.compile(r"vp[, ]+engineering|vice president[, ]+engineering", re.I),
    "CTO": re.compile(r"\bcto\b|chief technology officer", re.I),
    # Non-tech
    "HR Manager": re.compile(r"hr manager|human resources manager|people operations", re.I),
    "Recruiter": re.compile(r"recruiter|technical recruiter|corporate recruiter", re.I),
    "Talent Acquisition": re.compile(r"talent acquisition|talent partner", re.I),
    "Marketing Manager": re.compile(r"marketing manager|brand manager", re.I),
    "Growth Marketing": re.compile(r"growth marketing|growth manager|demand generation", re.I),
    "Sales Manager": re.compile(r"sales manager|sales director", re.I),
    "Account Executive": re.compile(r"account executive|\bae\b", re.I),
    "Business Development": re.compile(r"business development|bd manager|\bbdr\b", re.I),
    "Customer Success Manager": re.compile(r"customer success|client success", re.I),
    "Operations Manager": re.compile(r"operations manager|business operations", re.I),
    "Finance Manager": re.compile(r"finance manager|financial planning", re.I),
    "Financial Analyst": re.compile(r"financial analyst", re.I),
    "Business Analyst": re.compile(r"business analyst", re.I),
    "Management Consultant": re.compile(r"management consultant|strategy consultant", re.I),
    "Legal Counsel": re.compile(r"legal counsel|corporate counsel|attorney", re.I),
    "Office Manager": re.compile(r"office manager|facilities manager", re.I),
    "Executive Assistant": re.compile(r"executive assistant|administrative assistant", re.I),
    "Supply Chain Manager": re.compile(r"supply chain|logistics manager", re.I),
    "Content Manager": re.compile(r"content manager|content strategist", re.I),
    "Communications Manager": re.compile(r"communications manager|public relations", re.I),
    "Quantitative Analyst": re.compile(r"quantitative analyst|quant researcher", re.I),
}

# Titles accepted when user picks a role (includes close equivalents + senior variants)
ROLE_EQUIVALENTS: dict[str, list[str]] = {
    "AI Engineer": [
        "AI Engineer",
        "ML Engineer",
        "GenAI Engineer",
        "LLM Engineer",
        "Applied Scientist",
        "Research Scientist",
    ],
    "ML Engineer": ["ML Engineer", "AI Engineer", "MLOps Engineer", "Applied Scientist"],
    "GenAI Engineer": ["GenAI Engineer", "AI Engineer", "LLM Engineer", "ML Engineer"],
    "LLM Engineer": ["LLM Engineer", "AI Engineer", "GenAI Engineer", "ML Engineer"],
    "Data Scientist": ["Data Scientist", "Applied Scientist", "Research Scientist", "ML Engineer"],
    "Applied Scientist": ["Applied Scientist", "Research Scientist", "Data Scientist", "AI Engineer"],
    "Research Scientist": ["Research Scientist", "Applied Scientist", "Data Scientist"],
    "Data Engineer": ["Data Engineer", "Analytics Engineer", "ML Engineer"],
    "MLOps Engineer": ["MLOps Engineer", "ML Engineer", "Data Engineer", "DevOps Engineer"],
    "Software Engineer": ["Software Engineer", "Backend Engineer", "Full Stack Engineer"],
    "Backend Engineer": ["Backend Engineer", "Software Engineer", "Platform Engineer"],
    "Full Stack Engineer": ["Full Stack Engineer", "Software Engineer", "Backend Engineer"],
    "DevOps Engineer": ["DevOps Engineer", "Cloud Engineer", "Platform Engineer", "MLOps Engineer"],
    "Cloud Engineer": ["Cloud Engineer", "DevOps Engineer", "Platform Engineer"],
    "Platform Engineer": ["Platform Engineer", "DevOps Engineer", "Cloud Engineer", "Backend Engineer"],
    "Product Manager": ["Product Manager", "Technical Program Manager"],
    "Technical Program Manager": ["Technical Program Manager", "Program Manager", "Project Manager"],
    "Engineering Manager": ["Engineering Manager", "Director of Engineering"],
    "Director of Engineering": ["Director of Engineering", "VP Engineering", "Engineering Manager"],
    "VP Engineering": ["VP Engineering", "Director of Engineering", "CTO"],
    "Recruiter": ["Recruiter", "Talent Acquisition"],
    "Talent Acquisition": ["Talent Acquisition", "Recruiter"],
}

SENIOR_TITLE_BOOST = re.compile(
    r"chief|cto|ceo|founder|co-?founder|"
    r"vice president|\bvp\b|"
    r"director|head of|"
    r"principal|distinguished|fellow|"
    r"staff|lead|manager|"
    r"senior|\bsr\.?\b",
    re.I,
)

ROLE_SENIOR_QUERY: dict[str, str] = {
    "AI Engineer": "Head of AI OR Director of AI OR Principal AI OR VP AI",
    "ML Engineer": "Head of Machine Learning OR Director ML OR Principal ML",
    "Data Scientist": "Head of Data Science OR Director Data Science",
    "Software Engineer": "Director of Engineering OR Engineering Director OR VP Engineering",
    "Product Manager": "Director of Product OR VP Product OR Head of Product",
}


def equivalent_roles_for(selected: str) -> list[str]:
    return ROLE_EQUIVALENTS.get(selected, [selected])


def title_matches_role(job_title: str, selected_role: str) -> bool:
    """True if LinkedIn job title matches selected role or an equivalent."""
    blob = job_title or ""
    for equiv in equivalent_roles_for(selected_role):
        pat = ROLE_PATTERNS.get(equiv)
        if pat and pat.search(blob):
            return True
    blob_l = blob.lower()
    if selected_role == "AI Engineer" and re.search(
        r"head of ai|director of ai|vp[, ]+ai|chief ai|ai (lead|architect)|principal ai",
        blob_l,
    ):
        return True
    if selected_role in ("ML Engineer", "GenAI Engineer", "LLM Engineer") and re.search(
        r"head of (ml|machine learning|ai)|director of (ml|machine learning|ai)",
        blob_l,
    ):
        return True
    pat = ROLE_PATTERNS.get(selected_role)
    return bool(pat and pat.search(blob))


def seniority_score(job_title: str) -> int:
    t = (job_title or "").lower()
    if re.search(r"\b(ceo|cto|cfo|chief)\b", t):
        return 100
    if re.search(r"\bvp\b|vice president", t):
        return 90
    if "director" in t:
        return 85
    if "head of" in t:
        return 80
    if "principal" in t or "distinguished" in t or "fellow" in t:
        return 70
    if re.search(r"\bstaff\b", t):
        return 65
    if re.search(r"\blead\b", t) or "manager" in t:
        return 55
    if "senior" in t or re.search(r"\bsr\.?\b", t):
        return 45
    return 25


ROLE_LINKEDIN_TITLES: dict[str, str] = {
    "AI Engineer": (
        '"AI Engineer" OR "Machine Learning Engineer" OR "ML Engineer" OR '
        '"GenAI" OR "LLM Engineer" OR "Head of AI" OR "Director of AI" OR "Principal AI"'
    ),
    "ML Engineer": "ML Engineer OR Machine Learning Engineer",
    "GenAI Engineer": "GenAI Engineer OR Generative AI",
    "LLM Engineer": "LLM Engineer",
    "Data Scientist": "Data Scientist",
    "Applied Scientist": "Applied Scientist",
    "Research Scientist": "Research Scientist",
    "Data Engineer": "Data Engineer",
    "MLOps Engineer": "MLOps Engineer",
    "Data Analyst": "Data Analyst",
    "Analytics Engineer": "Analytics Engineer",
    "Software Engineer": "Software Engineer",
    "Backend Engineer": "Backend Engineer",
    "Full Stack Engineer": "Full Stack Engineer",
    "DevOps Engineer": "DevOps Engineer OR SRE",
    "Cloud Engineer": "Cloud Engineer",
    "Platform Engineer": "Platform Engineer",
    "Solutions Architect": "Solutions Architect",
    "UX Designer": "UX Designer",
    "Product Designer": "Product Designer",
    "Product Manager": "Product Manager",
    "Technical Program Manager": "Technical Program Manager OR TPM",
    "Project Manager": "Project Manager",
    "Program Manager": "Program Manager",
    "Engineering Manager": "Engineering Manager",
    "Director of Engineering": "Director of Engineering",
    "VP Engineering": "VP Engineering",
    "CTO": "CTO OR Chief Technology Officer",
    "HR Manager": "HR Manager OR Human Resources",
    "Recruiter": "Recruiter OR Technical Recruiter",
    "Talent Acquisition": "Talent Acquisition",
    "Marketing Manager": "Marketing Manager",
    "Growth Marketing": "Growth Marketing",
    "Sales Manager": "Sales Manager",
    "Account Executive": "Account Executive",
    "Business Development": "Business Development",
    "Customer Success Manager": "Customer Success Manager",
    "Operations Manager": "Operations Manager",
    "Finance Manager": "Finance Manager",
    "Financial Analyst": "Financial Analyst",
    "Business Analyst": "Business Analyst",
    "Management Consultant": "Management Consultant",
    "Legal Counsel": "Legal Counsel",
    "Office Manager": "Office Manager",
    "Executive Assistant": "Executive Assistant",
    "Supply Chain Manager": "Supply Chain",
    "Content Manager": "Content Manager",
    "Communications Manager": "Communications OR PR Manager",
    "Quantitative Analyst": "Quantitative Analyst",
}

ROLE_GROUPS: dict[str, list[str]] = {
    "Tech & data": TECH_ROLES,
    "Product & program": PRODUCT_ROLES,
    "Leadership": LEADERSHIP_ROLES,
    "Business & non-tech": NON_TECH_ROLES,
}
