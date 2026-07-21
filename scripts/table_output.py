#!/usr/bin/env python3
"""
Terminal Table Output
=======================
Renderiza resultados de jobs en una tabla estilizada en la terminal
usando la libreria Rich.
"""

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

import json


console = Console()


def print_jobs_table(jobs: list[dict], title: str = "Top Matches"):
    """
    Imprime una tabla estilizada con los jobs rankeados.

    Args:
        jobs: Lista de jobs rankeados (con _score)
        title: Título de la tabla
    """
    if not RICH_AVAILABLE:
        _print_fallback(jobs)
        return

    if not jobs:
        console.print("[yellow]😴 No se encontraron ofertas.[/yellow]")
        return

    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold white",
        min_width=100,
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("Score", justify="center", width=6)
    table.add_column("Title", style="bold white", width=35)
    table.add_column("Company", style="yellow", width=20)
    table.add_column("Salary", style="green", width=18)
    table.add_column("Remote", style="blue", width=10)
    table.add_column("Source", style="dim", width=14)
    table.add_column("Link", style="underline blue", width=40)

    for i, job in enumerate(jobs[:20], 1):
        score = job.get("_score", 0)
        title = job.get("title", "N/A")[:40]
        company = job.get("company", "Unknown")[:20]
        salary = _format_salary_display(job.get("salary", "N/A"))
        remote = job.get("remote", "?")[:10]
        source = job.get("source", "unknown")[:14]
        url = job.get("url", "")[:40]

        # Color según score
        if score >= 80:
            score_str = f"[bold green]{score:.0f}[/bold green]"
        elif score >= 60:
            score_str = f"[yellow]{score:.0f}[/yellow]"
        else:
            score_str = f"[red]{score:.0f}[/red]"

        table.add_row(
            str(i),
            score_str,
            title,
            company,
            salary,
            remote,
            source,
            url,
        )

    console.print()
    console.print(table)
    console.print()


def _format_salary_display(salary: str) -> str:
    """Formatea salario con indicador de modo."""
    if not salary or salary == "N/A":
        return "N/A"

    salary_lower = salary.lower()
    if any(kw in salary_lower for kw in ["/hr", "/hour", "hourly", "per hour", "por hora"]):
        return f"[cyan]{salary}[/cyan] [hourly]"
    elif any(kw in salary_lower for kw in ["/month", "/mo", "monthly", "/mes", "mensual"]):
        return f"[cyan]{salary}[/cyan] [monthly]"
    elif any(kw in salary_lower for kw in ["/year", "/yr", "annually", "/año", "anual"]):
        return f"[cyan]{salary}[/cyan] [yearly]"

    return salary


def print_job_detail(job: dict):
    """Imprime detalle de un job individual."""
    if not RICH_AVAILABLE:
        print(json.dumps(job, indent=2, ensure_ascii=False))
        return

    score = job.get("_score", 0)
    score_color = "green" if score >= 80 else ("yellow" if score >= 60 else "red")

    detail = (
        f"[bold]{job.get('title', 'N/A')}[/bold]\n"
        f"[yellow][company] {job.get('company', 'N/A')}[/yellow]\n"
        f"[{score_color}][score] {score:.1f}/100[/{score_color}]\n"
        f"[green][salary] {_format_salary_display(job.get('salary', 'N/A'))}[/green]\n"
        f"[blue][location] {job.get('remote', 'N/A')} | {job.get('location', 'N/A')}[/blue]\n"
        f"[dim][link] {job.get('url', '#')}[/dim]\n"
        f"[dim][source] {job.get('source', '?')}[/dim]\n"
    )

    if job.get("description"):
        desc = job["description"][:500]
        detail += f"\n[italic]{desc}[/italic]"

    console.print(Panel(detail, title="Job Detail", border_style="cyan"))


def print_stats(stats: dict):
    """Imprime estadísticas del mercado."""
    if not RICH_AVAILABLE:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return

    console.print(f"\n[bold cyan]--- Market Stats ---[/bold cyan]")
    console.print(f"   Total jobs: {stats.get('total', 0)}")
    # top_technologies son dicts {tech, count} -> extraer solo el nombre
    raw_techs = stats.get('top_technologies', [])[:5]
    tech_names = [t["tech"] if isinstance(t, dict) else str(t) for t in raw_techs]
    console.print(f"   Top technologies: {', '.join(tech_names)}")
    rs = stats.get('remote_stats', {})
    console.print(f"   Remote: {rs.get('remote_pct', 0):.0f}% | Hybrid: {rs.get('hybrid_pct', 0):.0f}% | On-site: {rs.get('onsite_pct', 0):.0f}%")
    console.print(f"   Sources: {', '.join(f'{k}: {v}' for k, v in stats.get('sources', {}).items())}")


def print_progress():
    """Retorna un contexto de progreso para usar en fetch-all."""
    if RICH_AVAILABLE:
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
    return None


def _print_fallback(jobs: list[dict]):
    """Fallback si rich no está instalado."""
    print()
    print(f"{'#':<3} {'Score':<6} {'Title':<40} {'Company':<20} {'Salary':<15} {'Remote':<10}")
    print("-" * 100)
    for i, job in enumerate(jobs[:15], 1):
        score = job.get("_score", 0)
        print(f"{i:<3} {score:<6.0f} {job.get('title', 'N/A')[:38]:<40} "
              f"{job.get('company', 'Unknown')[:18]:<20} "
              f"{str(job.get('salary', 'N/A'))[:13]:<15} "
              f"{job.get('remote', '?')[:8]:<10}")


if __name__ == "__main__":
    # Demo
    sample_jobs = [
        {
            "title": "Senior .NET Developer",
            "company": "Microsoft",
            "salary": "$120k - $150k/yr",
            "remote": "Remote",
            "source": "linkedin",
            "url": "https://example.com/job1",
            "_score": 92.5,
            "location": "Redmond, WA",
            "description": "We are looking for a senior .NET developer..."
        },
        {
            "title": "Angular Frontend Lead",
            "company": "Google",
            "salary": "$80 - $100/hr",
            "remote": "Remote",
            "source": "remoteok",
            "url": "https://example.com/job2",
            "_score": 85.0,
            "location": "Remote",
            "description": "Lead our Angular frontend team..."
        },
    ]
    print_jobs_table(sample_jobs)
    print_job_detail(sample_jobs[0])
