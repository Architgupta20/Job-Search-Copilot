import mammoth from "mammoth";
import { extractText, getDocumentProxy } from "unpdf";
import type { ParsedFacts } from "./types";

const EMAIL_RE = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/;
const PHONE_RE =
  /(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/;

async function extractPdfText(buffer: Buffer): Promise<string> {
  const pdf = await getDocumentProxy(new Uint8Array(buffer));
  const { text } = await extractText(pdf, { mergePages: true });
  if (Array.isArray(text)) return text.join("\n").trim();
  return (text ?? "").trim();
}

function buildAllowedClaims(rawText: string): string[] {
  const lines = rawText
    .split(/\r?\n/)
    .map((line) => line.replace(/\s+/g, " ").trim())
    .filter((line) => line.length >= 12);

  const unique = new Set<string>();
  for (const line of lines) {
    unique.add(line);
  }
  return [...unique].slice(0, 200);
}

function extractContact(rawText: string): ParsedFacts["contact"] {
  const lines = rawText.split(/\r?\n/).map((l) => l.trim());
  const top = lines.slice(0, 8).join(" ");
  const email = top.match(EMAIL_RE)?.[0] ?? rawText.match(EMAIL_RE)?.[0];
  const phone = top.match(PHONE_RE)?.[0] ?? rawText.match(PHONE_RE)?.[0];
  const name =
    lines.find(
      (l) =>
        l.length > 2 &&
        l.length < 60 &&
        !EMAIL_RE.test(l) &&
        !PHONE_RE.test(l) &&
        !/^(experience|education|skills|summary)/i.test(l),
    ) ?? undefined;

  return { name, email, phone };
}

export async function extractTextFromBuffer(
  buffer: Buffer,
  mimeType: string,
  fileName: string,
): Promise<string> {
  const lower = fileName.toLowerCase();

  if (
    mimeType ===
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
    lower.endsWith(".docx")
  ) {
    const result = await mammoth.extractRawText({ buffer });
    return result.value.trim();
  }

  if (mimeType === "application/pdf" || lower.endsWith(".pdf")) {
    return extractPdfText(buffer);
  }

  throw new Error("Unsupported file type. Use PDF or DOCX.");
}

export function buildParsedFacts(rawText: string): ParsedFacts {
  return {
    contact: extractContact(rawText),
    rawText,
    allowedClaims: buildAllowedClaims(rawText),
  };
}
