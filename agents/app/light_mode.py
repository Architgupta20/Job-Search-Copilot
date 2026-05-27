"""Reduce CPU/network load on laptops — set JOB_COPILOT_LIGHT=1 (dev:lite does this)."""

from __future__ import annotations

import os


def is_light_mode() -> bool:
    return os.getenv("JOB_COPILOT_LIGHT", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def people_per_role() -> int:
    return 3 if is_light_mode() else 10


def serp_query_limit() -> int:
    """How many Google query variants per role."""
    return 1 if is_light_mode() else 3


def serp_page_starts() -> tuple[int, ...]:
    """SerpAPI start offsets (each is one paid search)."""
    return (0,) if is_light_mode() else (0, 10)


def skip_careers_scrape() -> bool:
    return is_light_mode()


def skip_company_host_probe() -> bool:
    """Skip multi-URL company website probing."""
    return is_light_mode()
