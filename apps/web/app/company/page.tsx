import { Suspense } from "react";
import { CompanyForm } from "../components/company-form";

export default function CompanyPage() {
  return (
    <div className="mx-auto w-full max-w-3xl">
      <Suspense
        fallback={
          <p className="text-sm text-zinc-500">Loading company tools…</p>
        }
      >
        <CompanyForm />
      </Suspense>
    </div>
  );
}
