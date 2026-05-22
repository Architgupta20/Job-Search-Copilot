export type JDTailorResult = {
  runId: string;
  resumeId: string;
  jdTitle: string | null;
  tailoredText: string;
  keywordsUsed: string[];
  keywordsSkipped: string[];
  atsScorePercent: number;
  changeSummary: string[];
  warnings: string[];
};
