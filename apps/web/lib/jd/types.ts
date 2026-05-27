export type SuggestedEdit = {
  section: string;
  /** Plain-language pointer for where to edit in the user's Word/PDF resume */
  sectionHint?: string;
  original: string;
  suggested: string;
  reason: string;
  matchedKeywords?: string[];
};

export type AtsBreakdown = {
  scorePercent: number;
  totalKeywords: number;
  matchedKeywords: string[];
  missingKeywords: string[];
  supportedCount: number;
};

export type JDTailorResult = {
  runId: string;
  resumeId: string;
  jdTitle: string | null;
  tailoredText: string;
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
