/** Keep in sync with agents/app/services/company/roles.py */

export const PEOPLE_PER_ROLE = 10;

export const ROLE_GROUPS = {
  "Tech & data": [
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
  ],
  "Product & program": [
    "Product Manager",
    "Technical Program Manager",
    "Project Manager",
    "Program Manager",
  ],
  Leadership: [
    "Engineering Manager",
    "Director of Engineering",
    "VP Engineering",
    "CTO",
  ],
  "Business & non-tech": [
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
  ],
} as const;

export const TARGET_ROLES = Object.values(ROLE_GROUPS).flat();

export type TargetRole = (typeof TARGET_ROLES)[number];
