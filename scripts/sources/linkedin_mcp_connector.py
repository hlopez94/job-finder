#!/usr/bin/env python3
"""
LinkedIn MCP Server Connector
===============================
Connector especializado para interactuar con el MCP server linkedin-scraper
a través del protocolo MCP (Model Context Protocol).

Este script se comunica con el MCP server vía stdio JSON-RPC.

Requisitos:
  - MCP server configurado e instalado
  - Config en ~/.config/opencode/opencode.json o claude_desktop_config.json
"""

import json
import sys
import subprocess
from typing import Any


class MCPClient:
    """Cliente mínimo para interactuar con un MCP server vía stdio."""

    def __init__(self, server_command: str, args: list[str] = None):
        self.process = subprocess.Popen(
            [server_command] + (args or []),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def send_request(self, method: str, params: dict = None) -> dict:
        """Envía una solicitud JSON-RPC al MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        line = json.dumps(request) + "\n"
        self.process.stdin.write(line)
        self.process.stdin.flush()

        response_line = self.process.stdout.readline()
        if not response_line:
            raise ConnectionError("MCP server closed connection")

        return json.loads(response_line)

    def close(self):
        self.process.terminate()
        self.process.wait()


# ── Ejemplo de uso ──
if __name__ == "__main__":
    """
    Uso:
        python linkedin_mcp_connector.py <email> <password> <keyword> <location>

    Ejemplo:
        python linkedin_mcp_connector.py my@email.com pass123 ".NET" "Worldwide"
    """
    if len(sys.argv) < 5:
        print("Uso: python linkedin_mcp_connector.py <email> <password> <keyword> <location>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    keyword = sys.argv[3]
    location = sys.argv[4]

    client = MCPClient("npx", ["@modelcontextprotocol/server-linkedin-scraper"])
    try:
        # Inicializar
        client.send_request("initialize")

        # Llamar a la herramienta de search
        result = client.send_request("tools/call", {
            "name": "search_jobs",
            "arguments": {
                "email": email,
                "password": password,
                "keyword": keyword,
                "location": location,
            }
        })
        print(json.dumps(result, indent=2))
    finally:
        client.close()
