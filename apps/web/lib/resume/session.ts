"use client";

import { useEffect, useState } from "react";

export const RESUME_ID_KEY = "job-search-copilot:resumeId";
export const RESUME_NAME_KEY = "job-search-copilot:resumeName";

export type ResumeSession = { id: string; fileName: string };

function canUseSessionStorage(): boolean {
  return typeof window !== "undefined" && typeof window.sessionStorage !== "undefined";
}

export function saveResumeSession(id: string, fileName: string) {
  if (!canUseSessionStorage()) return;
  sessionStorage.setItem(RESUME_ID_KEY, id);
  sessionStorage.setItem(RESUME_NAME_KEY, fileName);
}

export function clearResumeSession() {
  if (!canUseSessionStorage()) return;
  sessionStorage.removeItem(RESUME_ID_KEY);
  sessionStorage.removeItem(RESUME_NAME_KEY);
}

export function getResumeSession(): ResumeSession | null {
  if (!canUseSessionStorage()) return null;
  const id = sessionStorage.getItem(RESUME_ID_KEY);
  const fileName = sessionStorage.getItem(RESUME_NAME_KEY);
  if (!id || !fileName) return null;
  return { id, fileName };
}

/** Client-only: safe to use during render (no SSR sessionStorage access). */
export function useResumeSession(): ResumeSession | null {
  const [session, setSession] = useState<ResumeSession | null>(null);

  useEffect(() => {
    setSession(getResumeSession());
  }, []);

  return session;
}
