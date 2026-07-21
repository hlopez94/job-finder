#!/usr/bin/env python3
"""
WeWorkRemotely Jobs Scraper
=============================
Parsea el feed RSS de WeWorkRemotely para extraer ofertas de trabajo.
"""

import feedparser
import re
from datetime import datetime, timedelta


def fetch_weworkremotely_jobs(config: dict, profile: dict) -> list[dict]:
    """
    Busca ofertas en WeWorkRemotely vía RSS.

    Args:
        config: Config del usuario (weworkremotely.categories)
        profile: Perfil del usuario

    Returns:
        Lista de dicts con job data normalizada
    """
    wwr_config = config.get("weworkremotely", {})
    if not wwr_config.get("enabled", True):
        print("   │   ⚠️ WeWorkRemotely deshabilitado en config")
        return []

    categories = wwr_config.get("categories", ["software-dev"])
    lookback_days = config.get("general", {}).get("lookback_days", 30)
    since_date = datetime.now() - timedelta(days=lookback_days)

    all_jobs = []
    seen_urls = set()

    for category in categories:
        feed_url = f"https://weworkremotely.com/categories/{category}/jobs.rss"
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            print(f"   │   ⚠️ Error fetching RSS for '{category}': {e}")
            continue

        for entry in feed.get("entries", []):
            published = entry.get("published_parsed") or entry.get("updated_parsed")
            if published:
                pub_date = datetime(*published[:6])
                if pub_date < since_date:
                    continue

            job = _parse_wwr_entry(entry, category)
            if job and job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)

    return all_jobs


def _parse_wwr_entry(entry: dict, category: str) -> dict | None:
    """Convierte una entrada RSS en estructura de job normalizada."""
    title = entry.get("title", "")
    summary = entry.get("summary", "") or ""
    link = entry.get("link", "")

    # Extraer empresa del título (formato: "Job Title at Company")
    company = "Unknown"
    title_parts = title.split(" at ")
    if len(title_parts) >= 2:
        company = title_parts[-1].strip()
        title = title_parts[0].strip()

    # Extraer salario
    salary = _extract_salary(summary + " " + title)

    return {
        "title": title,
        "company": company,
        "description": summary[:1000] if summary else "",
        "url": link,
        "source": "weworkremotely",
        "remote": "Remote",  # WeWorkRemotely es 100% remoto
        "salary": salary,
        "location": "Remote (Worldwide)",
        "posted_at": entry.get("published", ""),
        "category": category,
    }


def _extract_salary(text: str) -> str:
    """Extrae rango salarial."""
    patterns = [
        r"\$\s*(\d{2,3}[kK]?)\s*[-–to]*\s*\$?\s*(\d{2,3}[kK]?)",
        r"(?:salary|pay)[:\s]*\$?\s*([\d,]+)\s*[-–to]*\s*\$?\s*([\d,]*)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"${m.group(1)} - ${m.group(2)}"
    return "N/A"
