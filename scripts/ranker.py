#!/usr/bin/env python3
"""
Job Ranking Engine
====================
Rankea ofertas de trabajo según el perfil del usuario usando scoring ponderado.

Dimensiones de scoring:
  - Stack match: qué tecnologías del job coinciden con el perfil
  - Seniority match: nivel de experiencia requerido
  - Salary match: rango salarial vs expectativa
  - Remote match: modalidad de trabajo
  - Recency: qué tan reciente es la publicación
"""

import re
from datetime import datetime, timedelta


def rank_jobs(jobs: list[dict], profile: dict) -> list[dict]:
    """
    Rankea una lista de jobs contra el perfil del usuario.

    Args:
        jobs: Lista de dicts con datos de jobs normalizados
        profile: Perfil del usuario (profile.yaml)

    Returns:
        Lista ordenada por score descendente, con campo '_score' añadido
    """
    p = profile.get("profile", {})
    weights = p.get("weighting", {
        "stack_match": 0.35,
        "experience_match": 0.15,
        "seniority_match": 0.15,
        "salary_match": 0.15,
        "remote_match": 0.10,
        "recency": 0.10,
    })

    preferred_stack = p.get("preferred_stack", {})
    tech_set = _build_tech_set(preferred_stack)
    preferences = p.get("preferences", {})
    experience = p.get("experience", {})
    experience_history = p.get("experience_history", [])

    scored = []
    for job in jobs:
        score = 0.0

        # 1. Stack match (0-100)
        stack_score = _score_stack_match(job, tech_set)
        score += stack_score * weights.get("stack_match", 0.35)

        # 2. Experience history match (0-100) — compara contra roles anteriores
        exp_score = _score_experience_match(job, experience_history)
        score += exp_score * weights.get("experience_match", 0.15)

        # 3. Seniority match (0-100)
        seniority_score = _score_seniority(job, experience)
        score += seniority_score * weights.get("seniority_match", 0.15)

        # 4. Salary match (0-100)
        salary_score = _score_salary(job, preferences)
        score += salary_score * weights.get("salary_match", 0.15)

        # 5. Remote match (0-100)
        remote_score = _score_remote(job, preferences)
        score += remote_score * weights.get("remote_match", 0.10)

        # 6. Recency (0-100)
        recency_score = _score_recency(job)
        score += recency_score * weights.get("recency", 0.10)

        # Aplicar penalización por exclude_keywords
        penalty = _check_exclusions(job, preferences.get("exclude_keywords", []))
        score = max(0, score - penalty)

        job["_score"] = round(score, 2)
        job["_scores"] = {
            "stack": round(stack_score, 1),
            "experience": round(exp_score, 1),
            "seniority": round(seniority_score, 1),
            "salary": round(salary_score, 1),
            "remote": round(remote_score, 1),
            "recency": round(recency_score, 1),
        }
        scored.append(job)

    # Ordenar descendente por score
    scored.sort(key=lambda j: j["_score"], reverse=True)
    return scored


def _build_tech_set(preferred_stack: dict) -> set:
    """Construye un set con todas las tecnologías del perfil."""
    techs = set()
    for category in ["languages", "frameworks", "databases", "cloud", "tools"]:
        items = preferred_stack.get(category, [])
        techs.update(item.lower() for item in items)
    return techs


def _score_experience_match(job: dict, experience_history: list) -> float:
    """
    Compara el job contra la experiencia laboral previa del usuario.
    Si el job requiere tecnologías que el usuario ya usó en roles anteriores,
    es un mejor match.
    """
    if not experience_history:
        return 50.0  # neutro si no hay historial

    # Construir set de tecnologías usadas en experiencia previa
    exp_techs = set()
    for role in experience_history:
        for tech in role.get("stack", []):
            exp_techs.add(tech.lower())

    if not exp_techs:
        return 50.0

    # Stack del job
    text = (job.get("title", "") + " " + job.get("description", "")).lower()

    matches = sum(1 for tech in exp_techs if tech.lower() in text)
    ratio = matches / len(exp_techs)

    # Bonificación si matchea con tecnologías ya usadas profesionalmente
    if ratio > 0.3:
        return min(100.0, ratio * 120)
    elif ratio > 0.1:
        return 60.0
    else:
        return 30.0


