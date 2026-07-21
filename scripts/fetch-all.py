#!/usr/bin/env python3
"""
Job Finder — Orquestador Principal
====================================
Pipeline: fetch → dedup → rank → stats → notify → report

Uso:
    python scripts/fetch-all.py                         # usa profile.yaml
    python scripts/fetch-all.py --profile senior        # usa profile-senior.yaml
    python scripts/fetch-all.py --profile freelance     # usa profile-freelance.yaml
    python scripts/fetch-all.py --no-telegram           # skip notificación
    python scripts/fetch-all.py --no-cleanup            # skip limpieza

Requiere:
    - profile.yaml (o profile-{name}.yaml) en raíz del proyecto
    - config.yaml  (en raíz del proyecto)
    - pip install -r requirements.txt
"""

import sys
import os
import yaml
import json
import argparse
from datetime import datetime
from pathlib import Path

# Asegurar que podemos importar los módulos locales
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Imports de módulos locales ──
from scripts.sources.weremote import fetch_weworkremotely_jobs
from scripts.sources.remoteok import fetch_remoteok_jobs
from scripts.ranker import rank_jobs
from scripts.notify import send_telegram_notification
from scripts.dedup import deduplicate
from scripts.cleanup import cleanup_old_runs
from scripts.market_stats import compute_stats, format_stats_report

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


def load_config(profile_name: str = "profile"):
    """
    Carga profile y config.

    Args:
        profile_name: Nombre del perfil sin extensión.
                      "profile" → profile.yaml
                      "senior"  → profile-senior.yaml

    Returns:
        tuple: (profile, config)
    """
    # Determinar archivo de perfil
    if profile_name == "profile":
        profile_path = ROOT_DIR / "profile.yaml"
    else:
        profile_path = ROOT_DIR / f"profile-{profile_name}.yaml"

    config_path = ROOT_DIR / "config.yaml"

    if not profile_path.exists():
        print(f"❌ No se encontró {profile_path.name}.")
        available = list(ROOT_DIR.glob("profile*.yaml"))
        if available:
            print(f"   Perfiles disponibles: {', '.join(p.name for p in available)}")
        print(f"   Creá uno desde profile.template.yaml → {profile_path.name}")
        sys.exit(1)
    if not config_path.exists():
        print("❌ No se encontró config.yaml. Copiá config.template.yaml → config.yaml")
        sys.exit(1)

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return profile, config, profile_path.name


def ensure_output_dir(run_date: str) -> Path:
    """Crea el directorio de output para la fecha actual"""
    run_dir = OUTPUT_DIR / run_date
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def print_horizontal_rule():
    """Imprime una línea horizontal en la terminal."""
    try:
        from rich.console import Console
        console = Console()
        console.rule(style="blue")
    except ImportError:
        print("─" * 60)


