export type ParsedFacts = {
  contact: {
    name?: string;
    email?: string;
    phone?: string;
  };
  rawText: string;
  allowedClaims: string[];
};

export type ResumeRecord = {
  id: string;
  fileName: string;
  mimeType: string;
  storedPath: string;
  uploadedAt: string;
  parsedFacts: ParsedFacts;
};
