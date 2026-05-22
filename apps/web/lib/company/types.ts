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
};

export type JobResult = {
  title: string;
  url: string;
  location: string | null;
  snippet: string | null;
  matchScore: number;
};

export type CompanyRunResult = {
  runId: string;
  company: CompanyInfo;
  people: PersonResult[];
  jobs: JobResult[];
  warnings: string[];
};
