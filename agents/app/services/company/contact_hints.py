"""Where to look when email/phone are not on LinkedIn."""


def contact_lookup_hints(
    company_name: str,
    person_name: str,
    domain: str | None,
) -> list[str]:
    name = person_name.strip()
    co = company_name.strip()
    hints: list[str] = [
        f'Google: "{name}" "{co}" email OR contact',
        "LinkedIn profile → Contact info section (if visible to you)",
        "LinkedIn → Send connection request with a short note (use drafted message below)",
    ]
    if domain:
        d = domain.replace("www.", "")
        hints.insert(
            0,
            f'Company site: site:{d} "{name}" (team page, blog author, press release)',
        )
        hints.insert(
            1,
            f"Email pattern guess: firstname.lastname@{d} or firstname@{d} (verify before sending)",
        )
        hints.append(f"Hunter.io / Apollo.io — lookup {name} @ {d}")
    hints.extend(
        [
            "RocketReach, Lusha, or SignalHire (paid contact enrichment)",
            "GitHub / Google Scholar / conference speaker bio (common for engineers)",
            "Twitter/X bio link",
            f"{co} careers page or press kit — leadership quotes often list a media email",
            f"Ask a mutual connection or recruiter at {co} for a warm intro",
        ]
    )
    return hints
