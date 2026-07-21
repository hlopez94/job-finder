#!/usr/bin/env python3
"""
Auto-Cleanup
==============
Limpia resultados antiguos del directorio output/.

Por defecto mantiene solo los últimos 15 días de ejecuciones.
Se ejecuta automáticamente al inicio de fetch-all.py.
"""

import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


def cleanup_old_runs(max_days: int = 15, dry_run: bool = False) -> list[str]:
    """
    Elimina directorios de output más antiguos que max_days.

    Args:
        max_days: Días máximos a mantener (default: 15)
        dry_run: Si True, solo lista lo que se eliminaría sin borrar

    Returns:
        Lista de directorios eliminados
    """
    if not OUTPUT_DIR.exists():
        return []

    cutoff = datetime.now() - timedelta(days=max_days)
    removed = []

    for entry in sorted(OUTPUT_DIR.iterdir()):
        if not entry.is_dir():
            continue

        # Intentar parsear como fecha (YYYY-MM-DD)
        try:
            dir_date = datetime.strptime(entry.name, "%Y-%m-%d")
        except ValueError:
            continue

        if dir_date < cutoff:
            if dry_run:
                print(f"   🗑️  [DRY RUN] Se eliminaría: {entry.name}")
            else:
                shutil.rmtree(entry)
                print(f"   🗑️  Eliminado: {entry.name}")
            removed.append(entry.name)

    # También limpiar feedback.json si existe y está vacío
    feedback_file = OUTPUT_DIR / "feedback.json"
    if feedback_file.exists() and feedback_file.stat().st_size < 10:
        feedback_file.unlink()

    return removed


if __name__ == "__main__":
    """CLI para limpiar manualmente.

    Uso:
        python scripts/cleanup.py                    # limpiar (default 15 días)
        python scripts/cleanup.py --days 30          # limpiar >30 días
        python scripts/cleanup.py --dry-run          # solo listar
        python scripts/cleanup.py --all              # limpiar todo
    """
    import argparse

    parser = argparse.ArgumentParser(description="Job Finder — Cleanup")
    parser.add_argument("--days", type=int, default=15, help="Días máximos a mantener")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar, no borrar")
    parser.add_argument("--all", action="store_true", help="Limpiar todo (excepto feedback.json)")

    args = parser.parse_args()

    if args.all:
        print("🧹 Limpiando TODOS los resultados...")
        for entry in OUTPUT_DIR.iterdir():
            if entry.is_dir():
                shutil.rmtree(entry)
                print(f"   🗑️  Eliminado: {entry.name}")
        print("✅ Limpieza completa.")
    else:
        print(f"🧹 Limpiando resultados anteriores a {args.days} días...")
        removed = cleanup_old_runs(max_days=args.days, dry_run=args.dry_run)
        if removed:
            print(f"✅ {len(removed)} directorios {'marcados para' if args.dry_run else ''} eliminados.")
        else:
            print("✅ Nada que limpiar.")
