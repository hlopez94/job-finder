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


def _score_salary(job: dict, preferences: dict) -> float:
    """Evalúa si el salario está dentro del rango esperado."""
    salary_str = job.get("salary", "")
    if not salary_str or salary_str == "N/A":
        return 50.0  # neutro si no hay dato

    min_salary = preferences.get("min_salary_usd", 0)
    max_salary = preferences.get("max_salary_usd", 200000)

    ranges = re.findall(r"\$?\s*(\d{2,3})[kK]?", salary_str)
    if len(ranges) >= 2:
        job_min = int(ranges[0]) * 1000
        job_max = int(ranges[1]) * 1000
    elif len(ranges) == 1:
        job_min = job_max = int(ranges[0]) * 1000
    else:
        return 50.0

    # Si el rango del job está dentro de la expectativa
    if job_min >= min_salary and job_max <= max_salary:
        return 100.0
    # Si se solapa parcialmente
    if job_max >= min_salary and job_min <= max_salary:
        return 60.0
    # Si está por debajo
    if job_max < min_salary:
        return 20.0
    # Si está por encima
    return 80.0


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
