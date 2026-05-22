import type { CompanyRunResult } from "@/lib/company/types";

function esc(value: string | number | null | undefined): string {
  const s = String(value ?? "");
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function buildCompanyResultsCsv(result: CompanyRunResult): string {
  const lines: string[] = [];
  lines.push(
    [
      "type",
      "company",
      "name_or_title",
      "subtitle",
      "url",
      "role",
      "ats_percent",
      "email",
      "linkedin",
    ].join(","),
  );

  const company = result.company.name;

  for (const p of result.people) {
    lines.push(
      [
        "person",
        esc(company),
        esc(p.name),
        esc(p.title),
        esc(p.linkedinUrl),
        esc(p.matchedRole),
        "",
        esc(p.email),
        esc(p.linkedinUrl),
      ].join(","),
    );
  }

  for (const j of result.jobs) {
    lines.push(
      [
        "job",
        esc(company),
        esc(j.title),
        esc(j.snippet),
        esc(j.url),
        esc(j.matchedRole),
        j.atsScorePercent ?? "",
        "",
        "",
      ].join(","),
    );
  }

  return lines.join("\n");
}

export function downloadCompanyResultsCsv(result: CompanyRunResult) {
  const csv = buildCompanyResultsCsv(result);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${result.company.name.replace(/[^a-z0-9]+/gi, "-")}-search.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
