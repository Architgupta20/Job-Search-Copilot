export type CoverLetterResult = {
  runId: string;
  resumeId: string;
  companyName: string;
  roleTitle: string;
  body: string;
  jdKeywordsMatched: string[];
  jdKeywordsMissing: string[];
  resumeBulletsUsed: string[];
  warnings: string[];
};
