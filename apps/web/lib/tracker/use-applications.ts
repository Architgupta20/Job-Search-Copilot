"use client";

import { useEffect, useState } from "react";
import type { ApplicationEntry } from "@/lib/tracker/types";
import {
  loadApplications,
  TRACKER_CHANGED_EVENT,
} from "@/lib/tracker/storage";

export function useApplications(): {
  entries: ApplicationEntry[];
  ready: boolean;
  refresh: () => void;
} {
  const [entries, setEntries] = useState<ApplicationEntry[]>([]);
  const [ready, setReady] = useState(false);

  function refresh() {
    setEntries(loadApplications());
    setReady(true);
  }

  useEffect(() => {
    refresh();
    window.addEventListener(TRACKER_CHANGED_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(TRACKER_CHANGED_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, []);

  return { entries, ready, refresh };
}
