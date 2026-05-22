import { JDForm } from "../components/jd-form";
import { ResumeGuard } from "../components/resume-guard";

export default function JDPage() {
  return (
    <div className="min-h-full bg-zinc-50 px-4 py-12">
      <div className="mx-auto max-w-2xl">
        <ResumeGuard>
          <JDForm />
        </ResumeGuard>
      </div>
    </div>
  );
}
