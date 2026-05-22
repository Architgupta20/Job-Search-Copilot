"""Target job profiles and title-matching patterns."""

import re

# Each selected role returns up to PEOPLE_PER_ROLE LinkedIn results
PEOPLE_PER_ROLE = 10

TARGET_ROLES: list[str] = [
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
    "Product Manager",
    "Technical Program Manager",
    "Engineering Manager",
    "Business Analyst",
    "Quantitative Analyst",
]

ROLE_PATTERNS: dict[str, re.Pattern[str]] = {
    "AI Engineer": re.compile(
        r"ai engineer|artificial intelligence engineer|ai/ml",
        re.I,
    ),
    "ML Engineer": re.compile(
        r"ml engineer|machine learning engineer|deep learning engineer",
        re.I,
    ),
    "GenAI Engineer": re.compile(
        r"gen\s*ai|generative ai engineer|genai",
        re.I,
    ),
    "LLM Engineer": re.compile(r"llm engineer|large language model", re.I),
    "Data Scientist": re.compile(r"data scientist|applied scientist", re.I),
    "Applied Scientist": re.compile(r"applied scientist|research scientist", re.I),
    "Research Scientist": re.compile(r"research scientist|research engineer", re.I),
    "Data Engineer": re.compile(r"data engineer|etl engineer|analytics engineer", re.I),
    "MLOps Engineer": re.compile(r"mlops|ml ops|machine learning operations", re.I),
    "Data Analyst": re.compile(r"data analyst|business intelligence", re.I),
    "Analytics Engineer": re.compile(r"analytics engineer", re.I),
    "Software Engineer": re.compile(
        r"software engineer|swe\b|developer(?! relations)",
        re.I,
    ),
    "Backend Engineer": re.compile(r"backend engineer|back-end engineer", re.I),
    "Full Stack Engineer": re.compile(r"full[\s-]?stack", re.I),
    "DevOps Engineer": re.compile(r"devops|site reliability|sre\b", re.I),
    "Cloud Engineer": re.compile(r"cloud engineer|infrastructure engineer", re.I),
    "Platform Engineer": re.compile(r"platform engineer", re.I),
    "Solutions Architect": re.compile(r"solutions architect|cloud architect", re.I),
    "Product Manager": re.compile(r"product manager|product owner", re.I),
    "Technical Program Manager": re.compile(
        r"technical program manager|tpm\b|program manager",
        re.I,
    ),
    "Engineering Manager": re.compile(
        r"engineering manager|director of engineering",
        re.I,
    ),
    "Business Analyst": re.compile(r"business analyst", re.I),
    "Quantitative Analyst": re.compile(r"quantitative|quant analyst", re.I),
}

# LinkedIn search titles per role (senior IC + leadership for outreach)
ROLE_LINKEDIN_TITLES: dict[str, str] = {
    "AI Engineer": "AI Engineer OR Machine Learning Engineer OR Head of AI",
    "ML Engineer": "ML Engineer OR Machine Learning Engineer",
    "GenAI Engineer": "GenAI Engineer OR Generative AI",
    "LLM Engineer": "LLM Engineer OR Large Language Model",
    "Data Scientist": "Data Scientist OR Lead Data Scientist",
    "Applied Scientist": "Applied Scientist OR Research Scientist",
    "Research Scientist": "Research Scientist OR Research Engineer",
    "Data Engineer": "Data Engineer OR Lead Data Engineer",
    "MLOps Engineer": "MLOps Engineer OR ML Infrastructure",
    "Data Analyst": "Data Analyst OR Analytics Lead",
    "Analytics Engineer": "Analytics Engineer",
    "Software Engineer": "Software Engineer OR Engineering Manager",
    "Backend Engineer": "Backend Engineer OR Staff Engineer",
    "Full Stack Engineer": "Full Stack Engineer",
    "DevOps Engineer": "DevOps Engineer OR SRE",
    "Cloud Engineer": "Cloud Engineer OR Infrastructure",
    "Platform Engineer": "Platform Engineer",
    "Solutions Architect": "Solutions Architect OR Principal Architect",
    "Product Manager": "Product Manager OR Director of Product",
    "Technical Program Manager": "Technical Program Manager OR TPM",
    "Engineering Manager": "Engineering Manager OR Director Engineering",
    "Business Analyst": "Business Analyst OR Senior Business Analyst",
    "Quantitative Analyst": "Quantitative Analyst OR Quant Researcher",
}
