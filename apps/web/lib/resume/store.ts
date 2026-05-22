import { mkdir, writeFile } from "fs/promises";
import path from "path";
import type { ParsedFacts, ResumeRecord } from "./types";
import { getResumeDir } from "./paths";

export async function saveResume(params: {
  id: string;
  fileName: string;
  mimeType: string;
  buffer: Buffer;
  parsedFacts: ParsedFacts;
}): Promise<ResumeRecord> {
  const dir = getResumeDir(params.id);
  await mkdir(dir, { recursive: true });

  const ext = path.extname(params.fileName) || ".bin";
  const storedPath = path.join(dir, `original${ext}`);
  await writeFile(storedPath, params.buffer);

  const record: ResumeRecord = {
    id: params.id,
    fileName: params.fileName,
    mimeType: params.mimeType,
    storedPath,
    uploadedAt: new Date().toISOString(),
    parsedFacts: params.parsedFacts,
  };

  await writeFile(
    path.join(dir, "meta.json"),
    JSON.stringify(record, null, 2),
    "utf-8",
  );

  return record;
}
