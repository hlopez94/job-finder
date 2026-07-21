#!/usr/bin/env python3
"""
LinkedIn Jobs Scraper (Guest API)
==================================
Busca ofertas de trabajo en LinkedIn usando la Guest Jobs API (pública).
No requiere autenticación — usa la misma interfaz que.linkedin.com/jobs.

Endpoint: https://www.linkedin.com/jobs/search
Devuelve HTML con cards de jobs que parseamos con BeautifulSoup.

Parámetros de búsqueda:
  - keywords: términos de búsqueda (del perfil)
  - location: ubicación (default: "")
  - f_TPR: rango de tiempo (r604800 = 7 días, r2592000 = 30 días)
  - start: offset para paginación (0, 25, 50, ...)
  - f_WT: tipo de trabajo (2 = remoto)
"""

import re
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


# LinkedIn Guest Jobs API
_SEARCH_URL = "https://www.linkedin.com/jobs/search"
_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Máximo de páginas a traer (cada página = ~25 jobs)
_MAX_PAGES = 4
_JOBS_PER_PAGE = 25


def fetch_linkedin_jobs(config: dict, profile: dict) -> list[dict]:
    """
    Busca ofertas en LinkedIn vía Guest Jobs API.

    Args:
        config: Config del usuario (linkedin.search_keywords, etc.)
        profile: Perfil del usuario (para keywords)

    Returns:
        Lista de dicts con job data normalizada
    """
    p = profile.get("profile", {})
    linkedin_config = config.get("linkedin", {})

    if not linkedin_config.get("enabled", True):
        return []

    # Keywords de búsqueda (del config o del perfil)
    keywords = linkedin_config.get("search_keywords", [])
    if not keywords:
        stack = p.get("preferred_stack", {})
        keywords = stack.get("languages", []) + stack.get("frameworks", [])
        seniority = p.get("experience", {}).get("level", "")
        if seniority:
            keywords.append(seniority)

    if not keywords:
        keywords = [".NET", "Angular", "Remote"]

    lookback_days = config.get("general", {}).get("lookback_days", 30)
    # LinkedIn time filter: r604800 = 7 days, r2592000 = 30 days
    time_filter = "r604800" if lookback_days <= 7 else "r2592000"

    all_jobs = []

    # Buscar con cada keyword principal
    # Usamos las 2-3 keywords más relevantes para no sobrecargar
    search_terms = _build_search_terms(keywords, p)

    for term in search_terms:
        try:
            jobs = _search_linkedin(term, time_filter)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"       ⚠️ LinkedIn error '{term}': {e}")

    # Deduplicar por URL
    seen_urls = set()
    unique = []
    for job in all_jobs:
        url = job.get("url", "")
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        unique.append(job)

    return unique


def _build_search_terms(keywords: list, profile: dict) -> list[str]:
    """
    Construye términos de búsqueda optimizados.
    Combina tecnologías con seniority para mejores resultados.
    """
    seniority = profile.get("experience", {}).get("level", "Senior")
    terms = []

    # Combinaciones clave: "Senior .NET Developer", "Senior Angular Developer"
    core_techs = [k for k in keywords if k.lower() in {
        ".net", "c#", "angular", "blazor", "typescript", "react",
        "asp.net", "dotnet", "node", "python", "java"
    }]

    if core_techs:
        # Buscar cada tech core con seniority
        for tech in core_techs[:4]:  # máximo 4 búsquedas
            terms.append(f"{seniority} {tech} Remote")
    else:
        # Fallback: usar las primeras keywords
        terms.append(" ".join(keywords[:3]) + " Remote")

    return terms


