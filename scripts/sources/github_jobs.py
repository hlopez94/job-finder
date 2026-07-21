#!/usr/bin/env python3
"""
GitHub Jobs Scraper
====================
Busca ofertas de trabajo publicadas como GitHub Issues
con labels específicas (job, hire, hiring, job-posting).

Usa la GitHub API v4 (GraphQL) con autenticación por token.
"""

import requests
import re
from datetime import datetime, timedelta


def fetch_github_jobs(config: dict, profile: dict) -> list[dict]:
    """
    Busca GitHub Issues con labels de trabajo.

    Args:
        config: Config del usuario (contiene github.token)
        profile: Perfil del usuario (para filtrar por stack)

    Returns:
        Lista de dicts con job data normalizada
    """
    token = config.get("github", {}).get("token", "")
    if not token or token == "ghp_xxxxxxxxxxxxxxxxxxxx":
        print("   │   ⚠️ GitHub token no configurado")
        return []

    lookback_days = config.get("general", {}).get("lookback_days", 30)
    since_date = (datetime.now() - timedelta(days=lookback_days)).isoformat() + "Z"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Labels relacionadas a trabajo
    job_labels = ["job", "hire", "hiring", "job-posting", "remote-job"]

    all_issues = []
    for label in job_labels:
        url = "https://api.github.com/search/issues"
        query = f'label:"{label}" is:open is:issue updated:>={since_date[:10]}'
        params = {"q": query, "sort": "updated", "order": "desc", "per_page": 50}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code != 200:
                continue

            data = resp.json()
            for item in data.get("items", []):
                job = _parse_github_issue(item, label)
                if job:
                    all_issues.append(job)

        except requests.RequestException as e:
            print(f"   │   ⚠️ Error fetching label '{label}': {e}")

    return all_issues


def _parse_github_issue(issue: dict, label: str) -> dict | None:
    """Convierte un GitHub Issue en estructura de job normalizada."""
    body = issue.get("body", "") or ""

    # Extraer empresa del título o body (convenciones comunes)
    company = _extract_company(issue.get("title", ""), body)

    # Extraer salario (regex simple)
    salary = _extract_salary(issue.get("title", "") + " " + body)

    # Remoto
    remote = _detect_remote(issue.get("title", "") + " " + body, label)

    return {
        "title": issue.get("title", "Untitled Position"),
        "company": company,
        "description": body[:1000] if body else "",
        "url": issue.get("html_url", ""),
        "source": "github",
        "remote": remote,
        "salary": salary,
        "location": _extract_location(body),
        "posted_at": issue.get("created_at", ""),
        "labels": [l["name"] for l in issue.get("labels", [])],
        "repo_url": issue.get("repository_url", "").replace("https://api.github.com/repos/", "https://github.com/"),
    }


def _extract_company(title: str, body: str) -> str:
    """Intenta extraer nombre de empresa del título o body."""
    text = f"{title}\n{body[:500]}"

    # Formatos comunes: "Company: XYZ", "at XYZ", "[Company]"
    patterns = [
        r"(?:at|@|for|—|-)\s*@?([A-Z][A-Za-z0-9\s&.]+?)(?:\s*(?:is\s+(?:looking|hiring)|seeks?|has\s+opened))",
        r"^(?:\[|\()?([A-Z][A-Za-z0-9\s&.]+?)(?:\]|\))?\s*(?:is|are)\s+(?:hiring|looking)",
        r"(?:Company|Employer):\s*([A-Z][A-Za-z0-9\s&.]+)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    return "Unknown Company"


def _extract_salary(text: str) -> str:
    """Extrae rango salarial del texto."""
    patterns = [
        r"\$\s*(\d{2,3}[kK]?)\s*[-–to]*\s*\$?\s*(\d{2,3}[kK]?)",
        r"(?:salary|pay|compensation)[:\s]*\$?\s*(\d[\d,]+)\s*[-–to]*\s*\$?\s*(\d[\d,]*)",
        r"\$\s*(\d{1,3}(?:,\d{3})+)\s*[-–to]*\s*\$?\s*(\d{1,3}(?:,\d{3})+)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return f"${m.group(1)} - ${m.group(2)}"

    return "N/A"


def _detect_remote(text: str, label: str) -> str:
    """Detecta si la posición es remota."""
    if "remote" in label.lower():
        return "Remote"

    remote_keywords = [
        r"\bremote\b", r"\b100%\s*remote\b", r"\bfully\s*remote\b",
        r"\bwork\s*from\s*home\b", r"\bwfh\b", r"\banywhere\b",
    ]
    for pat in remote_keywords:
        if re.search(pat, text, re.IGNORECASE):
            return "Remote"

    if re.search(r"\bon.?site\b|\bhybrid\b|\blocal\b|\brelocat", text, re.IGNORECASE):
        return "On-site / Hybrid"

    return "Unknown"


def _extract_location(body: str) -> str:
    """Extrae ubicación del body."""
    patterns = [
        r"(?:location|loc|based|office)[:\s]+([A-Za-z\s,.-]+?)(?:\n|\.|,|\s*(?:Salary|Remote|Stack))",
    ]
    for pat in patterns:
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            loc = m.group(1).strip()
            if len(loc) > 3 and len(loc) < 60:
                return loc
    return "N/A"
