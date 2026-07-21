#!/usr/bin/env python3
"""
Prepara resultados de job scraping para análisis AI de geo-compatibilidad.
Lee results.json y produce un resumen simplificado para que el AI analice.

Uso:
    python scripts/prepare-geo-analysis.py [fecha]
    python scripts/prepare-geo-analysis.py 2026-07-21

Output: output/{fecha}/geo-analysis-input.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


def prepare_analysis(run_date: str = None) -> dict:
    """Prepara datos para análisis AI de geo-compatibilidad."""
    if not run_date:
        run_date = datetime.now().strftime("%Y-%m-%d")

    results_path = OUTPUT_DIR / run_date / "results.json"
    if not results_path.exists():
        print(f"[ERROR] No se encontro {results_path}")
        sys.exit(1)

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Preparar resumen para AI
    analysis_input = {
        "run_date": run_date,
        "profile": data.get("profile", "N/A"),
        "total_jobs": data.get("total_ranked", 0),
        "instructions": (
            "Analiza cada job para determinar si es compatible con un candidato "
            "remoto desde Argentina (LATAM). Para cada job, clasifícalo como:\n"
            "- ✅ APLICAR: Geo-compatible (LATAM/Worldwide/Argentina)\n"
            "- ⚠️ REVISAR: No hay info clara, necesita verificación\n"
            "- ❌ DESCARTAR: Geo-restringido (US-only, EU-only, etc.)\n\n"
            "Señales de geo-restricción:\n"
            "- location contiene 'United States' o ciudad de US → probablemente US-only\n"
            "- location contiene 'Europe', 'UK', 'Germany' → probablemente EU-only\n"
            "- En job page: 'authorized to work in US', 'US work authorization'\n"
            "- En job page: 'within Canada and the US'\n\n"
            "Señales de compatibilidad LATAM:\n"
            "- location contiene 'Worldwide', 'Global', 'Anywhere', 'Remote'\n"
            "- location contiene 'LATAM', 'Latin America', 'Argentina'\n"
            "- En job page: 'open to worldwide candidates'\n"
        ),
        "jobs": []
    }

    for job in data.get("top_results", []):
        analysis_input["jobs"].append({
            "rank": job.get("rank"),
            "title": job.get("title", ""),
            "company": job.get("company", "Unknown"),
            "score": job.get("score", 0),
            "location": job.get("location", "N/A"),
            "remote": job.get("remote", "Unknown"),
            "source": job.get("source", "unknown"),
            "url": job.get("url", ""),
            "salary": job.get("salary", "N/A"),
            "posted_at": job.get("posted_at", ""),
            # Indicadores rápidos para el AI
            "location_hint": _classify_location(job.get("location", "")),
        })

    # Save
    output_path = OUTPUT_DIR / run_date / "geo-analysis-input.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis_input, f, indent=2, ensure_ascii=False)

    print(f"[OK] Analisis preparado: {output_path}")
    print(f"     Jobs para analizar: {len(analysis_input['jobs'])}")

    # Resumen rapido
    hints = {}
    for j in analysis_input["jobs"]:
        h = j["location_hint"]
        hints[h] = hints.get(h, 0) + 1
    print(f"     Location hints: {hints}")

    return analysis_input


def _classify_location(location: str) -> str:
    """Clasificación rápida de ubicación para AI."""
    loc = location.lower()

    # LATAM / Worldwide
    if any(kw in loc for kw in ["worldwide", "global", "anywhere", "latam", "latin america", "south america", "argentina"]):
        return "latam-friendly"

    # US
    us_cities = ["united states", "new york", "san francisco", "los angeles", "chicago",
                 "seattle", "austin", "boston", "denver", "miami", "orlando", "tampa",
                 "dallas", "houston", "atlanta", "phoenix", "philadelphia", "carmel",
                 "remote (us", "us remote"]
    if any(c in loc for c in us_cities):
        return "us-likely"

    # Europe
    eu_cities = ["london", "berlin", "amsterdam", "paris", "munich", "dublin",
                 "europe", "united kingdom", "germany", "netherlands", "france", "spain"]
    if any(c in loc for c in eu_cities):
        return "eu-likely"

    # Empty / N/A
    if not location or location in ["n/a", "unknown", ""]:
        return "unknown"

    return "needs-review"


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else None
    prepare_analysis(date)
