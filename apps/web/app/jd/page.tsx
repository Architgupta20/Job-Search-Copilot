import { JDForm } from "../components/jd-form";
import { ResumeGuard } from "../components/resume-guard";

export default function JDPage() {
  return (
    <div className="mx-auto w-full max-w-2xl">
      <ResumeGuard>
        <JDForm />
      </ResumeGuard>
    </div>
  );
}
