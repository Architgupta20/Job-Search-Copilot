export type ContactConfidence = "verified" | "likely" | "not_found";

export type CompanyInfo = {
  name: string;
  domain: string | null;
  careersUrl: string | null;
};

export type PersonResult = {
  name: string;
  title: string;
  linkedinUrl: string | null;
  email: string | null;
  phone: string | null;
  emailConfidence: ContactConfidence;
  phoneConfidence: ContactConfidence;
  source: string;
  matchedRole?: string;
};

export type JobResult = {
  title: string;
  url: string;
  location: string | null;
  snippet: string | null;
  matchScore: number;
  matchedRole?: string | null;
};

export type CompanyRunResult = {
  runId: string;
  company: CompanyInfo;
  people: PersonResult[];
  peopleByRole?: Record<string, PersonResult[]>;
  jobs: JobResult[];
  jobsByRole?: Record<string, JobResult[]>;
  peoplePerRole?: number;
  warnings: string[];
};
