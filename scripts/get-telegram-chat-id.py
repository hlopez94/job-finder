#!/usr/bin/env python3
"""
Telegram Chat ID Helper
========================
Obtiene automáticamente tu chat_id de Telegram.

Uso:
    python scripts/get-telegram-chat-id.py <BOT_TOKEN>

Pasos previos:
    1. Crear bot con @BotFather (te da el BOT_TOKEN)
    2. Abrir chat con tu bot y enviarle cualquier mensaje (ej: "hola")
    3. Correr este script
"""

import sys
import requests


def get_chat_id(bot_token: str) -> None:
    """Obtiene el chat_id del último chat que le escribió al bot."""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

    try:
        resp = requests.get(url, timeout=15)
    except requests.RequestException as e:
        print(f"[ERROR] No se pudo conectar a Telegram: {e}")
        sys.exit(1)

    data = resp.json()

    if not data.get("ok"):
        print(f"[ERROR] Token invalido o error de API: {data.get('description')}")
        sys.exit(1)

    results = data.get("result", [])
    if not results:
        print("[!] No hay mensajes. Anda a Telegram y enviale un mensaje a tu bot primero.")
        print("    Luego volve a correr este script.")
        sys.exit(1)

    # Tomar el chat del mensaje mas reciente
    last = results[-1]
    message = last.get("message") or last.get("channel_post") or {}
    chat = message.get("chat", {})

    chat_id = chat.get("id")
    first_name = chat.get("first_name", "")
    username = chat.get("username", "")

    if not chat_id:
        print("[ERROR] No se pudo extraer el chat_id")
        sys.exit(1)

    print()
    print("=" * 50)
    print("  [OK] Chat ID encontrado")
    print("=" * 50)
    print(f"  Nombre:   {first_name}")
    print(f"  Username: @{username}")
    print(f"  Chat ID:  {chat_id}")
    print()
    print("  Agregalo a tu config.yaml:")
    print()
    print("  telegram:")
    print(f"    bot_token: \"{bot_token}\"")
    print(f"    chat_id: \"{chat_id}\"")
    print()


def send_test_message(bot_token: str, chat_id: str) -> None:
    """Envia un mensaje de prueba para verificar la config."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "<b>Job Finder</b> - Bot configurado correctamente!\n\nYa vas a recibir tus ofertas de trabajo rankeadas aca.",
        "parse_mode": "HTML",
    }
    resp = requests.post(url, json=payload, timeout=15)
    if resp.json().get("ok"):
        print("[OK] Mensaje de prueba enviado! Revisa tu Telegram.")
    else:
        print(f"[ERROR] No se pudo enviar el mensaje: {resp.json()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/get-telegram-chat-id.py <BOT_TOKEN> [chat_id --test]")
        sys.exit(1)

    token = sys.argv[1]

    # Modo test: verificar config completa
    if len(sys.argv) >= 4 and sys.argv[3] == "--test":
        send_test_message(token, sys.argv[2])
    else:
        get_chat_id(token)
