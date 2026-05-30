"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useResumeSession } from "@/lib/resume/session";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/company", label: "Company" },
  { href: "/tracker", label: "Tracker" },
  { href: "/jd", label: "JD tailor" },
  { href: "/cover-letter", label: "Cover letter" },
] as const;

function navClass(active: boolean) {
  return active
    ? "font-semibold text-emerald-800"
    : "text-zinc-600 hover:text-zinc-900";
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { session, ready } = useResumeSession();

  return (
    <div className="flex min-h-full flex-col bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <Link
            href="/"
            className="text-sm font-semibold tracking-tight text-zinc-900"
          >
            Job Search Copilot
          </Link>
          <nav className="flex flex-wrap items-center gap-4 text-sm">
            {NAV.map(({ href, label }) => (
              <Link
                key={href}
                href={href}
                className={navClass(
                  href === "/" ? pathname === "/" : pathname.startsWith(href),
                )}
              >
                {label}
              </Link>
            ))}
          </nav>
          {!ready ? (
            <p className="text-xs text-zinc-400">Checking resume…</p>
          ) : session ? (
            <p
              className="max-w-[12rem] truncate text-xs text-zinc-500"
              title={session.fileName}
            >
              Resume: {session.fileName}
            </p>
          ) : (
            <p className="text-xs text-zinc-400">No resume</p>
          )}
        </div>
      </header>
      <main className="flex-1 px-4 py-10">{children}</main>
    </div>
  );
}
