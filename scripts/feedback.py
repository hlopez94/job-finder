#!/usr/bin/env python3
"""
Job Feedback CLI
==================
Permite al usuario marcar jobs como vistos, aplicados, o rechazados.
El feedback se usa para:
  - No mostrar jobs ya vistos en futuras ejecuciones
  - Ajustar pesos de ranking basado en preferencias implícitas

Uso:
    python scripts/feedback.py --list                    # ver todas las interacciones
    python scripts/feedback.py --apply <job-url>         # marcar como aplicado
    python scripts/feedback.py --reject <job-url>        # marcar como no interesante
    python scripts/feedback.py --seen <job-url>          # marcar como ya visto
    python scripts/feedback.py --rate <job-url> 8        # puntuar job (1-10)
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


def load_feedback() -> list[dict]:
    """Carga el historial de feedback."""
    if not FEEDBACK_FILE.exists():
        return []
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_feedback(feedback: list[dict]):
    """Guarda el historial de feedback."""
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback, f, indent=2, ensure_ascii=False)


def add_feedback(job_url: str, action: str, rating: int = None):
    """Agrega una entrada de feedback."""
    feedback = load_feedback()

    # Buscar si ya existe para ese job
    existing = [f for f in feedback if f.get("url") == job_url]
    if existing:
        entry = existing[0]
        entry["action"] = action
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


def main():
    parser = argparse.ArgumentParser(description="Job Finder — Feedback CLI")
    parser.add_argument("--list", action="store_true", help="Listar todas las interacciones")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas")
    parser.add_argument("--apply", metavar="URL", help="Marcar job como aplicado")
    parser.add_argument("--reject", metavar="URL", help="Marcar job como no interesante")
    parser.add_argument("--seen", metavar="URL", help="Marcar job como ya visto")
    parser.add_argument("--rate", nargs=2, metavar=("URL", "SCORE"), help="Puntuar job (1-10)")

    args = parser.parse_args()

    if args.list:
        list_feedback()
    elif args.stats:
        show_stats()
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
