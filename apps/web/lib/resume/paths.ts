import path from "path";

/** Project root: Job-Search-copilot/ (two levels above apps/web) */
export function getDataRoot() {
  return path.join(process.cwd(), "..", "..", "data", "resumes");
}

export function getResumeDir(id: string) {
  return path.join(getDataRoot(), id);
}
