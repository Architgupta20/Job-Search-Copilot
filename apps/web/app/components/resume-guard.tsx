"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getResumeSession } from "@/lib/resume/session";

export function ResumeGuard({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [session, setSession] = useState<{
    id: string;
    fileName: string;
  } | null>(null);

  useEffect(() => {
    setSession(getResumeSession());
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <p className="text-sm text-zinc-500">Checking resume session…</p>
    );
  }

  if (!session) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        No resume uploaded yet.{" "}
        <Link href="/" className="font-medium underline">
          Upload on home page
        </Link>{" "}
        first.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
        Using resume: <span className="font-medium">{session.fileName}</span>
      </div>
      {children}
    </div>
  );
}
