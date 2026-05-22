export const RESUME_ID_KEY = "job-search-copilot:resumeId";
export const RESUME_NAME_KEY = "job-search-copilot:resumeName";

export function saveResumeSession(id: string, fileName: string) {
  sessionStorage.setItem(RESUME_ID_KEY, id);
  sessionStorage.setItem(RESUME_NAME_KEY, fileName);
}

export function clearResumeSession() {
  sessionStorage.removeItem(RESUME_ID_KEY);
  sessionStorage.removeItem(RESUME_NAME_KEY);
}

export function getResumeSession(): { id: string; fileName: string } | null {
  const id = sessionStorage.getItem(RESUME_ID_KEY);
  const fileName = sessionStorage.getItem(RESUME_NAME_KEY);
  if (!id || !fileName) return null;
  return { id, fileName };
}
