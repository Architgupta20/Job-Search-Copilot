import * as cheerio from "cheerio";
import type { ContactConfidence, PersonResult } from "./types";
import { fetchHtml } from "./http";
import {
  filterAndRankPeople,
  isExcludedOutreachTitle,
  PEOPLE_LINKEDIN_QUERY,
  SENIOR_OUTREACH_TITLE,
} from "./people-filters";

const EMAIL_RE = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
const PHONE_RE =
  /(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g;

const SENIOR_TITLE_FROM_SNIPPET =
  /(CEO|CTO|COO|Chief|Founder|President|VP|Vice President|SVP|Director|Head of[^.|]{0,40}|Lead(?:ing)?[^.|]{0,30}(?:AI|ML|Machine Learning|Engineering)?|Principal|Staff|Program Manager|Engineering Manager|Hiring Manager|Recruiter|Talent Acquisition|Talent Partner)[^.|]*/i;

function confidence(value: string | null): ContactConfidence {
  if (!value) return "not_found";
  return "likely";
}

function extractTitleFromSnippet(snippet: string, fallback: string): string {
  const match = snippet.match(SENIOR_TITLE_FROM_SNIPPET);
  return (match?.[0] ?? fallback).trim();
}

function parseSerpLinkedIn(
  results: { title?: string; link?: string; snippet?: string }[],
  companyName: string,
): PersonResult[] {
  const people: PersonResult[] = [];
  const seen = new Set<string>();

  for (const item of results) {
    const link = item.link ?? "";
    if (!link.includes("linkedin.com/in")) continue;

    const title = item.title ?? "";
    const snippet = item.snippet ?? "";
    const namePart = title.split("-")[0]?.split("|")[0]?.trim() ?? "";
    const name = namePart.replace(/\s+\|.*/, "").trim();
    if (!name || name.length < 3) continue;
    if (seen.has(link)) continue;
    seen.add(link);

    const jobTitle = extractTitleFromSnippet(snippet, "Leader");
    if (isExcludedOutreachTitle(jobTitle)) continue;

    people.push({
      name,
      title: jobTitle,
      linkedinUrl: link.split("?")[0],
      email: null,
      phone: null,
      emailConfidence: "not_found",
      phoneConfidence: "not_found",
      source: `SerpAPI · ${companyName}`,
    });
  }

  return filterAndRankPeople(people, 10);
}

async function discoverViaSerpApi(
  companyName: string,
): Promise<PersonResult[]> {
  const key = process.env.SERPAPI_API_KEY;
  if (!key) return [];

  const q = `site:linkedin.com/in ${companyName} ${PEOPLE_LINKEDIN_QUERY}`;
  const url = new URL("https://serpapi.com/search.json");
  url.searchParams.set("engine", "google");
  url.searchParams.set("q", q);
  url.searchParams.set("num", "20");
  url.searchParams.set("api_key", key);

  const res = await fetch(url.toString());
  if (!res.ok) return [];

  const data = (await res.json()) as {
    organic_results?: { title?: string; link?: string; snippet?: string }[];
  };
  return parseSerpLinkedIn(data.organic_results ?? [], companyName);
}

async function discoverViaTeamPages(
  domain: string,
  companyName: string,
): Promise<PersonResult[]> {
  const paths = ["/team", "/about", "/about-us", "/leadership", "/company"];
  const people: PersonResult[] = [];
  const seen = new Set<string>();

  for (const path of paths) {
    const origin = `https://${domain}`;
    const html = await fetchHtml(new URL(path, origin).toString());
    if (!html) continue;

    const $ = cheerio.load(html);
    const blocks: string[] = [];

    $("h2, h3, h4, .team-member, [class*='team'], [class*='leadership']").each(
      (_, el) => {
        const text = $(el).text().replace(/\s+/g, " ").trim();
        if (text.length > 8 && text.length < 120) blocks.push(text);
      },
    );

    const pageEmails = html.match(EMAIL_RE) ?? [];
    const pagePhones = html.match(PHONE_RE) ?? [];

    for (const block of blocks.slice(0, 40)) {
      const parts = block.split(/[-–—|]/);
      const name = parts[0]?.trim();
      const jobTitle = parts.slice(1).join(" ").trim() || "";
      if (!name || name.length < 4 || name.length > 50) continue;
      if (seen.has(name.toLowerCase())) continue;
      if (!/[A-Z][a-z]+/.test(name)) continue;
      if (!jobTitle || !SENIOR_OUTREACH_TITLE.test(jobTitle)) continue;
      if (isExcludedOutreachTitle(jobTitle)) continue;
      seen.add(name.toLowerCase());

      const email = pageEmails.find((e) => !e.includes("example.com")) ?? null;
      const phone = pagePhones[0] ?? null;

      people.push({
        name,
        title: jobTitle.slice(0, 80),
        linkedinUrl: `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(`${name} ${companyName}`)}`,
        email,
        phone,
        emailConfidence: confidence(email),
        phoneConfidence: confidence(phone),
        source: `Company website · ${domain}`,
      });
    }
  }

  return filterAndRankPeople(people, 10);
}

async function discoverViaOpenAI(
  companyName: string,
  contextText: string,
): Promise<PersonResult[]> {
  const key = process.env.OPENAI_API_KEY;
  if (!key || !contextText.trim()) return [];

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      temperature: 0.2,
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content:
            'Extract up to 10 real people for cold outreach: CEOs, VPs, Directors, Heads of, Lead/Principal/Staff engineers, Program Managers, Engineering Managers, Recruiters. EXCLUDE: SDE1, SD1, SDE I/II, Junior, Intern, entry-level, and generic "AI Engineer" or "ML Engineer" without Lead/Senior/Director/Head/Principal/Staff. Return JSON: { "people": [{ "name", "title", "email", "phone" }] }. Use null for unknown email/phone. Do not invent people.',
        },
        {
          role: "user",
          content: `Company: ${companyName}\n\nText:\n${contextText.slice(0, 12000)}`,
        },
      ],
    }),
  });

  if (!res.ok) return [];

  const data = (await res.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  const raw = data.choices?.[0]?.message?.content;
  if (!raw) return [];

  try {
    const parsed = JSON.parse(raw) as {
      people?: {
        name: string;
        title: string;
        email?: string | null;
        phone?: string | null;
      }[];
    };
    const mapped = (parsed.people ?? []).map((p) => ({
      name: p.name,
      title: p.title,
      linkedinUrl: `https://www.linkedin.com/search/results/people/?keywords=${encodeURIComponent(`${p.name} ${companyName}`)}`,
      email: p.email ?? null,
      phone: p.phone ?? null,
      emailConfidence: confidence(p.email ?? null),
      phoneConfidence: confidence(p.phone ?? null),
      source: "OpenAI · page text",
    }));
    return filterAndRankPeople(mapped, 10);
  } catch {
    return [];
  }
}

