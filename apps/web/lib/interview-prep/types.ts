export type StarPrompt = {
  situation: string;
  task: string;
  action: string;
  result: string;
  tip: string;
};

export type InterviewQuestion = {
  id: number;
  question: string;
  category: "behavioral" | "technical" | "role-fit";
  resumeAnchor: string;
  starPrompt: StarPrompt;
};

export type InterviewPrepResult = {
  runId: string;
  resumeId: string;
  companyName: string;
  roleTitle: string;
  questions: InterviewQuestion[];
  resumeBulletsUsed: string[];
  jdKeywordsUsed: string[];
  source: "llm" | "template";
  warnings: string[];
};
