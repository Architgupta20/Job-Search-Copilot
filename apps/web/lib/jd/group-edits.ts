import type { SuggestedEdit } from "@/lib/jd/types";

export function groupEditsBySection(
  edits: SuggestedEdit[],
): [string, SuggestedEdit[]][] {
  const map = new Map<string, SuggestedEdit[]>();
  for (const edit of edits) {
    const list = map.get(edit.section) ?? [];
    list.push(edit);
    map.set(edit.section, list);
  }
  return [...map.entries()];
}
