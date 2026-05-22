import { randomUUID } from "crypto";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { fetchJobs } from "./jobs";
import { discoverPeople } from "./people";
import { resolveCompany } from "./resolve";
import type { CompanyRunResult } from "./types";

function getRunsDir() {
  return path.join(process.cwd(), "..", "..", "data", "runs");
}

export async function runCompanySearch(params: {
  companyName: string;
  targetRoles: string[];
}): Promise<CompanyRunResult> {
  const warnings: string[] = [];
  const company = await resolveCompany(params.companyName);

  if (!company.domain) {
    warnings.push(
      "Could not verify company website — job and people results may be limited.",
    );
  }

  let jobs: CompanyRunResult["jobs"] = [];
  if (company.careersUrl) {
    jobs = await fetchJobs(company.careersUrl, params.targetRoles);
  } else {
    warnings.push(
      "Careers page not found — add jobs manually or try exact company name.",
    );
  }

  const peopleResult = await discoverPeople({
    companyName: company.name,
    domain: company.domain,
  });

  warnings.push(...peopleResult.warnings);

  const runId = randomUUID();
  const result: CompanyRunResult = {
    runId,
    company,
    people: peopleResult.people,
    jobs,
    warnings: [...new Set(warnings)],
  };

  const dir = getRunsDir();
  await mkdir(dir, { recursive: true });
  await writeFile(
    path.join(dir, `${runId}.json`),
    JSON.stringify(result, null, 2),
    "utf-8",
  );

  return result;
}
