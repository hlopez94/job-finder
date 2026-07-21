# 🎯 Job Finder Skill

> Skill reutilizable para buscar ofertas de trabajo rankeadas según tu perfil.

## 📋 Descripción

Esta skill automatiza la búsqueda de ofertas de trabajo en múltiples fuentes (GitHub Jobs, LinkedIn, WeWorkRemotely), las rankea según tu perfil técnico y preferencias, y te notifica por Telegram con las mejores coincidencias.

## 🚀 Requisitos

- **Python 3.11+**
- **pip** (gestor de paquetes Python)
- **Git**
- **(Opcional)** MCP Server `linkedin-scraper` para búsqueda en LinkedIn
- **(Opcional)** Cuenta de GitHub con Personal Access Token
- **(Opcional)** Bot de Telegram

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/hlopez94/job-finder.git
cd job-finder

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar perfil personal
cp profile.template.yaml profile.yaml
# Editar profile.yaml con tus datos reales

# 4. Configurar API keys
cp config.template.yaml config.yaml
# Editar config.yaml con tus tokens reales

# 5. ¡Ejecutar!
python scripts/fetch-all.py
```

## 📁 Estructura del proyecto

```
job-finder/
├── profile.yaml              # [PRIVADO] Tu perfil (skills, preferencias)
├── config.yaml               # [PRIVADO] API keys, tokens
├── profile.template.yaml     # Template para compartir
├── config.template.yaml      # Template para compartir
├── scripts/
│   ├── fetch-all.py          # Orquestador principal
│   ├── sources/
│   │   ├── github_jobs.py    # Scraper GitHub Issues
│   │   ├── linkedin.py       # LinkedIn MCP connector
│   │   ├── linkedin_mcp_connector.py  # MCP client helper
│   │   └── weremote.py       # WeWorkRemotely RSS parser
│   ├── ranker.py             # Motor de ranking ponderado
│   └── notify.py             # Notificador Telegram
├── output/                   # Resultados por fecha
│   └── YYYY-MM-DD/
│       ├── results.json
│       └── results.md
├── skills/
│   └── job-finder-skill.md   # Esta skill
├── ADR/                      # Decisiones arquitectónicas
├── GLOSSARY.md               # Glosario del dominio
├── .gitignore
├── requirements.txt
└── README.md
```

## 🎮 Uso

### Búsqueda completa
```bash
# Perfil default
python scripts/fetch-all.py

# Perfil específico (multi-perfil)
python scripts/fetch-all.py --profile senior      # → profile-senior.yaml
python scripts/fetch-all.py --profile freelance   # → profile-freelance.yaml

# Opciones adicionales
python scripts/fetch-all.py --no-telegram    # skip notificación
python scripts/fetch-all.py --no-cleanup     # skip limpieza automática
python scripts/fetch-all.py --no-table       # skip tabla en terminal
python scripts/fetch-all.py --debug          # modo verbose
```

Esto ejecuta el pipeline completo:
1. **Cleanup** — Limpia resultados > 15 días
2. **Fetch** — Busca ofertas en WeWorkRemotely + RemoteOK + StackOverflow + LinkedIn
3. **Dedup** — Elimina duplicados por título + empresa
4. **Rank** — Scorrea cada oferta contra tu perfil
5. **Stats** — Genera estadísticas del mercado
6. **Notify** — Envía top N por Telegram
7. **Report** — Guarda resultados en `output/{fecha}/`

### Investigar empresa + preparar entrevista
```bash
python scripts/feedback.py --research <url>              # empresa específica
python scripts/feedback.py --research --last-run         # empresas del último run
```

### Ver resultados previos
Los resultados quedan guardados en `output/YYYY-MM-DD/` con formato Markdown y JSON.

## 📝 Formato del Perfil (profile.yaml)

```yaml
profile:
  name: "Tu Nombre"
  github_handle: "tu-user"
  preferred_stack:
    languages: [".NET", "C#", "TypeScript"]
    frameworks: ["Angular", "ASP.NET Core"]
    databases: ["PostgreSQL", "SQL Server"]
    cloud: ["Azure", "AWS"]
    tools: ["Docker", "Kubernetes"]
  experience:
    level: "Senior"
    years: 8
  preferences:
    remote_only: true
    salary_mode: "annually"          # hourly | monthly | annually
    min_salary: 80000
    max_salary: 150000
    exclude_keywords: ["blockchain", "crypto"]
  weighting:
    stack_match: 0.35
    experience_match: 0.15
    seniority_match: 0.15
    salary_match: 0.15
    remote_match: 0.10
    recency: 0.10
```

## 🔧 Configuración MCP LinkedIn

Para habilitar la búsqueda en LinkedIn, configurá el MCP server en tu `opencode.json` o `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "linkedin-scraper": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-linkedin-scraper"]
    }
  }
}
```

Luego completá los datos en `config.yaml`:
```yaml
linkedin:
  email: "tu-email@example.com"
  password: "tu-contraseña"
```

## 📊 Scoring

| Dimensión | Peso | Descripción |
|---|---|---|
| Stack Match | 35% | Coincidencia de tecnologías con tu perfil |
| Experience Match | 15% | Similitud con experiencia laboral previa |
| Seniority | 15% | Nivel de experiencia requerido |
| Salary | 15% | Rango salarial vs expectativa (normalizado a anual) |
| Remote | 10% | Modalidad de trabajo |
| Recency | 10% | Frescura de la publicación |

## 🎭 Multi-Perfil

Podés tener varios perfiles para distintos tipos de búsqueda:

```bash
# Búsqueda full-time (salario anual, senior)
python scripts/fetch-all.py --profile senior

# Búsqueda freelance (tarifa por hora)
python scripts/fetch-all.py --profile freelance
```

Cada perfil tiene su propio archivo: `profile-senior.yaml`, `profile-freelance.yaml`, etc.
Usá los templates incluidos como base y personalizalos.

## 📊 Market Stats

Cada ejecución genera estadísticas del mercado:
```
📊 Market Stats
   📦 Total jobs: 45
   🔥 Top technologies: .net, angular, typescript, azure, postgresql
   🌍 Remote: 78% | Hybrid: 15% | On-site: 7%
   📰 Sources: remoteok: 20, linkedin: 15, weremote: 10
```

## 🔒 Privacidad

- `profile.yaml`, `profile-*.yaml` y `config.yaml` están en `.gitignore`
- `output/` con resultados está en `.gitignore`
- Solo los templates y scripts se comparten en el repo público
