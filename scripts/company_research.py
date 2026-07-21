#!/usr/bin/env python3
"""
Company Research + Interview Prep
===================================
Cuando el usuario selecciona un job que le interesa, este módulo:
  1. Busca información de la empresa (vía web scraping)
  2. Genera un resumen ejecutivo
  3. Prepara recomendaciones para la entrevista basadas en el stack
"""

import re
import json
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT_DIR / "output" / ".company_cache"


def ensure_cache():
    """Asegura que exista el directorio de cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(company: str) -> Path:
    """Path para cache de empresa."""
    safe_name = re.sub(r"[^\w]", "_", company.lower())
    return CACHE_DIR / f"{safe_name}.json"


def _load_cache(company: str) -> dict | None:
    """Carga datos de empresa del cache."""
    path = _cache_path(company)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Cache válido por 7 días
        cached_date = datetime.fromisoformat(data.get("_cached_at", "2000-01-01"))
        if (datetime.now() - cached_date).days < 7:
            return data
    return None


def _save_cache(company: str, data: dict):
    """Guarda datos de empresa en cache."""
    data["_cached_at"] = datetime.now().isoformat()
    with open(_cache_path(company), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def research_company(company: str, job_title: str = "", tech_stack: list = None) -> dict:
    """
    Investiga una empresa y genera recomendaciones.

    Args:
        company: Nombre de la empresa
        job_title: Título del puesto (para contexto)
        tech_stack: Stack tecnológico del puesto

    Returns:
        Dict con: company_info, interview_tips, market_context
    """
    # Intentar cache
    cached = _load_cache(company)
    if cached:
        cached["_from_cache"] = True
        return cached

    result = {
        "company": company,
        "company_info": _scrape_company_info(company),
        "interview_tips": _generate_interview_tips(tech_stack or [], job_title),
        "market_context": _get_market_context(company, job_title),
        "generated_at": datetime.now().isoformat(),
    }

    _save_cache(company, result)
    return result


def _scrape_company_info(company: str) -> dict:
    """Scrapea información básica de la empresa desde la web."""
    info = {
        "name": company,
        "description": "",
        "website": "",
        "industry": "",
        "headquarters": "",
        "size": "",
        "sources": [],
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    }

    # Intentar buscar en Crunchbase (público)
    try:
        search_url = f"https://www.crunchbase.com/organization/{quote_plus(company.lower().replace(' ', '-'))}"
        info["sources"].append({"type": "crunchbase", "url": search_url})
    except:
        pass

    # Intentar buscar en Google Finance
    try:
        search_url = f"https://www.google.com/search?q={quote_plus(company)}+company+overview"
        resp = requests.get(search_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            # Extraer snippet de descripción
            snippets = re.findall(r'<span[^>]*>(.*?)</span>', resp.text)
            for snippet in snippets[:5]:
                if len(snippet) > 50 and "company" in snippet.lower():
                    info["description"] = snippet[:300]
                    break
            info["sources"].append({"type": "google", "url": search_url})
    except:
        pass

    # Intentar Glassdoor
    try:
        gd_url = f"https://www.glassdoor.com/Reviews/{quote_plus(company)}-Reviews-E{hash(company) % 1000000}.htm"
        info["sources"].append({"type": "glassdoor", "url": gd_url})
    except:
        pass

    # LinkedIn company page
    try:
        li_url = f"https://www.linkedin.com/company/{quote_plus(company.lower().replace(' ', '-'))}"
        info["sources"].append({"type": "linkedin", "url": li_url})
    except:
        pass

    return info


def _generate_interview_tips(tech_stack: list, job_title: str) -> list:
    """Genera tips de entrevista basados en el stack tecnológico."""
    tips = []

    # Tips generales
    tips.append({
        "category": "General",
        "tips": [
            "Investigá la empresa: misión, valores, productos, cultura",
            "Prepará 3 preguntas inteligentes sobre el equipo y la tecnología",
            "Tené ejemplos concretos de proyectos anteriores usando STAR (Situación, Tarea, Acción, Resultado)",
            "Prepará tu pitch de 30 segundos: quién sos, qué hacés, qué buscás",
        ]
    })

    # Tips específicos por tecnología
    tech_lower = [t.lower() for t in (tech_stack or [])]

    if any(t in tech_lower for t in [".net", "c#", "asp.net", "blazor"]):
        tips.append({
            "category": ".NET / C#",
            "tips": [
                "Repasar Clean Architecture, DDD, CQRS patrones",
                "Preparar ejemplos de async/await, LINQ, Dependency Injection",
                "Estar al día con .NET 8/9 features (AOT, NativeAOT, minimal APIs)",
                "Repasar Entity Framework Core vs Dapper tradeoffs",
            ]
        })

    if any(t in tech_lower for t in ["angular", "typescript"]):
        tips.append({
            "category": "Angular / TypeScript",
            "tips": [
                "Repasar Signals, OnPush change detection, zoneless Angular",
                "Conocer standalone components, new control flow (@if/@for)",
                "Preparar ejemplos de RxJS y manejo de estado",
                "Hablar de accesibilidad (WCAG) y performance (Core Web Vitals)",
            ]
        })

    if any(t in tech_lower for t in ["azure", "aws", "cloud"]):
        tips.append({
            "category": "Cloud",
            "tips": [
                "Repasar arquitectura serverless vs containers vs VMs",
                "Preparar ejemplos de CI/CD pipelines",
                "Conocer patrones de resiliencia (Circuit Breaker, Retry)",
                "Hablar de costos en cloud y optimización (FinOps)",
            ]
        })

    if any(t in tech_lower for t in ["postgresql", "sql server", "database", "redis"]):
        tips.append({
            "category": "Bases de Datos",
            "tips": [
                "Repasar normalización, indexing, query optimization",
                "Preparar ejemplos de migraciones zero-downtime",
                "Conocer diferencias entre SQL y NoSQL (cuándo usar cada uno)",
                "Hablar de multi-tenant data isolation strategies",
            ]
        })

    if any(t in tech_lower for t in ["docker", "kubernetes", "k8s", "terraform"]):
        tips.append({
            "category": "DevOps / Infra",
            "tips": [
                "Repasar Kubernetes concepts: pods, services, ingress, HPA",
                "Conocer GitOps (ArgoCD, Flux) y despliegues declarativos",
                "Preparar ejemplos de IaC con Terraform o Bicep",
                "Hablar de monitoreo y observabilidad (OpenTelemetry, Prometheus)",
            ]
        })

    return tips


def _get_market_context(company: str, job_title: str) -> dict:
    """Obtiene contexto de mercado para la empresa/rol."""
    return {
        "similar_companies": [],
        "market_trends": [
            "Alta demanda de perfiles .NET/Angular en el mercado",
            "Salarios en aumento para posiciones 100% remotas",
            "Empresas buscando Senior+ con experiencia en Clean Architecture",
        ],
    }


def generate_report(job: dict) -> str:
    """
    Genera un reporte Markdown completo con company research + interview prep.

    Args:
        job: Job data dict

    Returns:
        String con reporte en Markdown
    """
    company = job.get("company", "Unknown")
    title = job.get("title", "Unknown Position")
    tech_stack = job.get("tags", [])
    # También extraer stack de la descripción
    desc = job.get("description", "")

    research = research_company(company, title, tech_stack)

    lines = [
        f"# 📋 Company Research: {company}",
        f"",
        f"**Job:** {title}",
        f"**Score:** {job.get('_score', 'N/A'):.0f}/100" if job.get('_score') else "",
        f"**Salary:** {job.get('salary', 'N/A')}",
        f"**Link:** [{job.get('url', '#')}]({job.get('url', '#')})",
        f"",
        f"---",
        f"",
        f"## 🏢 Sobre {company}",
        f"",
        f"{research['company_info'].get('description', 'Información no disponible. Revisá los sources abajo.')}",
        f"",
        f"**Sources:**",
    ]

    for src in research["company_info"].get("sources", []):
        lines.append(f"- [{src['type']}]({src['url']})")

    lines.extend(["", "---", "", "## 🎯 Interview Tips", ""])

    for category in research.get("interview_tips", []):
        lines.append(f"### {category['category']}")
        lines.append("")
        for tip in category["tips"]:
            lines.append(f"- {tip}")
        lines.append("")

    lines.extend(["---", "", "## 📊 Market Context", ""])
    for trend in research.get("market_context", {}).get("market_trends", []):
        lines.append(f"- {trend}")

    lines.extend(["", "---", "", f"*Reporte generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}*"])

    return "\n".join(lines)


if __name__ == "__main__":
    """CLI para investigar una empresa."""
    import argparse
    parser = argparse.ArgumentParser(description="Company Research + Interview Prep")
    parser.add_argument("company", help="Nombre de la empresa")
    parser.add_argument("--title", help="Título del puesto", default="")
    parser.add_argument("--stack", nargs="*", help="Stack tecnológico", default=[])

    args = parser.parse_args()

    result = research_company(args.company, args.title, args.stack)
    print(json.dumps(result, indent=2, ensure_ascii=False))
