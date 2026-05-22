/** Keep in sync with agents/app/services/company/roles.py */

export const PEOPLE_PER_ROLE = 10;

export const TARGET_ROLES = [
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
] as const;

export type TargetRole = (typeof TARGET_ROLES)[number];