export async function discoverPeople(params: {
  companyName: string;
  domain: string | null;
}): Promise<{ people: PersonResult[]; warnings: string[] }> {
  const warnings: string[] = [];
  let people: PersonResult[] = [];

  people = await discoverViaSerpApi(params.companyName);
  if (people.length === 0) {
    warnings.push(
      "LinkedIn leaders via SerpAPI not available — using website + optional OpenAI.",
    );
  }

  if (people.length < 10 && params.domain) {
    const fromSite = await discoverViaTeamPages(
      params.domain,
      params.companyName,
    );
    const seen = new Set(people.map((p) => p.name.toLowerCase()));
    for (const p of fromSite) {
      if (!seen.has(p.name.toLowerCase())) people.push(p);
    }
    people = filterAndRankPeople(people, 10);
  }

  if (people.length < 5 && params.domain && process.env.OPENAI_API_KEY) {
    const html =
      (await fetchHtml(`https://${params.domain}/team`)) ??
      (await fetchHtml(`https://${params.domain}/about`));
    if (html) {
      const $ = cheerio.load(html);
      const text = $("body").text().replace(/\s+/g, " ").slice(0, 12000);
      const fromAi = await discoverViaOpenAI(params.companyName, text);
      const seen = new Set(people.map((p) => p.name.toLowerCase()));
      for (const p of fromAi) {
        if (!seen.has(p.name.toLowerCase())) people.push(p);
      }
      people = filterAndRankPeople(people, 10);
    }
  }

  if (!process.env.SERPAPI_API_KEY) {
    warnings.push(
      "Add SERPAPI_API_KEY in .env for stronger LinkedIn people results.",
    );
  }

  warnings.push(
    "People list targets leaders & hiring contacts only (no SDE1 / junior IC roles).",
  );

  return { people, warnings };
}
