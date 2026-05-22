import * as cheerio from "cheerio";
import type { JobResult } from "./types";
import { fetchHtml } from "./http";

const ROLE_PATTERNS: Record<string, RegExp[]> = {
  "AI Engineer": [/ai engineer/i, /artificial intelligence engineer/i],
  "ML Engineer": [/ml engineer/i, /machine learning engineer/i],
  "Data Scientist": [/data scientist/i],
  "Data Analyst": [/data analyst/i],
};

function scoreTitle(title: string, roles: string[]): number {
  let score = 0;
  for (const role of roles) {
    const patterns = ROLE_PATTERNS[role] ?? [new RegExp(role, "i")];
    if (patterns.some((p) => p.test(title))) score += 10;
  }
  if (/engineer|scientist|analyst|machine learning|ml|ai/i.test(title))
    score += 2;
  return score;
}

export async function fetchJobs(
  careersUrl: string,
  targetRoles: string[],
): Promise<JobResult[]> {
  const html = await fetchHtml(careersUrl);
  if (!html) return [];

  const $ = cheerio.load(html);
  const base = new URL(careersUrl);
  const seen = new Set<string>();
  const jobs: JobResult[] = [];

  $("a[href]").each((_, el) => {
    const href = $(el).attr("href");
    const title = $(el).text().replace(/\s+/g, " ").trim();
    if (!href || title.length < 8 || title.length > 120) return;

    let url: string;
    try {
      url = new URL(href, base).toString();
    } catch {
      return;
    }

    if (seen.has(url)) return;
    const score = scoreTitle(title, targetRoles);
    if (score < 8) return;

    seen.add(url);
    jobs.push({
      title,
      url,
      location: null,
      snippet: null,
      matchScore: score,
    });
  });

  return jobs.sort((a, b) => b.matchScore - a.matchScore).slice(0, 15);
}
