#!/usr/bin/env python3
"""
StackOverflow Jobs Scraper
============================
Parsea ofertas de trabajo de Stack Overflow Jobs.
Usa scraping del HTML ya que no tienen API pública oficial.
"""

import requests
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


def fetch_stackoverflow_jobs(config: dict, profile: dict) -> list[dict]:
    """
    Busca ofertas en Stack Overflow Jobs vía scraping.

    URL: https://stackoverflow.com/jobs

    Args:
        config: Config del usuario
        profile: Perfil del usuario (para filtrar por stack)

    Returns:
        Lista de dicts con job data normalizada
    """
    lookback_days = config.get("general", {}).get("lookback_days", 30)

    # Usar el stack del perfil para construir búsqueda
    p = profile.get("profile", {})
    preferred_stack = p.get("preferred_stack", {})
    all_techs = (
        preferred_stack.get("languages", [])
        + preferred_stack.get("frameworks", [])
    )
    # Tomar las primeras tecnologías para la búsqueda
    tech_query = "+".join(all_techs[:3]) if all_techs else "developer"

    # Construir query de búsqueda
    remote_param = "&r=true" if p.get("preferences", {}).get("remote_only", True) else ""

    url = (
        f"https://stackoverflow.com/jobs"
        f"?q={tech_query}"
        f"{remote_param}"
        f"&sort= freshness"
        f"&max=50"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"       ⚠️ StackOverflow error: {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []

        # Stack Overflow jobs listing
        job_cards = soup.select("div.js-result, div.-job, article.listResults > div")
        if not job_cards:
            # Fallback: buscar cualquier card con data-jobid
            job_cards = soup.find_all("div", attrs={"data-jobid": True})

        for card in job_cards:
            job = _parse_stackoverflow_card(card)
            if job:
                jobs.append(job)

        return jobs

    except requests.RequestException as e:
        print(f"       ⚠️ StackOverflow connection error: {e}")
        return []
    except Exception as e:
        print(f"       ⚠️ StackOverflow parse error: {e}")
        return []


def _parse_stackoverflow_card(card) -> dict | None:
    """Parsea una card de trabajo de Stack Overflow."""
    try:
        # Título
        title_el = card.select_one("h2 a, a.s-link, a[data-jobid]")
        if not title_el:
            return None
        title = title_el.get_text(strip=True)
        url_suffix = title_el.get("href", "")
        if url_suffix and not url_suffix.startswith("http"):
            url = f"https://stackoverflow.com{url_suffix}"
        else:
            url = url_suffix or ""

        # Empresa
        company_el = card.select_one("span.employer, span:has(strong), [itemprop='hiringOrganization']")
        company = company_el.get_text(strip=True) if company_el else "Unknown"

        # Ubicación
        location_el = card.select_one("span.location, [itemprop='jobLocation']")
        location = location_el.get_text(strip=True) if location_el else "N/A"

        # Remoto
        remote = "Remote" if "remote" in (card.get_text(strip=True)).lower() else "Unknown"

        # Tags / stack
        tags = []
        tag_els = card.select("a.post-tag, span.tag, div.tags > a")
        for tag in tag_els:
            tags.append(tag.get_text(strip=True))

        # Fecha
        date_el = card.select_one("span.date, time, [datetime]")
        posted_at = ""
        if date_el:
            posted_at = date_el.get("datetime", "") or date_el.get_text(strip=True)

        # Descripción (breve)
        desc_el = card.select_one("p.description, div.description, div.summary")
        description = desc_el.get_text(strip=True) if desc_el else ""

        return {
            "title": title,
            "company": company,
            "description": description[:1000],
            "url": url,
            "source": "stackoverflow",
            "remote": remote,
            "salary": "N/A",  # StackOverflow no siempre muestra salary
            "location": location,
            "posted_at": posted_at,
            "tags": tags,
        }

    except Exception as e:
        return None