def _score_stack_match(job: dict, tech_set: set) -> float:
    """Calcula qué tanto del stack del job matchea con el perfil."""
    text = (job.get("title", "") + " " + job.get("description", "")).lower()

    matches = sum(1 for tech in tech_set if tech.lower() in text)
    total_techs = len(tech_set)

    if total_techs == 0:
        return 50.0  # neutro si no hay stack definido

    ratio = matches / total_techs
    return min(100.0, ratio * 150)  # bonificación si matchea mucho


def _score_seniority(job: dict, experience: dict) -> float:
    """Evalúa si el nivel de seniority coincide."""
    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    user_level = experience.get("level", "Senior").lower()

    level_map = {
        "junior": 0, "jr": 0, "entry": 0, "trainee": 0,
        "mid": 1, "intermediate": 1, "semi-senior": 1,
        "senior": 2, "sr": 2, "staff": 3, "lead": 4, "principal": 5,
    }

    # Nivel del usuario
    user_lvl = level_map.get(user_level, 2)

    # Detectar nivel en el job
    found_levels = set()
    for word, lvl in level_map.items():
        if re.search(rf"\b{word}\b", text, re.IGNORECASE):
            found_levels.add(lvl)

    if not found_levels:
        return 50.0  # neutro si no especifica

    # Si hay match exacto de seniority
    if user_lvl in found_levels:
        return 100.0

    # Si está cerca (±1 nivel)
    for fl in found_levels:
        if abs(fl - user_lvl) <= 1:
            return 60.0

    return 20.0


def _normalize_to_annual(value: float, mode: str) -> float:
    """
    Normaliza un valor salarial a su equivalente anual.

    Modos soportados:
      - "hourly":   asume 2080 hrs/año (40h/sem * 52 sem)
      - "monthly":  multiplica por 12
      - "annually": sin cambio
    """
    if mode == "hourly":
        return value * 2080
    elif mode == "monthly":
        return value * 12
    else:  # annually (default)
        return value


def _detect_salary_mode(text: str) -> str | None:
    """
    Detecta el modo salarial de una oferta de trabajo.

    Returns: "hourly" | "monthly" | "annually" | None
    """
    text_lower = text.lower()

    # Keywords de modo horario
    if re.search(r"\b(?:per\s*hr|/hr|/hour|per\s*hour|hourly|por\s*hora)\b", text_lower):
        return "hourly"

    # Keywords de modo mensual
    if re.search(r"\b(?:per\s*month|/month|/mo|monthly|por\s*m[ée]s|mensual|/mes)\b", text_lower):
        return "monthly"

    # Keywords de modo anual
    if re.search(r"\b(?:per\s*(?:year|annum)|/year|/yr|annually|annual|por\s*a[ñn]o|/a[ñn]o)\b", text_lower):
        return "annually"

    return None


