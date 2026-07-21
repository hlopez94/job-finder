# ⚙️ Configuración de MCP Servers

Este documento explica cómo configurar los MCP servers necesarios para el proyecto **Job Finder**.

## 📋 MCP Servers Requeridos

| Server | Propósito | Config |
|---|---|---|
| **MCPVault (Obsidian)** | Acceso al vault de documentación | `@bitbonsai/mcpvault@latest` |
| **LinkedIn Scraper** | Búsqueda de ofertas en LinkedIn | `@stickerdaniel/linkedin-mcp-server` |
| **MarkItDown** | Convertir PDF/Word/Excel a Markdown | `markitdown-mcp` (pip) |

---

## 1️⃣ MCPVault — Acceso a Obsidian

[MCPVault](https://mcpvault.org) permite que el asistente AI lea, busque y cree notas en tu vault de Obsidian.

### Instalación

**En OpenCode** (recomendado → config ya incluido en `opencode.json`):
```bash
opencode mcp add
# Modo interactivo → seleccioná "local" → ingresá:
# npx -y @bitbonsai/mcpvault@latest D:\work-scrapper\job-finder
```

**En Claude Code:**
```bash
claude mcp add-json obsidian --scope project '{
  "type": "stdio",
  "command": "npx",
  "args": ["@bitbonsai/mcpvault@latest", "D:\\work-scrapper\\job-finder"]
}'
```

**En Claude Desktop / ChatGPT+:**
Agregar a `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "mcpvault-obsidian": {
      "command": "npx",
      "args": [
        "-y",
        "@bitbonsai/mcpvault@latest",
        "D:\\work-scrapper\\job-finder"
      ]
    }
  }
}
```

> 💡 **Tip**: Si tu AI client se ejecuta desde la carpeta del vault, podés omitir el path: `"args": ["@bitbonsai/mcpvault@latest"]`

### Verificar instalación
```bash
npx @bitbonsai/mcpvault@latest --version
```

---

## 2️⃣ LinkedIn Scraper MCP

[LinkedIn MCP Server](https://github.com/stickerdaniel/linkedin-mcp-server) permite buscar ofertas de trabajo, scrapear perfiles y empresas de LinkedIn.

### Requisitos
- Cookie `li_at` de LinkedIn (sesión activa)
- Node.js 18+

### Obtener tu cookie `li_at`

1. Iniciá sesión en [LinkedIn](https://linkedin.com) desde tu navegador
2. Abrí las DevTools (F12)
3. Andá a **Application** → **Cookies** → `www.linkedin.com`
4. Buscá `li_at` y copiá el valor
5. Guardalo como variable de entorno:
   ```bash
   # PowerShell
   $env:LINKEDIN_LI_AT_COOKIE = "tu-cookie-aqui"
   
   # O en .env.local (ya está en .gitignore)
   echo "LINKEDIN_LI_AT_COOKIE=tu-cookie-aqui" >> .env.local
   ```

### Configurar en OpenCode

Config en `opencode.json`:
```json
{
  "mcpServers": {
    "linkedin-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "@stickerdaniel/linkedin-mcp-server"
      ],
      "env": {
        "LINKEDIN_COOKIE": "${LINKEDIN_LI_AT_COOKIE}"
      }
    }
  }
}
```

### Verificar instalación
```bash
npx @stickerdaniel/linkedin-mcp-server --help
```

---

## 3️⃣ MarkItDown — Conversión de Documentos

[MarkItDown MCP](https://github.com/microsoft/markitdown) convierte documentos (PDF, Word, Excel, PowerPoint, imágenes, audio, HTML, etc.) a Markdown. Es útil para el proyecto **Job Finder** cuando necesitás:

- Leer un CV en PDF para generar tu `profile.yaml` (skill `generar-perfil`)
- Procesar documentos adjuntos a ofertas de trabajo

### Instalación

Ya está en `requirements.txt`:
```bash
pip install markitdown-mcp
```

### Uso en OpenCode

Config ya incluido en `opencode.json`:
```json
{
  "mcpServers": {
    "markitdown": {
      "command": "markitdown-mcp",
      "args": []
    }
  }
}
```

### Verificar instalación
```bash
markitdown-mcp --help
```

### Herramienta expuesta

El server expone una sola tool:
- `convert_to_markdown(uri)` — donde `uri` puede ser `http:`, `https:`, `file:` o `data:`

**Ejemplo de uso (en el agente):**
```
Convertí el CV en C:\Users\...\mi-cv.pdf a markdown
→ usa convert_to_markdown con uri file:///C:/Users/.../mi-cv.pdf
```

### Alternativa: usar la librería directamente

También podés usar `markitdown` como librería Python (sin MCP):
```bash
pip install 'markitdown[pdf]'
```

```python
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert("cv.pdf")
print(result.text_content)
```

---

## 4️⃣ Configurar secrets en Docker MCP (si usás Docker)

```bash
# LinkedIn cookie
docker mcp secret set linkedin-mcp-server.cookie=<tu-li_at-cookie>

# Obsidian API key (solo si usás obsidian mcp server en vez de mcpvault)
docker mcp secret set obsidian.api_key=<tu-api-key>
```

---

## 🔒 Seguridad

- **NUNCA** compartas tu cookie `li_at` de LinkedIn
- **NUNCA** subas `.env.local` o `config.yaml` con datos reales al repo
- El `.gitignore` ya protege estos archivos
- Usá variables de entorno para tokens sensibles
