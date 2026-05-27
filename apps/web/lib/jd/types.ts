export type SuggestedEdit = {
  section: string;
  bulletNumber?: number;
  /** Plain-language pointer for where to edit in the user's Word/PDF resume */
  sectionHint?: string;
  original: string;
  suggested: string;
  jdKeywordsAdded?: string[];
  wordCount?: number;
  reasonForChange?: string;
  /** Backward-compatible alias */
  reason: string;
  matchedKeywords?: string[];
  targetMissingKeywords?: string[];
  addedKeywords?: string[];
};

export type AtsBreakdown = {
  scorePercent: number;
  totalKeywords: number;
  matchedKeywords: string[];
  missingKeywords: string[];
  supportedCount: number;
  relatedMatchedKeywords?: string[];
};

export type JDTailorResult = {
  runId: string;
  resumeId: string;
  jdTitle: string | null;
  tailoredText: string;
  tailoringReport?: string;
  suggestedEdits?: SuggestedEdit[];
  keywordsUsed: string[];
  keywordsSkipped: string[];
  atsScorePercent: number;
  atsBreakdown: AtsBreakdown;
  changeSummary: string[];
  warnings: string[];
  sourceJobUrl?: string;
  sourceJobTitle?: string;
};
