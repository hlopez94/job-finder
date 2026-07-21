#!/usr/bin/env python3
"""
RemoteOK Jobs Scraper
=======================
Parsea el feed de RemoteOK para extraer ofertas de trabajo remotas.
API pública: https://remoteok.com/api
"""

import requests
import re
from datetime import datetime, timedelta


def fetch_remoteok_jobs(config: dict, profile: dict) -> list[dict]:
    """
    Busca ofertas en RemoteOK vía su API pública.

    RemoteOK API es pública y no requiere autenticación.
    Endpoint: GET https://remoteok.com/api

    Args:
        config: Config del usuario (general.lookback_days)
        profile: Perfil del usuario (para filtrar por stack)

    Returns:
        Lista de dicts con job data normalizada
    """
    lookback_days = config.get("general", {}).get("lookback_days", 30)
    since_date = datetime.now() - timedelta(days=lookback_days)

    url = "https://remoteok.com/api"
    headers = {
        "User-Agent": "JobFinder/1.0 (job-finder-bot)",
        "Accept": "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"       ⚠️ RemoteOK API error: {resp.status_code}")
            return []

        data = resp.json()
        # El primer elemento es un meta-mensaje, skip
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "success" in data[0]:
            data = data[1:] if len(data) > 1 else []

        jobs = []
        for item in data:
            if not isinstance(item, dict):
                continue

            # Filtrar por fecha
            date_str = item.get("date", "")
            try:
                pub_date = datetime.strptime(date_str[:10], "%Y-%m-%d") if date_str else datetime.now()
            except ValueError:
                pub_date = datetime.now()

            if pub_date < since_date:
                continue

            job = _parse_remoteok_item(item)
            if job:
                jobs.append(job)

        return jobs

    except requests.RequestException as e:
        print(f"       ⚠️ RemoteOK connection error: {e}")
        return []


def _parse_remoteok_item(item: dict) -> dict | None:
    """Convierte un ítem de RemoteOK en estructura de job normalizada."""
    title = item.get("position", "") or item.get("title", "")
    if not title:
        return None

    company = item.get("company", "Unknown")
    description = item.get("description", "") or ""
    # Remover HTML tags
    description = re.sub(r"<[^>]+>", " ", description).strip()

    salary = _extract_salary(item)
    url = item.get("url", "")
    if url and not url.startswith("http"):
        url = f"https://remoteok.com{url}"

    return {
        "title": title,
        "company": company,
        "description": description[:1000],
        "url": url,
        "source": "remoteok",
        "remote": "Remote",
        "salary": salary,
        "location": "Remote (Worldwide)",
        "posted_at": item.get("date", ""),
        "tags": item.get("tags", []),
    }


def _extract_salary(item: dict) -> str:
    """Extrae rango salarial del ítem de RemoteOK."""
    # RemoteOK a veces incluye salary en el campo "salary" o en description
    salary = item.get("salary", "") or ""
    if salary:
        return salary

    # Intentar extraer de description
    desc = item.get("description", "") or ""
    patterns = [
        r"\$\s*(\d{2,3}[kK]?)\s*[-–to]*\s*\$?\s*(\d{2,3}[kK]?)",
        r"(?:salary|pay)[:\s]*\$?\s*([\d,]+)\s*[-–to]*\s*\$?\s*([\d,]*)",
    ]
    for pat in patterns:
        m = re.search(pat, desc, re.IGNORECASE)
        if m:
            return f"${m.group(1)} - ${m.group(2)}"

    return "N/A"
