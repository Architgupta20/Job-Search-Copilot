import { readFile } from "fs/promises";
import path from "path";
import type { ResumeRecord } from "./types";
import { getResumeDir } from "./paths";

export async function loadResume(id: string): Promise<ResumeRecord | null> {
  try {
    const raw = await readFile(
      path.join(getResumeDir(id), "meta.json"),
      "utf-8",
    );
    return JSON.parse(raw) as ResumeRecord;
  } catch {
    return null;
  }
}
