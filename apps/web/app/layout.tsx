import type { Metadata } from "next";
import { AppShell } from "./components/app-shell";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Search Copilot",
  description:
    "Upload a resume, search companies for contacts and jobs, tailor to a JD, and prep for interviews.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
