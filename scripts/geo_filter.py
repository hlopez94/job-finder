#!/usr/bin/env python3
"""
Geo-Filter para Job Finder
============================
Filtra trabajos por compatibilidad geográfica con Argentina (LATAM).

Uso:
    python scripts/geo-filter.py [fecha]
    python scripts/geo-filter.py 2026-07-21

Output: output/{fecha}/geo-filtered.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


def geo_filter_jobs(jobs: list[dict]) -> tuple[list[dict], dict]:
    """
    Filtra lista de jobs por compatibilidad LATAM.
    
    Args:
        jobs: Lista de jobs rankeados
        
    Returns:
        Tuple de (jobs_filtrados, estadisticas)
    """
    print(f"Jobs totales para geo-filter: {len(jobs)}")
    
    # Clasificar cada job
    classified = {"latam": [], "maybe": [], "us_only": [], "other": []}
    
    for job in jobs:
        location = job.get("location", "")
        classification = _classify_geo(location)
        job["_geo_classification"] = classification
        classified[classification].append(job)
    
    stats = {
        "latam": len(classified["latam"]),
        "maybe": len(classified["maybe"]),
        "us_only": len(classified["us_only"]),
        "other": len(classified["other"]),
    }
    
    # Crear output filtrado (solo LATAM + maybe)
    filtered_jobs = classified["latam"] + classified["maybe"]
    
    print(f"  LATAM-friendly: {stats['latam']}")
    print(f"  Maybe (needs review): {stats['maybe']}")
    print(f"  US-only: {stats['us_only']}")
    print(f"  Other region: {stats['other']}")
    
    return filtered_jobs, stats


def geo_filter(run_date: str = None) -> dict:
    """Filtra jobs por compatibilidad LATAM."""
    if not run_date:
        run_date = datetime.now().strftime("%Y-%m-%d")

    results_path = OUTPUT_DIR / run_date / "results.json"
    if not results_path.exists():
        print(f"[ERROR] No se encontro {results_path}")
        sys.exit(1)

    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_jobs = data.get("top_results", [])
    filtered_jobs, stats = geo_filter_jobs(all_jobs)

    output = {
        "run_date": run_date,
        "profile": data.get("profile", "N/A"),
        "total_before_filter": len(all_jobs),
        "total_after_filter": len(filtered_jobs),
        "filter_stats": stats,
        "top_results": filtered_jobs,
    }

    # Guardar
    output_path = OUTPUT_DIR / run_date / "geo-filtered.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Geo-filter guardado: {output_path}")
    print(f"     Jobs filtrados: {len(filtered_jobs)} de {len(all_jobs)}")

    # Mostrar top LATAM jobs
    if stats["latam"] > 0:
        latam_jobs = [j for j in filtered_jobs if j.get("_geo_classification") == "latam"]
        print("\nJobs LATAM-friendly (top 5):")
        for j in latam_jobs[:5]:
            print(f"  {j.get('rank')}: {j.get('title')[:50]} | {j.get('location')}")

    return output


def _classify_geo(location: str) -> str:
    """Clasifica ubicacion para geo-filter."""
    loc = location.lower()

    # LATAM / Worldwide - CLARAMENTE COMPATIBLE
    latam_keywords = [
        "worldwide", "global", "anywhere", "remote (worldwide)",
        "latam", "latin america", "south america", "argentina",
        "brazil", "brazilian", "mexico", "colombia", "chile",
        "remote (global)", "global remote", "worldwide remote"
    ]
    if any(kw in loc for kw in latam_keywords):
        return "latam"

    # US-only - CLARAMENTE NO COMPATIBLE
    us_keywords = [
        "united states", "us only", "usa only", "us-based",
        "us remote", "remote (us", "within the us",
        "new york", "san francisco", "los angeles", "chicago",
        "seattle", "austin", "boston", "denver", "miami", "orlando",
        "tampa", "dallas", "houston", "atlanta", "phoenix",
        "philadelphia", "carmel", "paraná"  # Orlando location
    ]
    if any(kw in loc for kw in us_keywords):
        return "us_only"

    # Europe - CLARAMENTE NO COMPATIBLE
    eu_keywords = [
        "europe", "united kingdom", "uk only", "germany", "german",
        "netherlands", "dutch", "france", "french", "spain", "spanish",
        "london", "berlin", "amsterdam", "paris", "munich", "dublin",
        "remote (eu", "eu remote", "europe remote"
    ]
    if any(kw in loc for kw in eu_keywords):
        return "other"

    # Empty / N/A - PODRIA SER REMOTO
    if not location or location in ["n/a", "unknown", ""]:
        return "maybe"

    # Remote without region qualifier - PODRIA SER GLOBAL
    remote_keywords = ["remote", "work from home", "wfh"]
    if any(kw in loc for kw in remote_keywords):
        return "maybe"

    # Other - REVISAR
    return "maybe"


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else None
    geo_filter(date)