def main():
    parser = argparse.ArgumentParser(description="🎯 Job Finder — Buscador inteligente de ofertas")
    parser.add_argument("--profile", default="profile",
                        help="Nombre del perfil (default: 'profile' → profile.yaml, 'senior' → profile-senior.yaml)")
    parser.add_argument("--no-telegram", action="store_true", help="Skip notificación Telegram")
    parser.add_argument("--no-cleanup", action="store_true", help="Skip limpieza automática")
    parser.add_argument("--no-table", action="store_true", help="Skip tabla en terminal")
    parser.add_argument("--output", choices=["md", "json", "both"], default="both",
                        help="Formato de output (default: both)")
    parser.add_argument("--debug", action="store_true", help="Modo debug (más verbose)")

    args = parser.parse_args()

    print("=" * 60)
    print(f"  🎯 Job Finder")
    print(f"  Perfil: {args.profile}")
    print("=" * 60)

    # ── 0. Cleanup automático (15 días) ──
    if not args.no_cleanup:
        print("🧹 Limpieza automática (> 15 días)...")
        removed = cleanup_old_runs(max_days=15)
        if removed:
            print(f"   ✅ {len(removed)} ejecuciones antiguas eliminadas")
        print()

    # ── 1. Cargar configuración ──
    print("📄 Cargando perfil y configuración...")
    profile, config, profile_filename = load_config(args.profile)
    p = profile.get("profile", {})
    print(f"   Perfil: {p.get('name', 'N/A')} ({profile_filename})")
    print(f"   Stack: {', '.join(p.get('preferred_stack', {}).get('languages', []))}")
    salary_mode = p.get("preferences", {}).get("salary_mode", "annually")
    min_s = p.get("preferences", {}).get("min_salary", 0)
    max_s = p.get("preferences", {}).get("max_salary", 0)
    print(f"   Salary: ${min_s}-${max_s}/{salary_mode}")
    print()

    run_date = datetime.now().strftime("%Y-%m-%d")
    run_dir = ensure_output_dir(run_date)

    all_jobs = []

    # ── 2. Fetch de cada fuente ──
    print("🔍 Buscando ofertas...")
    print()

    # 2a. WeWorkRemotely
    print("   ├── WeWorkRemotely...")
    try:
        weremote_jobs = fetch_weworkremotely_jobs(config, profile)
        print(f"   │   ✅ {len(weremote_jobs)} ofertas encontradas")
        all_jobs.extend(weremote_jobs)
    except Exception as e:
        print(f"   │   ⚠️ Error: {e}")

    # 2b. RemoteOK
    print("   ├── RemoteOK...")
    try:
        remoteok_jobs = fetch_remoteok_jobs(config, profile)
        print(f"   │   ✅ {len(remoteok_jobs)} ofertas encontradas")
        all_jobs.extend(remoteok_jobs)
    except Exception as e:
        print(f"   │   ⚠️ Error: {e}")

    # 2c. LinkedIn (via Guest Jobs API — no auth needed)
    print("   ├── LinkedIn...")
    try:
        from scripts.sources.linkedin import fetch_linkedin_jobs
        linkedin_jobs = fetch_linkedin_jobs(config, profile)
        print(f"   │   ✅ {len(linkedin_jobs)} ofertas encontradas")
        all_jobs.extend(linkedin_jobs)
    except Exception as e:
        print(f"   │   ⚠️ Error: {e}")

    print()
    print(f"📊 Total pre-dedup: {len(all_jobs)} ofertas")
    print()

    if not all_jobs:
        print("😴 No se encontraron ofertas. Probá ajustar los filtros.")
        sys.exit(0)

    # ── 3. Deduplicación ──
    print("🔍 Deduplicando...")
    deduped = deduplicate(all_jobs)
    duplicates = len(all_jobs) - len(deduped)
    if duplicates > 0:
        print(f"   ✅ {duplicates} duplicados eliminados")
    print(f"   📦 {len(deduped)} ofertas únicas")
    print()

    # ── 4. Ranking ──
    print("🏆 Rankeando ofertas...")
    ranked = rank_jobs(deduped, profile)
    show_top = config.get("ranking", {}).get("show_top", 10)
    top_jobs = ranked[:show_top]
    print(f"   Top {len(top_jobs)} ofertas seleccionadas")
    print()

    # ── 5. Tabla en terminal ──
    if not args.no_table:
        try:
            from scripts.table_output import print_jobs_table, print_stats
            print_jobs_table(ranked[:show_top],
                             title=f"🏆 Top {show_top} — {p.get('name', 'Job Finder')}")
        except ImportError:
            pass  # rich no instalado, no mostrar tabla

    print_horizontal_rule()

    # ── 6. Market Stats ──
    print("📊 Generando estadísticas de mercado...")
    stats = compute_stats(ranked)
    try:
        from scripts.table_output import print_stats as print_stats_table
        print_stats_table(stats)
    except ImportError:
        print(f"   📦 Total: {stats['total']} jobs")
    print()

    # ── 7. Guardar resultados ──
    print("💾 Guardando resultados...")

    json_path = run_dir / "results.json"
    md_path = run_dir / "results.md"
    stats_path = run_dir / "market-stats.md"

    # JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_date": run_date,
            "profile": p.get("name", "N/A"),
            "profile_file": profile_filename,
            "total_fetched": len(all_jobs),
            "total_deduped": len(deduped),
            "total_ranked": len(ranked),
            "top_results": [
                {
                    "rank": i + 1,
                    "title": j.get("title", "N/A"),
                    "company": j.get("company", "Unknown"),
                    "score": round(j.get("_score", 0), 1),
                    "score_detail": j.get("_scores", {}),
                    "salary": j.get("salary", "N/A"),
                    "remote": j.get("remote", "Unknown"),
                    "location": j.get("location", "N/A"),
                    "url": j.get("url", ""),
                    "source": j.get("source", "unknown"),
                    "posted_at": j.get("posted_at", ""),
                }
                for i, j in enumerate(top_jobs)
            ],
            "stats": stats,
        }, f, indent=2, ensure_ascii=False)

    # Markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 🎯 Job Finder — {run_date}\n\n")
        f.write(f"**Perfil:** {p.get('name', 'N/A')} ({profile_filename})\n\n")
        f.write(f"**Total ofertas encontradas:** {len(all_jobs)}\n")
        f.write(f"**Duplicados eliminados:** {duplicates}\n")
        f.write(f"**Rankeadas:** {len(ranked)}\n\n")

        f.write("---\n\n## 🏆 Top Matches\n\n")
        for i, job in enumerate(top_jobs):
            score = job.get("_score", 0)
            f.write(f"### {i+1}. {job.get('title', 'N/A')} — 🎯 {score:.0f}/100\n\n")
            f.write("| Campo | Valor |\n|---|---|\n")
            f.write(f"| **Empresa** | {job.get('company', 'N/A')} |\n")
            f.write(f"| **Salario** | {job.get('salary', 'N/A')} |\n")
            f.write(f"| **Remoto** | {job.get('remote', 'N/A')} |\n")
            f.write(f"| **Ubicación** | {job.get('location', 'N/A')} |\n")
            f.write(f"| **Fuente** | {job.get('source', 'N/A')} |\n")
            f.write(f"| **Link** | [{job.get('url', '#')}]({job.get('url', '#')}) |\n")
            if job.get("posted_at"):
                f.write(f"| **Publicado** | {job['posted_at']} |\n")
            f.write(f"\n{job.get('description', '')[:400]}...\n\n---\n\n")

        # Incluir market stats
        f.write("\n## 📊 Market Stats\n\n")
        f.write(format_stats_report(stats))

    # Market stats report
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(format_stats_report(stats))

    print(f"   📄 {json_path}")
    print(f"   📄 {md_path}")
    print(f"   📄 {stats_path}")
    print()

    # ── 8. Notificar por Telegram ──
    if not args.no_telegram:
        telegram = config.get("telegram", {})
        if telegram.get("bot_token") and telegram.get("chat_id"):
            print("📱 Enviando notificación Telegram...")
            try:
                send_telegram_notification(top_jobs, config, profile, run_date)
                print("   ✅ Notificación enviada")
            except Exception as e:
                print(f"   ⚠️ Error al enviar Telegram: {e}")
        else:
            print("📱 Telegram no configurado. Skipping notificación.")
    else:
        print("📱 Telegram omitido (--no-telegram)")

    # ── 9. Tips post-ejecución ──
    print()
    print("💡 Tips:")
    print("   • Ver feedback:  python scripts/feedback.py --list")
    print("   • Investigar empresa:  python scripts/feedback.py --research <url>")
    print("   • Multi-perfil:  python scripts/fetch-all.py --profile freelance")

    print()
    print("=" * 60)
    print("  ✅ Job Finder — Completado")
    print(f"  📁 Resultados: {run_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
