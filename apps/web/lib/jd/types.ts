export type SuggestedEdit = {
  section: string;
  original: string;
  suggested: string;
  reason: string;
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
