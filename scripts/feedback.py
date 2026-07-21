#!/usr/bin/env python3
"""
Job Feedback CLI
==================
Permite al usuario interactuar con los resultados de búsqueda.

Comandos:
    python scripts/feedback.py --list                    # ver todas las interacciones
    python scripts/feedback.py --apply <url>             # marcar como aplicado
    python scripts/feedback.py --reject <url>            # marcar como no interesante
    python scripts/feedback.py --seen <url>              # marcar como ya visto
    python scripts/feedback.py --rate <url> <1-10>       # puntuar job (1-10)
    python scripts/feedback.py --research <url>          # investigar empresa del job
    python scripts/feedback.py --research --last-run     # investigar empresas del último run
    python scripts/feedback.py --stats                   # estadísticas de feedback
"""

import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
FEEDBACK_FILE = ROOT_DIR / "output" / "feedback.json"
OUTPUT_DIR = ROOT_DIR / "output"


def load_feedback() -> list[dict]:
    """Carga el historial de feedback."""
    if not FEEDBACK_FILE.exists():
        return []
    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_feedback(feedback: list[dict]):
    """Guarda el historial de feedback."""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback, f, indent=2, ensure_ascii=False)


def add_feedback(job_url: str, action: str, rating: int = None):
    """Agrega una entrada de feedback."""
    feedback = load_feedback()

    existing = [f for f in feedback if f.get("url") == job_url]
    if existing:
        entry = existing[0]
        entry["action"] = action
        if rating:
            entry["rating"] = rating
        entry["updated_at"] = datetime.now().isoformat()
    else:
        feedback.append({
            "url": job_url,
            "action": action,
            "rating": rating,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })

    save_feedback(feedback)
    print(f"✅ Job marcado como '{action}': {job_url}")


def list_feedback():
    """Lista todo el feedback."""
    feedback = load_feedback()
    if not feedback:
        print("📭 No hay feedback registrado.")
        return

    print(f"\n📊 Feedback History ({len(feedback)} entries):\n")
    print(f"{'Action':<12} {'Rating':<8} {'URL'}")
    print("-" * 80)
    for entry in feedback:
        rating = str(entry.get("rating", "-")) if entry.get("rating") else "-"
        print(f"{entry['action']:<12} {rating:<8} {entry['url']}")


def show_stats():
    """Muestra estadísticas de feedback."""
    feedback = load_feedback()
    if not feedback:
        print("📭 No hay feedback registrado.")
        return

    total = len(feedback)
    applied = sum(1 for f in feedback if f["action"] == "apply")
    rejected = sum(1 for f in feedback if f["action"] == "reject")
    seen = sum(1 for f in feedback if f["action"] == "seen")
    rated = [f for f in feedback if f.get("rating")]

    print(f"\n📊 Feedback Stats:\n")
    print(f"   Total interactions: {total}")
    print(f"   ✅ Applied:         {applied}")
    print(f"   👎 Rejected:        {rejected}")
    print(f"   👁️  Seen:            {seen}")
    if rated:
        avg_rating = sum(f["rating"] for f in rated) / len(rated)
        print(f"   ⭐ Avg rating:      {avg_rating:.1f}/10 ({len(rated)} rated)")


def research_job(job_url: str):
    """
    Investiga una empresa a partir de la URL de un job.
    Busca el job en los resultados guardados o lo crea desde la URL.
    """
    from scripts.company_research import research_company, generate_report

    # Buscar en últimos resultados
    job_data = _find_job_by_url(job_url)

    if not job_data:
        # Si no encontramos el job, pedimos datos básicos
        print(f"⚠️ No se encontraron datos del job en resultados locales.")
        company = input("   Nombre de la empresa: ")
        title = input("   Título del puesto: ")
        job_data = {
            "company": company,
            "title": title,
            "url": job_url,
            "salary": "N/A",
            "_score": 0,
        }

    company = job_data.get("company", "Unknown")
    print(f"\n🔍 Investigando {company}...\n")

    report = generate_report(job_data)

    # Guardar reporte
    report_dir = OUTPUT_DIR / "research"
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in company).strip()
    report_path = report_dir / f"{safe_name}_{datetime.now().strftime('%Y%m%d')}.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(report)
    print(f"\n📄 Reporte guardado: {report_path}")


def research_last_run():
    """Investiga empresas de los top jobs del último run."""
    # Encontrar el directorio más reciente
    if not OUTPUT_DIR.exists():
        print("❌ No hay ejecuciones previas.")
        return

    runs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name != "research"]
    if not runs:
        print("❌ No hay ejecuciones previas.")
        return

    latest = max(runs, key=lambda d: d.name)
    results_file = latest / "results.json"

    if not results_file.exists():
        print(f"❌ No se encontraron resultados en {latest.name}")
        return

    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    top_results = data.get("top_results", [])
    if not top_results:
        print("❌ No hay resultados en el último run.")
        return

    print(f"\n🔍 Investigando top {len(top_results[:5])} empresas del run {latest.name}...\n")
    for job in top_results[:5]:
        research_job(job.get("url", ""))


def _find_job_by_url(url: str) -> dict | None:
    """Busca un job por URL en los resultados guardados."""
    if not OUTPUT_DIR.exists():
        return None

    for run_dir in sorted(OUTPUT_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir() or run_dir.name == "research":
            continue
        results_file = run_dir / "results.json"
        if not results_file.exists():
            continue

        try:
            with open(results_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for job in data.get("top_results", []):
                if job.get("url") == url:
                    return job
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    return None


def main():
    parser = argparse.ArgumentParser(description="Job Finder — Feedback CLI")
    parser.add_argument("--list", action="store_true", help="Listar todas las interacciones")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--apply", metavar="URL", help="Marcar job como aplicado")
    parser.add_argument("--reject", metavar="URL", help="Marcar job como no interesante")
    parser.add_argument("--seen", metavar="URL", help="Marcar job como ya visto")
    parser.add_argument("--rate", nargs=2, metavar=("URL", "SCORE"), help="Puntuar job (1-10)")
    parser.add_argument("--research", metavar="URL", nargs="?", const="__last__",
                        help="Investigar empresa del job (o --research --last-run)")
    parser.add_argument("--last-run", action="store_true",
                        help="Usar con --research para investigar empresas del último run")

    args = parser.parse_args()

    if args.list:
        list_feedback()
    elif args.stats:
        show_stats()
    elif args.last_run and args.research:
        research_last_run()
    elif args.research and args.research != "__last__":
        research_job(args.research)
    elif args.apply:
        add_feedback(args.apply, "apply")
    elif args.reject:
        add_feedback(args.reject, "reject")
    elif args.seen:
        add_feedback(args.seen, "seen")
    elif args.rate:
        try:
            score = int(args.rate[1])
            if score < 1 or score > 10:
                print("❌ Score debe ser entre 1 y 10")
                sys.exit(1)
            add_feedback(args.rate[0], "rated", score)
        except ValueError:
            print("❌ Score debe ser un número entero")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
