"use client";

import { useEffect, useState } from "react";

export const RESUME_ID_KEY = "job-search-copilot:resumeId";
export const RESUME_NAME_KEY = "job-search-copilot:resumeName";

/** Fired after save/clear so header and guards refresh in the same tab. */
export const RESUME_SESSION_EVENT = "job-search-copilot:resume-session";

export type ResumeSession = { id: string; fileName: string };

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

/** One-time: copy old sessionStorage keys into localStorage. */
function migrateFromSessionStorage(): void {
  if (!canUseStorage()) return;
  const hasLocal = localStorage.getItem(RESUME_ID_KEY);
  if (hasLocal) return;
  try {
    const id = sessionStorage.getItem(RESUME_ID_KEY);
    const fileName = sessionStorage.getItem(RESUME_NAME_KEY);
    if (id && fileName) {
      localStorage.setItem(RESUME_ID_KEY, id);
      localStorage.setItem(RESUME_NAME_KEY, fileName);
      sessionStorage.removeItem(RESUME_ID_KEY);
      sessionStorage.removeItem(RESUME_NAME_KEY);
    }
  } catch {
    /* ignore quota / private mode */
  }
}

function notifyResumeSessionChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(RESUME_SESSION_EVENT));
}

export function saveResumeSession(id: string, fileName: string) {
  if (!canUseStorage()) return;
  localStorage.setItem(RESUME_ID_KEY, id);
  localStorage.setItem(RESUME_NAME_KEY, fileName);
  notifyResumeSessionChanged();
}

export function clearResumeSession() {
  if (!canUseStorage()) return;
  localStorage.removeItem(RESUME_ID_KEY);
  localStorage.removeItem(RESUME_NAME_KEY);
  try {
    sessionStorage.removeItem(RESUME_ID_KEY);
    sessionStorage.removeItem(RESUME_NAME_KEY);
  } catch {
    /* ignore */
  }
  notifyResumeSessionChanged();
}

export function getResumeSession(): ResumeSession | null {
  if (!canUseStorage()) return null;
  migrateFromSessionStorage();
  const id = localStorage.getItem(RESUME_ID_KEY);
  const fileName = localStorage.getItem(RESUME_NAME_KEY);
  if (!id || !fileName) return null;
  return { id, fileName };
}

export type ResumeSessionState = {
  session: ResumeSession | null;
  /** False until localStorage has been read (avoids flashing "No resume"). */
  ready: boolean;
};

/** Client-only hook; updates when resume is saved/cleared anywhere in the app. */
export function useResumeSession(): ResumeSessionState {
  const [state, setState] = useState<ResumeSessionState>({
    session: null,
    ready: false,
  });

  useEffect(() => {
    function refresh() {
      setState({ session: getResumeSession(), ready: true });
    }

    refresh();

    window.addEventListener(RESUME_SESSION_EVENT, refresh);
    window.addEventListener("storage", refresh);

    return () => {
      window.removeEventListener(RESUME_SESSION_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  return state;
}
