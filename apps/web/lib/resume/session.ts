"use client";

import { useEffect, useState } from "react";

export const RESUME_ID_KEY = "job-search-copilot:resumeId";
export const RESUME_NAME_KEY = "job-search-copilot:resumeName";
const TAB_SESSION_KEY = "job-search-copilot:tab-session";

/** Fired after save/clear so header and guards refresh in the same tab. */
export const RESUME_SESSION_EVENT = "job-search-copilot:resume-session";

export type ResumeSession = { id: string; fileName: string };

function canUseSessionStorage(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.sessionStorage !== "undefined"
  );
}

function notifyResumeSessionChanged(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(RESUME_SESSION_EVENT));
}

/**
 * Call once when the app loads in a new browser tab/window.
 * Clears any resume from a previous visit so Home asks for upload again.
 */
export function initAppSession(): void {
  if (!canUseSessionStorage()) return;
  try {
    if (!sessionStorage.getItem(TAB_SESSION_KEY)) {
      sessionStorage.removeItem(RESUME_ID_KEY);
      sessionStorage.removeItem(RESUME_NAME_KEY);
      // Remove old localStorage resume from earlier versions
      localStorage.removeItem(RESUME_ID_KEY);
      localStorage.removeItem(RESUME_NAME_KEY);
      sessionStorage.setItem(TAB_SESSION_KEY, "1");
      notifyResumeSessionChanged();
    }
  } catch {
    /* ignore */
  }
}

export function saveResumeSession(id: string, fileName: string) {
  if (!canUseSessionStorage()) return;
  sessionStorage.setItem(RESUME_ID_KEY, id);
  sessionStorage.setItem(RESUME_NAME_KEY, fileName);
  notifyResumeSessionChanged();
}

export function clearResumeSession() {
  if (!canUseSessionStorage()) return;
  sessionStorage.removeItem(RESUME_ID_KEY);
  sessionStorage.removeItem(RESUME_NAME_KEY);
  localStorage.removeItem(RESUME_ID_KEY);
  localStorage.removeItem(RESUME_NAME_KEY);
  notifyResumeSessionChanged();
}

export function getResumeSession(): ResumeSession | null {
  if (!canUseSessionStorage()) return null;
  const id = sessionStorage.getItem(RESUME_ID_KEY);
  const fileName = sessionStorage.getItem(RESUME_NAME_KEY);
  if (!id || !fileName) return null;
  return { id, fileName };
}

export type ResumeSessionState = {
  session: ResumeSession | null;
  ready: boolean;
};

/** Client-only hook; updates when resume is saved/cleared anywhere in the app. */
export function useResumeSession(): ResumeSessionState {
  const [state, setState] = useState<ResumeSessionState>({
    session: null,
    ready: false,
  });

  useEffect(() => {
    initAppSession();

    function refresh() {
      setState({ session: getResumeSession(), ready: true });
    }

    refresh();

    window.addEventListener(RESUME_SESSION_EVENT, refresh);

    return () => {
      window.removeEventListener(RESUME_SESSION_EVENT, refresh);
    };
  }, []);

  return state;
}
