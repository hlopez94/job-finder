#!/usr/bin/env python3
"""
Job Finder — Orquestador Principal
====================================
Pipeline: fetch → rank → notify → report

Uso:
    python scripts/fetch-all.py

Requiere:
    - profile.yaml (en raíz del proyecto)
    - config.yaml  (en raíz del proyecto)
    - pip install -r requirements.txt
"""

import sys
import os
import yaml
import json
from datetime import datetime
from pathlib import Path

# Asegurar que podemos importar los módulos locales
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Imports de los scrapers ──
from scripts.sources.weremote import fetch_weworkremotely_jobs
from scripts.sources.remoteok import fetch_remoteok_jobs
from scripts.sources.stackoverflow import fetch_stackoverflow_jobs
from scripts.ranker import rank_jobs
from scripts.notify import send_telegram_notification

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"

def load_config():
    """Carga profile.yaml y config.yaml"""
    profile_path = ROOT_DIR / "profile.yaml"
    config_path = ROOT_DIR / "config.yaml"

    if not profile_path.exists():
        print("❌ No se encontró profile.yaml. Copiá profile.template.yaml → profile.yaml")
        sys.exit(1)
    if not config_path.exists():
        print("❌ No se encontró config.yaml. Copiá config.template.yaml → config.yaml")
        sys.exit(1)

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return profile, config


def ensure_output_dir(run_date: str) -> Path:
    """Crea el directorio de output para la fecha actual"""
    run_dir = OUTPUT_DIR / run_date
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def main():
    print("=" * 60)
    print("  🎯 Job Finder — Iniciando búsqueda")
    print("=" * 60)
    print()

    # ── 1. Cargar configuración ──
    print("📄 Cargando perfil y configuración...")
    profile, config = load_config()
    print(f"   Perfil: {profile['profile']['name']}")
    print(f"   Stack: {', '.join(profile['profile']['preferred_stack']['languages'])}")
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

    # 2c. StackOverflow Jobs
    print("   ├── StackOverflow Jobs...")
    try:
        so_jobs = fetch_stackoverflow_jobs(config, profile)
        print(f"   │   ✅ {len(so_jobs)} ofertas encontradas")
        all_jobs.extend(so_jobs)
    except Exception as e:
        print(f"   │   ⚠️ Error: {e}")

    # 2d. LinkedIn (via MCP)
    print("   └── LinkedIn (via MCP)...")
    try:
        from scripts.sources.linkedin import fetch_linkedin_jobs
        linkedin_jobs = fetch_linkedin_jobs(config, profile)
        print(f"       ✅ {len(linkedin_jobs)} ofertas encontradas")
        all_jobs.extend(linkedin_jobs)
    except ImportError:
        print(f"       ⚠️ Módulo linkedin no disponible. Skipping.")
    except Exception as e:
        print(f"       ⚠️ Error: {e}")

    print()
    print(f"📊 Total: {len(all_jobs)} ofertas recolectadas")
    print()

    if not all_jobs:
        print("😴 No se encontraron ofertas. Probá ajustar los filtros.")
        sys.exit(0)

    # ── 3. Ranking ──
    print("🏆 Rankeando ofertas...")
    ranked = rank_jobs(all_jobs, profile)
    top_jobs = ranked[:config["ranking"]["show_top"]]
    print(f"   Top {len(top_jobs)} ofertas seleccionadas")
    print()

    # ── 4. Guardar resultados ──
    print("💾 Guardando resultados...")
    json_path = run_dir / "results.json"
    md_path = run_dir / "results.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "run_date": run_date,
            "profile": profile["profile"]["name"],
            "total_fetched": len(all_jobs),
            "total_ranked": len(ranked),
            "top_results": [
                {
                    "rank": i + 1,
                    "title": j["title"],
                    "company": j.get("company", "Unknown"),
                    "score": j["_score"],
                    "salary": j.get("salary", "N/A"),
                    "remote": j.get("remote", "Unknown"),
                    "url": j.get("url", ""),
                    "source": j.get("source", "unknown"),
                }
                for i, j in enumerate(top_jobs)
            ]
        }, f, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 🎯 Job Finder — {run_date}\n\n")
        f.write(f"**Perfil:** {profile['profile']['name']}\n\n")
        f.write(f"**Total ofertas encontradas:** {len(all_jobs)}\n")
        f.write(f"**Rankeadas:** {len(ranked)}\n\n")
        f.write("---\n\n")
        f.write("## 🏆 Top Matches\n\n")
        for i, job in enumerate(top_jobs):
            score = job["_score"]
            f.write(f"### {i+1}. {job['title']} — 🎯 {score:.0f}/100\n\n")
            f.write(f"| Campo | Valor |\n|---|---|\n")
            f.write(f"| **Empresa** | {job.get('company', 'N/A')} |\n")
            f.write(f"| **Salario** | {job.get('salary', 'N/A')} |\n")
            f.write(f"| **Remoto** | {job.get('remote', 'N/A')} |\n")
            f.write(f"| **Fuente** | {job.get('source', 'N/A')} |\n")
            f.write(f"| **Link** | [{job.get('url', '#')}]({job.get('url', '#')}) |\n\n")
            f.write(f"{job.get('description', '')[:300]}...\n\n---\n\n")

    print(f"   📄 {json_path}")
    print(f"   📄 {md_path}")
    print()

    # ── 5. Notificar por Telegram ──
    if config.get("telegram", {}).get("bot_token") and config["telegram"].get("chat_id"):
        print("📱 Enviando notificación Telegram...")
        try:
            send_telegram_notification(top_jobs, config, profile, run_date)
            print("   ✅ Notificación enviada")
        except Exception as e:
            print(f"   ⚠️ Error al enviar Telegram: {e}")
    else:
        print("📱 Telegram no configurado. Skipping notificación.")

    print()
    print("=" * 60)
    print("  ✅ Job Finder — Completado")
    print(f"  📁 Resultados: {run_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