def _parse_job_salary(salary_str: str) -> tuple:
    """
    Parsea el salario de un job y lo normaliza a anual.

    Returns:
        tuple: (job_min_annual, job_max_annual, salary_display)
               donde salary_display es el string original para mostrar
    """
    if not salary_str or salary_str == "N/A":
        return None, None, salary_str

    text = salary_str

    # Detectar modo del job
    job_mode = _detect_salary_mode(text)

    # Extraer valores numéricos
    # Soporta: "30-45", "30-45/hr", "$30-$45/hour", "80k-150k", "$80k-$150k/yr"
    ranges = re.findall(r"\$?\s*(\d{1,3}(?:,\d{3})*|\d+)(?:\s*[kK])?", text)

    if len(ranges) >= 2:
        # Limpiar comas y convertir
        raw_min = float(ranges[0].replace(",", ""))
        raw_max = float(ranges[1].replace(",", ""))

        # Detectar si el texto original tiene 'k' o 'K'
        has_k = "k" in text.lower()
        if has_k:
            raw_min *= 1000
            raw_max *= 1000
    elif len(ranges) == 1:
        raw_min = raw_max = float(ranges[0].replace(",", ""))
        has_k = "k" in text.lower()
        if has_k:
            raw_min *= 1000
            raw_max *= 1000
    else:
        return None, None, salary_str

    # Si no se pudo detectar el modo, asumir anual (default)
    if not job_mode:
        job_mode = "annually"

    # Normalizar a anual
    annual_min = _normalize_to_annual(raw_min, job_mode)
    annual_max = _normalize_to_annual(raw_max, job_mode)

    return annual_min, annual_max, salary_str


def _score_salary(job: dict, preferences: dict) -> float:
    """
    Evalúa si el salario está dentro del rango esperado,
    soportando modos hourly/monthly/annually.

    Normaliza todo a salario anual para comparar.
    """
    salary_str = job.get("salary", "")
    if not salary_str or salary_str == "N/A":
        return 50.0  # neutro si no hay dato

    # Parsear preferencias del usuario
    salary_mode = preferences.get("salary_mode", "annually")
    user_min = preferences.get("min_salary", 0)
    user_max = preferences.get("max_salary", 200000)

    # Normalizar preferencias del usuario a anual
    user_min_annual = _normalize_to_annual(user_min, salary_mode)
    user_max_annual = _normalize_to_annual(user_max, salary_mode)

    # Parsear y normalizar salario del job a anual
    job_min_annual, job_max_annual, _ = _parse_job_salary(salary_str)

    if job_min_annual is None:
        return 50.0  # no se pudo parsear

    # Comparar en base anual
    if job_min_annual >= user_min_annual and job_max_annual <= user_max_annual:
        return 100.0  # dentro del rango
    if job_max_annual >= user_min_annual and job_min_annual <= user_max_annual:
        return 60.0   # se solapa parcialmente
    if job_max_annual < user_min_annual:
        return 20.0   # está por debajo
    return 80.0       # está por encima (mejor de lo esperado)


def _score_remote(job: dict, preferences: dict) -> float:
    """Evalúa si la modalidad de trabajo es la deseada."""
    remote_only = preferences.get("remote_only", True)
    job_remote = job.get("remote", "Unknown").lower()

    if not remote_only:
        return 100.0

    if "remote" in job_remote:
        return 100.0
    if "hybrid" in job_remote:
        return 50.0
    if "on-site" in job_remote or "onsite" in job_remote:
        return 0.0
    return 50.0  # Unknown


def _score_recency(job: dict) -> float:
    """Evalúa qué tan reciente es la publicación."""
    posted = job.get("posted_at", "")
    if not posted:
        return 50.0

    try:
        if "T" in posted:
            pub_date = datetime.fromisoformat(posted.split(".")[0])
        else:
            pub_date = datetime.strptime(posted[:10], "%Y-%m-%d")
    except (ValueError, IndexError):
        return 50.0

    days_ago = (datetime.now() - pub_date).days
    if days_ago <= 3:
        return 100.0
    if days_ago <= 7:
        return 80.0
    if days_ago <= 14:
        return 60.0
    if days_ago <= 30:
        return 40.0
    return 20.0


def _check_exclusions(job: dict, exclude_keywords: list) -> float:
    """Aplica penalización si el job contiene keywords excluidas."""
    if not exclude_keywords:
        return 0.0

    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    for kw in exclude_keywords:
        if kw.lower() in text:
            return 30.0  # penalización fija por keyword
    return 0.0
