"use client";

import type {
  ApplicationEntry,
  ApplicationInput,
  ApplicationStatus,
} from "@/lib/tracker/types";

const STORAGE_KEY = "job-search-copilot:applications";
export const TRACKER_CHANGED_EVENT = "job-search-copilot:tracker-changed";

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function notifyChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(TRACKER_CHANGED_EVENT));
}

function newId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `app-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function loadApplications(): ApplicationEntry[] {
  if (!canUseStorage()) return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ApplicationEntry[];
    if (!Array.isArray(parsed)) return [];
    return parsed.sort(
      (a, b) =>
        new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
    );
  } catch {
    return [];
  }
}

function persist(entries: ApplicationEntry[]): void {
  if (!canUseStorage()) return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  notifyChanged();
}

export function addApplication(input: ApplicationInput): ApplicationEntry {
  const now = new Date().toISOString();
  const entry: ApplicationEntry = {
    id: newId(),
    company: input.company.trim(),
    role: input.role.trim(),
    contactName: input.contactName?.trim() || null,
    contactLinkedIn: input.contactLinkedIn?.trim() || null,
    contactEmail: input.contactEmail?.trim() || null,
    status: input.status ?? "saved",
    notes: input.notes?.trim() ?? "",
    createdAt: now,
    updatedAt: now,
  };
  const entries = loadApplications();
  persist([entry, ...entries]);
  return entry;
}

export function updateApplication(
  id: string,
  patch: Partial<
    Pick<
      ApplicationEntry,
      | "company"
      | "role"
      | "contactName"
      | "contactLinkedIn"
      | "contactEmail"
      | "status"
      | "notes"
    >
  >,
): ApplicationEntry | null {
  const entries = loadApplications();
  const index = entries.findIndex((e) => e.id === id);
  if (index < 0) return null;

  const current = entries[index];
  const next: ApplicationEntry = {
    ...current,
    ...patch,
    company: patch.company?.trim() ?? current.company,
    role: patch.role?.trim() ?? current.role,
    contactName:
      patch.contactName !== undefined
        ? patch.contactName?.trim() || null
        : current.contactName,
    contactLinkedIn:
      patch.contactLinkedIn !== undefined
        ? patch.contactLinkedIn?.trim() || null
        : current.contactLinkedIn,
    contactEmail:
      patch.contactEmail !== undefined
        ? patch.contactEmail?.trim() || null
        : current.contactEmail,
    notes: patch.notes !== undefined ? patch.notes.trim() : current.notes,
    updatedAt: new Date().toISOString(),
  };

  const updated = [...entries];
  updated[index] = next;
  persist(updated);
  return next;
}

export function deleteApplication(id: string): void {
  persist(loadApplications().filter((e) => e.id !== id));
}

export function setApplicationStatus(
  id: string,
  status: ApplicationStatus,
): ApplicationEntry | null {
  return updateApplication(id, { status });
}

export function hasSimilarApplication(
  input: ApplicationInput,
): ApplicationEntry | undefined {
  const company = input.company.trim().toLowerCase();
  const role = input.role.trim().toLowerCase();
  const contact = input.contactName?.trim().toLowerCase() ?? "";

  return loadApplications().find((e) => {
    if (e.company.toLowerCase() !== company) return false;
    if (e.role.toLowerCase() !== role) return false;
    if (!contact) return true;
    return (e.contactName?.toLowerCase() ?? "") === contact;
  });
}

export function addApplicationFromContact(input: ApplicationInput): {
  entry: ApplicationEntry;
  duplicate: boolean;
} {
  const existing = hasSimilarApplication(input);
  if (existing) {
    return { entry: existing, duplicate: true };
  }
  return { entry: addApplication(input), duplicate: false };
}
