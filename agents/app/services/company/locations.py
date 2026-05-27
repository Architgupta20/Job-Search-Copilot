"""Country / city helpers for LinkedIn people search (SerpAPI)."""

from __future__ import annotations

# SerpAPI `location` parameter (Google search origin)
COUNTRY_SERP_LOCATION: dict[str, str] = {
    "India": "India",
    "United States": "United States",
    "United Kingdom": "United Kingdom",
    "Canada": "Canada",
    "Singapore": "Singapore",
    "United Arab Emirates": "United Arab Emirates",
    "Australia": "Australia",
    "Germany": "Germany",
}

# Cities per country (UI + query terms)
CITIES_BY_COUNTRY: dict[str, list[str]] = {
    "India": [
        "Delhi",
        "Mumbai",
        "Bengaluru",
        "Hyderabad",
        "Chennai",
        "Pune",
        "Kolkata",
        "Gurgaon",
        "Noida",
        "Ahmedabad",
        "Jaipur",
        "Chandigarh",
    ],
    "United States": [
        "New York",
        "San Francisco",
        "Seattle",
        "Austin",
        "Boston",
        "Chicago",
        "Los Angeles",
    ],
    "United Kingdom": ["London", "Manchester", "Edinburgh", "Birmingham"],
    "Canada": ["Toronto", "Vancouver", "Montreal", "Calgary"],
    "Singapore": ["Singapore"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi"],
    "Australia": ["Sydney", "Melbourne", "Brisbane"],
    "Germany": ["Berlin", "Munich", "Frankfurt"],
}

# Extra spellings / metro names for snippet matching
_CITY_ALIASES: dict[tuple[str, str], list[str]] = {
    ("India", "Delhi"): ["delhi", "new delhi", "ncr", "national capital region"],
    ("India", "Mumbai"): ["mumbai", "bombay"],
    ("India", "Bengaluru"): ["bengaluru", "bangalore"],
    ("India", "Gurgaon"): ["gurgaon", "gurugram"],
    ("India", "Hyderabad"): ["hyderabad", "cyberabad"],
    ("United States", "San Francisco"): ["san francisco", "sf bay", "bay area"],
    ("United States", "New York"): ["new york", "nyc", "new york city"],
    ("United Kingdom", "London"): ["london", "greater london"],
}


def normalize_country(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    v = value.strip()
    for name in COUNTRY_SERP_LOCATION:
        if name.lower() == v.lower():
            return name
    return v


def normalize_city(country: str | None, value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    v = value.strip()
    if country and country in CITIES_BY_COUNTRY:
        for c in CITIES_BY_COUNTRY[country]:
            if c.lower() == v.lower():
                return c
    return v


def serpapi_location(country: str | None, city: str | None) -> str | None:
    """Value for SerpAPI Google `location` param."""
    country = normalize_country(country)
    city = normalize_city(country, city)
    if not country:
        return None
    if city:
        return f"{city}, {country}"
    return COUNTRY_SERP_LOCATION.get(country, country)


def query_location_terms(country: str | None, city: str | None) -> str:
    """Appended to Google `q` for LinkedIn people search."""
    country = normalize_country(country)
    city = normalize_city(country, city)
    parts: list[str] = []
    if city:
        parts.append(city)
    if country:
        parts.append(country)
    return " ".join(parts)


def location_label(country: str | None, city: str | None) -> str | None:
    country = normalize_country(country)
    city = normalize_city(country, city)
    if city and country:
        return f"{city}, {country}"
    if country:
        return country
    if city:
        return city
    return None


def person_matches_location(
    snippet: str,
    serp_title: str,
    country: str | None,
    city: str | None,
) -> bool:
    """When user picks a city, keep profiles whose snippet/title mentions that area."""
    country = normalize_country(country)
    city = normalize_city(country, city)
    if not country and not city:
        return True

    blob = f"{snippet} {serp_title}".lower()

    if city and country:
        key = (country, city)
        aliases = _CITY_ALIASES.get(key, [city.lower()])
        if any(a in blob for a in aliases):
            return True
        # LinkedIn snippets often use metro only
        return city.lower() in blob

    if country:
        low_country = country.lower()
        if low_country in blob:
            return True
        if country == "India" and any(
            term in blob
            for term in (
                "india",
                "indian",
                "bengaluru",
                "bangalore",
                "mumbai",
                "delhi",
                "hyderabad",
                "chennai",
                "pune",
                "kolkata",
                "gurgaon",
                "noida",
            )
        ):
            return True
        return False

    return True