def _search_linkedin(keyword: str, time_filter: str = "r2592000") -> list[dict]:
    """
    Ejecuta una búsqueda en LinkedIn Guest Jobs API.
    Trae hasta 100 resultados (4 páginas de 25).
    """
    jobs = []

    session = requests.Session()
    session.headers.update(_HEADERS)

    # Primero visitar la página principal para obtener cookies
    try:
        session.get("https://www.linkedin.com/jobs", timeout=10)
    except Exception:
        pass  # No es crítico

    for page in range(_MAX_PAGES):
        start = page * _JOBS_PER_PAGE
        params = {
            "keywords": keyword,
            "location": "",           # worldwide
            "f_TPR": time_filter,     # último mes
            "f_WT": "2",             # remote
            "start": start,
            "position": 1,
            "pageNum": 0,
        }

        try:
            resp = session.get(_SEARCH_URL, params=params, timeout=15)

            if resp.status_code == 429:
                # Rate limited — parar paginación
                break
            if resp.status_code != 200:
                break

            page_jobs = _parse_search_page(resp.text)
            if not page_jobs:
                break  # No más resultados

            jobs.extend(page_jobs)

            # Si menos de 25 resultados, no hay más páginas
            if len(page_jobs) < _JOBS_PER_PAGE:
                break

        except requests.RequestException:
            break

    return jobs


def _parse_search_page(html: str) -> list[dict]:
    """Parsea una página de resultados de LinkedIn Jobs."""
    soup = BeautifulSoup(html, "html.parser")
    jobs = []

    # LinkedIn usa divs con class "base-card" o "base-search-card"
    cards = soup.select("div.base-search-card, div.base-card")
    if not cards:
        # Fallback: buscar cualquier card con enlace a /jobs/view/
        cards = []
        for link in soup.find_all("a", href=re.compile(r"/jobs/view/")):
            parent = link.find_parent("div", class_=re.compile(r"card|result"))
            if parent and parent not in cards:
                cards.append(parent)

    for card in cards:
        job = _parse_job_card(card)
        if job:
            jobs.append(job)

    return jobs


def _parse_job_card(card) -> dict | None:
    """Parsea una card individual de job de LinkedIn."""
    try:
        # Título + URL
        title_el = card.select_one("a.base-search-card__full-link, a[data-tracking-control-name*='job']")
        if not title_el:
            title_el = card.select_one("h3 a, h2 a, a[href*='/jobs/view/']")
        if not title_el:
            return None

        title = title_el.get_text(strip=True)
        url = title_el.get("href", "").split("?")[0]  # limpiar tracking params
        if not url.startswith("http"):
            url = f"https://www.linkedin.com{url}"

        # Empresa
        company_el = card.select_one("a.hidden-nested-link, span.job-search-card__company-name, h4 a")
        company = company_el.get_text(strip=True) if company_el else "Unknown"

        # Ubicación
        location_el = card.select_one("span.job-search-card__location, span[class*='location']")
        location = location_el.get_text(strip=True) if location_el else "N/A"

        # Fecha de publicación
        date_el = card.select_one("time")
        posted_at = ""
        if date_el:
            posted_at = date_el.get("datetime", "") or date_el.get_text(strip=True)

        # Remoto (detectar del título o ubicación)
        remote = _detect_remote_from_text(title + " " + location)

        return {
            "title": title,
            "company": company,
            "description": title,  # Guest API no trae descripción completa
            "url": url,
            "source": "linkedin",
            "remote": remote,
            "salary": "N/A",
            "location": location,
            "posted_at": posted_at,
            "tags": _extract_tags_from_title(title),
        }

    except Exception:
        return None


def _detect_remote_from_text(text: str) -> str:
    """Detecta si es remoto desde el texto disponible."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["remote", "work from home", "wfh", "anywhere"]):
        return "Remote"
    if any(kw in text_lower for kw in ["hybrid", "partial remote"]):
        return "Hybrid"
    return "Unknown"


def _extract_tags_from_title(title: str) -> list[str]:
    """Extrae tecnologías mencionadas en el título del job."""
    tech_keywords = {
        ".net", "c#", "angular", "react", "typescript", "javascript",
        "python", "java", "node", "blazor", "asp.net", "vue", "svelte",
        "docker", "kubernetes", "aws", "azure", "sql", "mongodb",
        "redis", "graphql", "rest", "api", "microservices",
    }
    title_lower = title.lower()
    found = [t for t in tech_keywords if t in title_lower]
    return found
