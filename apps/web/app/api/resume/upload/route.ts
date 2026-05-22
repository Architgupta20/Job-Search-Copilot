import { randomUUID } from "crypto";
import { NextResponse } from "next/server";
import {
  buildParsedFacts,
  extractTextFromBuffer,
} from "@/lib/resume/parser";
import { saveResume } from "@/lib/resume/store";

export const runtime = "nodejs";

const MAX_BYTES = 10 * 1024 * 1024;

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!file || !(file instanceof File)) {
      return NextResponse.json(
        { error: "No file provided. Use field name 'file'." },
        { status: 400 },
      );
    }

    if (file.size > MAX_BYTES) {
      return NextResponse.json(
        { error: "File must be 10 MB or smaller." },
        { status: 400 },
      );
    }

    const fileName = file.name;
    const lower = fileName.toLowerCase();
    const isDocx = lower.endsWith(".docx");
    const isPdf = lower.endsWith(".pdf");

    if (!isDocx && !isPdf) {
      return NextResponse.json(
        { error: "Only PDF and DOCX files are supported." },
        { status: 400 },
      );
    }

    const mimeType = isDocx
      ? "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      : "application/pdf";

    const buffer = Buffer.from(await file.arrayBuffer());
    const rawText = await extractTextFromBuffer(buffer, mimeType, fileName);

    if (!rawText || rawText.length < 50) {
      return NextResponse.json(
        {
          error:
            "Could not extract enough text from the resume. Try a different file or DOCX format.",
        },
        { status: 422 },
      );
    }

    const parsedFacts = buildParsedFacts(rawText);
    const id = randomUUID();

    const record = await saveResume({
      id,
      fileName,
      mimeType,
      buffer,
      parsedFacts,
    });

    return NextResponse.json({
      id: record.id,
      fileName: record.fileName,
      uploadedAt: record.uploadedAt,
      contact: record.parsedFacts.contact,
      claimCount: record.parsedFacts.allowedClaims.length,
    });
  } catch (err) {
    console.error("Resume upload failed:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Upload failed." },
      { status: 500 },
    );
  }
}
