import { Suspense } from "react";
import { InterviewPrepForm } from "../components/interview-prep-form";

export default function InterviewPrepPage() {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <Suspense fallback={<p className="text-sm text-zinc-500">Loading…</p>}>
        <InterviewPrepForm />
      </Suspense>
    </div>
  );
}
