#!/usr/bin/env python3
"""
Job Deduplicator
==================
Elimina jobs duplicados basado en título normalizado + empresa.

Estrategia:
  - Normaliza títulos (minúsculas, remueve puntuación, remueve palabras genéricas)
  - Agrupa por (título_normalizado, empresa_normalizada)
  - Si hay duplicados, conserva el de mayor score o el más reciente
"""

import re
from difflib import SequenceMatcher


# Palabras genéricas a ignorar en títulos
GENERIC_WORDS = {
    "senior", "sr", "jr", "junior", "mid", "mid-level", "level",
    "staff", "lead", "principal", "remote", "full-time", "part-time",
    "contract", "freelance", "temporary", "permanent",
    "experienced", "software", "engineer", "developer", "engineerring",
    "i", "ii", "iii", "iv", "v",
}


def normalize_title(title: str) -> str:
    """Normaliza un título para comparación."""
    if not title:
        return ""

    title = title.lower()
    # Remover puntuación
    title = re.sub(r"[^\w\s]", " ", title)
    # Remover palabras genéricas
    words = [w for w in title.split() if w not in GENERIC_WORDS and len(w) > 1]
    # Ordenar palabras para que "Developer Senior" == "Senior Developer"
    words.sort()
    return " ".join(words)


def normalize_company(company: str) -> str:
    """Normaliza nombre de empresa para comparación."""
    if not company:
        return ""

    company = company.lower().strip()
    # Remover artículos y sufijos legales
    company = re.sub(r"\b(the|a|an|inc|llc|ltd|corp|gmbh|s.a|s.a.s|s.l)\b", "", company)
    company = re.sub(r"[^\w\s]", "", company)
    return " ".join(company.split())


def are_similar(title1: str, title2: str, threshold: float = 0.80) -> bool:
    """Compara dos títulos usando similitud de secuencia."""
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    if not norm1 or not norm2:
        return False
    return SequenceMatcher(None, norm1, norm2).ratio() >= threshold


def deduplicate(jobs: list[dict]) -> list[dict]:
    """
    Deduplica una lista de jobs.

    Estrategia:
      1. Agrupa por (título_normalizado, empresa_normalizada)
      2. De cada grupo, conserva el de mayor score (si están rankeados)
         o el primero (si no)

    Args:
        jobs: Lista de dicts con job data

    Returns:
        Lista deduplicada
    """
    seen = {}  # key -> mejor job

    for job in jobs:
        title = job.get("title", "")
        company = job.get("company", "Unknown")

        norm_title = normalize_title(title)
        norm_company = normalize_company(company)
        key = (norm_title, norm_company)

        if key in seen:
            existing = seen[key]
            # Conservar el de mayor score
            existing_score = existing.get("_score", 0) or 0
            current_score = job.get("_score", 0) or 0
            if current_score > existing_score:
                seen[key] = job
            # Si no hay score, conservar el más completo
            elif current_score == existing_score:
                existing_len = len(existing.get("description", ""))
                current_len = len(job.get("description", ""))
                if current_len > existing_len:
                    seen[key] = job
        else:
            seen[key] = job

    # También verificar títulos similares (misma empresa, título parecido)
    # Ej: "Senior .NET Developer" vs ".NET Developer Senior"
    items = list(seen.items())
    final_jobs = []
    used_companies = {}

    for key, job in items:
        norm_company = key[1]
        norm_title = key[0]

        if norm_company in used_companies:
            # Verificar si es similar a algún job ya agregado
            is_dup = False
            for existing_title in used_companies[norm_company]:
                if are_similar(norm_title, existing_title):
                    is_dup = True
                    break
            if is_dup:
                continue

        used_companies.setdefault(norm_company, []).append(norm_title)
        final_jobs.append(job)

    return final_jobs
