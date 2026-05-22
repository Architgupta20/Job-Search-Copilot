import * as cheerio from "cheerio";
import type { CompanyInfo } from "./types";
import { fetchHtml } from "./http";

function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "")
    .trim();
}

function domainCandidates(companyName: string): string[] {
  const slug = slugify(companyName);
  const words = companyName
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "")
    .split(/\s+/)
    .filter(Boolean);
  const firstWord = words[0] ?? slug;

  const bases = new Set([
    slug,
    firstWord,
    words.join(""),
    words.slice(0, 2).join(""),
  ]);

  const hosts: string[] = [];
  for (const base of bases) {
    if (!base) continue;
    hosts.push(`https://www.${base}.com`, `https://${base}.com`);
    hosts.push(`https://www.${base}.io`, `https://${base}.ai`);
  }
  return [...new Set(hosts)];
}

const CAREERS_PATHS = [
  "/careers",
  "/jobs",
  "/join-us",
  "/company/careers",
  "/en/careers",
  "/careers/open-roles",
];

async function findCareersUrl(origin: string): Promise<string | null> {
  for (const path of CAREERS_PATHS) {
    const url = new URL(path, origin).toString();
    const html = await fetchHtml(url);
    if (!html) continue;
    const $ = cheerio.load(html);
    const text = $("body").text().toLowerCase();
    if (
      text.includes("job") ||
      text.includes("career") ||
      text.includes("opening") ||
      $("a[href*='job']").length > 2
    ) {
      return url;
    }
  }

  const homeHtml = await fetchHtml(origin);
  if (!homeHtml) return null;
  const $ = cheerio.load(homeHtml);
  let best: string | null = null;
  $("a[href]").each((_, el) => {
    const href = $(el).attr("href");
    const label = $(el).text().toLowerCase();
    if (!href) return;
    if (
      /career|jobs|join us|we're hiring|open roles/i.test(label) ||
      /career|\/jobs/i.test(href)
    ) {
      try {
        best = new URL(href, origin).toString();
      } catch {
        /* ignore */
      }
    }
  });
  return best;
}

export async function resolveCompany(companyName: string): Promise<CompanyInfo> {
  const trimmed = companyName.trim();
  let domain: string | null = null;
  let careersUrl: string | null = null;

  for (const host of domainCandidates(trimmed)) {
    const html = await fetchHtml(host);
    if (!html) continue;
    try {
      domain = new URL(host).hostname;
    } catch {
      continue;
    }
    careersUrl = await findCareersUrl(host);
    if (careersUrl) break;
    if (html.length > 500) break;
  }

  return {
    name: trimmed,
    domain,
    careersUrl,
  };
}
