/** Titles to exclude from cold-outreach people list (junior ICs). */
const EXCLUDED_TITLE =
  /\b(SDE\s*1|SDE1|SD1|SD-1|SDE\s*-?\s*I\b|SDE\s*II|software engineer\s*i\b|software engineer\s*1\b|junior|intern|internship|entry[- ]?level|graduate|new grad|associate\s+(ai|ml|machine learning|software|data)\s+engineer)\b/i;

/** Junior AI/ML IC titles without seniority (e.g. "AI Engineer" at L3). */
const JUNIOR_IC_AI =
  /\b((?<!lead\s)(?<!senior\s)(?<!staff\s)(?<!principal\s)(?<!director\s)ai engineer|(?<!lead\s)ml engineer|machine learning engineer|data scientist i\b|data analyst i\b)\b/i;

/** Senior / hiring contacts we want for cold email. */
export const SENIOR_OUTREACH_TITLE =
  /\b(CEO|CTO|COO|CFO|founder|co-founder|president|chief|VP|vice president|svp|evp|director|head of|lead|principal|staff|program manager|engineering manager|hiring manager|recruiter|talent acquisition|talent partner|people partner|HRBP)\b/i;

export function isExcludedOutreachTitle(title: string): boolean {
  const t = title.trim();
  if (!t) return true;
  if (EXCLUDED_TITLE.test(t)) return true;
  if (JUNIOR_IC_AI.test(t) && !SENIOR_OUTREACH_TITLE.test(t)) return true;
  return false;
}

export function seniorOutreachScore(title: string): number {
  const t = title.toLowerCase();
  let score = 0;
  if (/\bceo\b|chief executive/.test(t)) score += 20;
  if (/\bcto\b|chief technology/.test(t)) score += 18;
  if (/\bvp\b|vice president|svp|evp/.test(t)) score += 16;
  if (/director|head of/.test(t)) score += 14;
  if (/lead|principal|staff/.test(t)) score += 12;
  if (/program manager/.test(t)) score += 11;
  if (/engineering manager|hiring manager/.test(t)) score += 10;
  if (/recruiter|talent/.test(t)) score += 8;
  if (SENIOR_OUTREACH_TITLE.test(t)) score += 5;
  return score;
}

/** LinkedIn search query — leadership & hiring, not junior engineers. */
export const PEOPLE_LINKEDIN_QUERY =
  '("Lead AI Engineer" OR "Lead Machine Learning" OR "Program Manager" OR CEO OR "Head of AI" OR "Head of Machine Learning" OR "Director of Engineering" OR "Engineering Manager" OR "VP Engineering" OR "Technical Recruiter" OR "Talent Acquisition")';

export function filterAndRankPeople<T extends { title: string }>(
  people: T[],
  limit = 10,
): T[] {
  return people
    .filter((p) => !isExcludedOutreachTitle(p.title))
    .sort((a, b) => seniorOutreachScore(b.title) - seniorOutreachScore(a.title))
    .slice(0, limit);
}
