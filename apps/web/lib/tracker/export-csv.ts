import type { ApplicationEntry } from "@/lib/tracker/types";
import { STATUS_LABELS } from "@/lib/tracker/types";

function esc(value: string | number | null | undefined): string {
  const s = String(value ?? "");
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function buildApplicationsCsv(entries: ApplicationEntry[]): string {
  const headers = [
    "company",
    "role",
    "contact name",
    "email",
    "linkedin",
    "status",
    "notes",
    "updated",
  ];
  const lines = [headers.join(",")];
  for (const e of entries) {
    lines.push(
      [
        esc(e.company),
        esc(e.role),
        esc(e.contactName),
        esc(e.contactEmail),
        esc(e.contactLinkedIn),
        esc(STATUS_LABELS[e.status]),
        esc(e.notes),
        esc(e.updatedAt.slice(0, 10)),
      ].join(","),
    );
  }
  return lines.join("\n");
}

export function downloadApplicationsCsv(entries: ApplicationEntry[]) {
  const blob = new Blob([buildApplicationsCsv(entries)], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `applications-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
