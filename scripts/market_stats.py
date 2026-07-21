#!/usr/bin/env python3
"""
Market Stats Engine
=====================
Analiza los jobs recolectados y genera estadísticas del mercado laboral.

Stats generados:
  - Tecnologías más demandadas
  - Distribución de salarios
  - Remote vs On-site ratio
  - Distribución por fuente
  - Seniority demandado
"""

import re
from collections import Counter
from datetime import datetime
from pathlib import Path


def compute_stats(jobs: list[dict]) -> dict:
    """
    Calcula estadísticas del mercado a partir de los jobs recolectados.

    Args:
        jobs: Lista de dicts con job data

    Returns:
        Dict con estadísticas
    """
    if not jobs:
        return {
            "total": 0,
            "sources": {},
            "top_technologies": [],
            "salary_stats": {},
            "remote_stats": {"remote": 0, "hybrid": 0, "onsite": 0, "unknown": 0},
            "seniority_stats": {},
            "top_companies": [],
            "generated_at": datetime.now().isoformat(),
        }

    sources = Counter()
    all_techs = Counter()
    remote_stats = {"remote": 0, "hybrid": 0, "onsite": 0, "unknown": 0}
    seniority_stats = Counter()
    companies = Counter()
    salaries = []
    titles = []

    # Tecnologías conocidas para detectar
    KNOWN_TECHS = [
        ".net", "c#", "csharp", "asp.net", "blazor", "f#",
        "angular", "typescript", "javascript", "react", "vue", "node",
        "python", "java", "go", "golang", "rust", "c++",
        "postgresql", "postgres", "sql server", "mysql", "mongodb", "redis",
        "azure", "aws", "gcp", "google cloud",
        "docker", "kubernetes", "k8s", "terraform", "github actions",
        "microservices", "clean architecture", "ddd", "cqrs", "event-driven",
        "rest", "graphql", "grpc",
    ]

    SENIORITY_KEYWORDS = {
        "junior": "Junior", "jr": "Junior", "entry": "Junior", "trainee": "Junior",
        "mid": "Mid", "intermediate": "Mid", "semi-senior": "Mid",
        "senior": "Senior", "sr": "Senior", "staff": "Staff",
        "lead": "Lead", "principal": "Principal", "head": "Lead",
    }

    for job in jobs:
        # Fuentes
        source = job.get("source", "unknown")
        sources[source] += 1

        # Empresas
        company = job.get("company", "Unknown")
        if company and company != "Unknown":
            companies[company] += 1

        # Tecnologías (de descripción + título + tags)
        text = (
            job.get("title", "") + " " +
            job.get("description", "") + " " +
            " ".join(job.get("tags", []))
        ).lower()

        for tech in KNOWN_TECHS:
            if re.search(rf"\b{re.escape(tech)}\b", text):
                all_techs[tech] += 1

        # Remote
        remote = job.get("remote", "").lower()
        if "remote" in remote:
            remote_stats["remote"] += 1
        elif "hybrid" in remote:
            remote_stats["hybrid"] += 1
        elif "on-site" in remote or "onsite" in remote:
            remote_stats["onsite"] += 1
        else:
            remote_stats["unknown"] += 1

        # Seniority
        title_lower = job.get("title", "").lower()
        for keyword, level in SENIORITY_KEYWORDS.items():
            if re.search(rf"\b{keyword}\b", title_lower):
                seniority_stats[level] += 1
                break

        # Salarios
        salary = job.get("salary", "")
        if salary and salary != "N/A":
            salaries.append(salary)

        # Títulos (para nubes de palabras)
        titles.append(job.get("title", ""))

    # Top tecnologías
    top_techs = [{"tech": t.replace("#", ".net" if t == ".net" else t), "count": c}
                 for t, c in all_techs.most_common(15) if c > 0]

    # Top empresas
    top_companies = [{"company": c, "count": cnt}
                     for c, cnt in companies.most_common(10)]

    # Total remoto
    total_remote = sum(remote_stats.values())
    remote_pct = (remote_stats["remote"] / total_remote * 100) if total_remote else 0
    hybrid_pct = (remote_stats["hybrid"] / total_remote * 100) if total_remote else 0
    onsite_pct = (remote_stats["onsite"] / total_remote * 100) if total_remote else 0

    return {
        "total": len(jobs),
        "sources": dict(sources),
        "top_technologies": top_techs,
        "remote_stats": {
            "remote": remote_stats["remote"],
            "hybrid": remote_stats["hybrid"],
            "onsite": remote_stats["onsite"],
            "unknown": remote_stats["unknown"],
            "remote_pct": round(remote_pct, 1),
            "hybrid_pct": round(hybrid_pct, 1),
            "onsite_pct": round(onsite_pct, 1),
        },
        "seniority_stats": dict(seniority_stats),
        "top_companies": top_companies,
        "salary_samples": len(salaries),
        "generated_at": datetime.now().isoformat(),
    }


def format_stats_report(stats: dict) -> str:
    """
    Genera un reporte Markdown de las estadísticas.

    Args:
        stats: Dict de estadísticas (de compute_stats)

    Returns:
        String con reporte Markdown
    """
    lines = [
        "# 📊 Market Stats",
        "",
        f"Generado: {stats.get('generated_at', 'N/A')[:10]}",
        f"",
        f"## 📦 Overview",
        f"",
        f"| Metric | Value |",
        f"|---|---|",
        f"| **Total Jobs** | {stats['total']} |",
        f"| **Salary Sample** | {stats['salary_samples']} jobs |",
        f"| **Remote** | {stats['remote_stats']['remote']} ({stats['remote_stats']['remote_pct']}%) |",
        f"| **Hybrid** | {stats['remote_stats']['hybrid']} ({stats['remote_stats']['hybrid_pct']}%) |",
        f"| **On-site** | {stats['remote_stats']['onsite']} ({stats['remote_stats']['onsite_pct']}%) |",
        f"",
        f"## 🔥 Top Technologies",
        f"",
        f"| # | Technology | Mentions |",
        f"|---|---|---|",
    ]

    for i, tech in enumerate(stats.get("top_technologies", [])[:10], 1):
        lines.append(f"| {i} | {tech['tech']} | {tech['count']} |")

    lines.extend([
        "",
        f"## 🏢 Top Companies Hiring",
        f"",
        f"| # | Company | Jobs |",
        f"|---|---|---|",
    ])

    for i, company in enumerate(stats.get("top_companies", [])[:10], 1):
        lines.append(f"| {i} | {company['company']} | {company['count']} |")

    lines.extend([
        "",
        f"## 📰 Sources Distribution",
        f"",
    ])

    for source, count in stats.get("sources", {}).items():
        pct = (count / stats["total"] * 100) if stats["total"] else 0
        lines.append(f"- **{source}**: {count} ({pct:.0f}%)")

    return "\n".join(lines)
