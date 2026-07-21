#!/usr/bin/env python3
"""
LinkedIn Jobs Scraper (via MCP)
==================================
Conector para el MCP Server linkedin-scraper.
Requiere que el MCP server linkedin-scraper esté configurado y ejecutándose.

Configuración esperada en config.yaml:
  linkedin:
    email: "tu-email@example.com"
    password: "tu-contraseña"
    search_keywords: [".NET", "Angular", "Senior", "Remote"]
    locations: ["Worldwide", "United States", "Europe"]
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta


def fetch_linkedin_jobs(config: dict, profile: dict) -> list[dict]:
    """
    Busca ofertas en LinkedIn usando el MCP Server linkedin-scraper.

    Args:
        config: Config del usuario (linkedin.email, linkedin.password, etc.)
        profile: Perfil del usuario (para filtrar por stack)

    Returns:
        Lista de dicts con job data normalizada
    """
    linkedin_config = config.get("linkedin", {})
    email = linkedin_config.get("email", "")
    password = linkedin_config.get("password", "")

    if not email or not password:
        print("       ⚠️ LinkedIn: email/password no configurados")
        return []

    search_keywords = linkedin_config.get(
        "search_keywords",
        profile.get("profile", {}).get("preferred_stack", {}).get("languages", [])
        + [profile.get("profile", {}).get("experience", {}).get("level", "Senior")]
    )

    locations = linkedin_config.get("locations", ["Worldwide"])
    lookback_days = config.get("general", {}).get("lookback_days", 30)

    all_jobs = []

    for keyword in search_keywords:
        for location in locations:
            try:
                jobs = _call_linkedin_mcp(keyword, location, email, password)
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"       ⚠️ Error LinkedIn '{keyword}' / '{location}': {e}")

    # Normalizar y deduplicar
    seen_urls = set()
    normalized = []
    for job in all_jobs:
        url = job.get("url", job.get("link", ""))
        if url in seen_urls:
            continue
        seen_urls.add(url)

        normalized.append({
            "title": job.get("title", "Untitled"),
            "company": job.get("company", job.get("employer", "Unknown")),
            "description": (job.get("description") or job.get("summary") or "")[:1000],
            "url": url,
            "source": "linkedin",
            "remote": _detect_remote(job),
            "salary": job.get("salary", job.get("salaryRange", "N/A")),
            "location": job.get("location", "N/A"),
            "posted_at": job.get("postedAt", job.get("date", "")),
        })

    return normalized


def _call_linkedin_mcp(keyword: str, location: str, email: str, password: str) -> list[dict]:
    """
    Ejecuta el MCP server linkedin-scraper como subprocess.
    Nota: Esta es una implementación de ejemplo.
    En producción, usarías el MCP client SDK en vez de subprocess.
    """
    # Placeholder: Aquí iría la llamada real al MCP server
    # Por ahora retorna vacío hasta que el MCP server esté configurado
    print(f"       ℹ️  LinkedIn MCP para '{keyword}' en '{location}' — pendiente de configuración MCP")

    # Ejemplo de implementación futura:
    # result = subprocess.run(
    #     ["npx", "@anthropic/claude-code", "mcp", "linkedin-scraper", "search",
    #      "--keyword", keyword,
    #      "--location", location,
    #      "--email", email,
    #      "--password", password],
    #     capture_output=True, text=True, timeout=30
    # )
    # return json.loads(result.stdout)

    return []


def _detect_remote(job: dict) -> str:
    """Detecta si la posición es remota desde el job de LinkedIn."""
    text = json.dumps(job).lower()
    if any(kw in text for kw in ["remote", "work from home", "wfh", "anywhere"]):
        return "Remote"
    if any(kw in text for kw in ["hybrid", "partial remote"]):
        return "Hybrid"
    if any(kw in text for kw in ["on-site", "onsite", "in office"]):
        return "On-site"
    return "Unknown"
