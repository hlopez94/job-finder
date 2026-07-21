#!/usr/bin/env python3
"""
Telegram Notifier
===================
Envía notificaciones por Telegram con el top de ofertas rankeadas.
"""

import requests
from datetime import datetime


def send_telegram_notification(
    top_jobs: list[dict],
    config: dict,
    profile: dict,
    run_date: str,
) -> bool:
    """
    Envía un mensaje con las mejores ofertas por Telegram.

    Args:
        top_jobs: Lista de jobs rankeados (top N)
        config: Config del usuario (contiene telegram.bot_token, telegram.chat_id)
        profile: Perfil del usuario
        run_date: Fecha de la ejecución (YYYY-MM-DD)

    Returns:
        True si se envió correctamente, False otherwise
    """
    telegram = config.get("telegram", {})
    bot_token = telegram.get("bot_token", "")
    chat_id = telegram.get("chat_id", "")

    if not bot_token or not chat_id:
        print("   ⚠️ Telegram: bot_token o chat_id no configurados")
        return False

    # Construir mensaje
    profile_name = profile.get("profile", {}).get("name", "User")
    message = _build_message(top_jobs, profile_name, run_date)

    # Enviar
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            return True
        else:
            print(f"   ⚠️ Telegram API error: {resp.status_code} - {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"   ⚠️ Telegram connection error: {e}")
        return False


def _build_message(top_jobs: list[dict], profile_name: str, run_date: str) -> str:
    """Construye el mensaje HTML formateado para Telegram."""
    now = datetime.now().strftime("%H:%M")

    lines = [
        f"<b>🎯 Job Finder — {run_date}</b>",
        f"<i>Generado a las {now} para {profile_name}</i>",
        "",
        f"🔥 <b>Top {len(top_jobs)} Matches</b>",
        "═══════════════════════════",
        "",
    ]

    for i, job in enumerate(top_jobs, 1):
        score = job.get("_score", 0)
        title = job.get("title", "Untitled")
        company = job.get("company", "Unknown")
        salary = job.get("salary", "💰 N/A")
        remote = job.get("remote", "📍 N/A")
        url = job.get("url", "")

        # Score emoji
        if score >= 80:
            score_emoji = "🏆"
        elif score >= 60:
            score_emoji = "⭐"
        else:
            score_emoji = "📌"

        lines.append(f"{score_emoji} <b>{i}. {title}</b>")
        lines.append(f"   <b>🏢</b> {company}  |  <b>🎯</b> {score:.0f}/100")
        lines.append(f"   {salary}  |  {remote}")
        if url:
            lines.append(f"   🔗 <a href='{url}'>Abrir oferta</a>")
        lines.append("")

    lines.append("═══════════════════════════")
    lines.append("💡 <i>Editá tu perfil en profile.yaml para mejorar los matches</i>")
    lines.append(f"📁 Resultados completos: <code>output/{run_date}/</code>")

    return "\n".join(lines)
