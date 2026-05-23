import type { CompanyRunResult } from "@/lib/company/types";

function esc(value: string | number | null | undefined): string {
  const s = String(value ?? "");
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function buildCompanyResultsCsv(result: CompanyRunResult): string {
  const headers = [
    "serial no",
    "company name",
    "person name",
    "role",
    "linkedin url",
    "email id",
    "contact number",
  ];

  const lines: string[] = [headers.join(",")];
  const company = result.company.name;

  result.people.forEach((p, index) => {
    lines.push(
      [
        index + 1,
        esc(company),
        esc(p.name),
        esc(p.title),
        esc(p.linkedinUrl ?? ""),
        esc(p.email ?? ""),
        esc(p.phone ?? ""),
      ].join(","),
    );
  });

  return lines.join("\n");
}

export function downloadCompanyResultsCsv(result: CompanyRunResult) {
  const csv = buildCompanyResultsCsv(result);
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${result.company.name.replace(/[^a-z0-9]+/gi, "-")}-people.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
