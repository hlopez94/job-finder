# ADR-001: Arquitectura y Stack del Proyecto Job Finder

## Estado
**ACEPTADO** — 2026-07-21

## Contexto
Necesitamos un sistema que permita buscar ofertas de trabajo en múltiples fuentes (GitHub Issues, LinkedIn, WeWorkRemotely), las rankee según un perfil configurable, y notifique al usuario por Telegram con las mejores coincidencias.

## Decisión

### Stack Tecnológico
| Componente | Tecnología | Razón |
|---|---|---|
| **Lenguaje principal** | Python 3.11+ | Ideal para scripting, scraping, fácil de compartir. Rich ecosystem de parsing (BeautifulSoup, requests) |
| **Scraping GitHub** | `requests` + `BeautifulSoup4` + GitHub API v4 (GraphQL) | GitHub Issues API es REST/GraphQL. Fácil, sin rate limits agresivos con token |
| **Scraping LinkedIn** | MCP Server `linkedin-scraper` | Ya existe en MCP marketplace. Lo configuramos como tool externa |
| **Scraping WeWorkRemotely** | `feedparser` (RSS) | WeWorkRemotely tiene RSS público. Parseo trivial |
| **Ranking Engine** | Python puro con scoring ponderado | Evitamos dependencias ML. Ponderación configurable YAML |
| **Notificación** | `python-telegram-bot` | API simple, bot token vía env var |
| **Perfil/Config** | YAML (`PyYAML`) | Legible, versionable, fácil de compartir como template |
| **Output** | Markdown + JSON | Markdown legible para humanos, JSON para procesamiento |

### Arquitectura
```
job-finder/
├── profile.yaml              # Perfil del usuario (gitignored)
├── config.yaml               # API keys, preferencias (gitignored)
├── profile.template.yaml     # Template para compartir
├── config.template.yaml      # Template para compartir
├── scripts/
│   ├── fetch-all.py          # Orquestador principal
│   ├── sources/
│   │   ├── github_jobs.py    # Scraper GitHub Issues
│   │   ├── linkedin.py       # MCP LinkedIn connector
│   │   └── weremote.py       # RSS WeWorkRemotely
│   ├── ranker.py             # Motor de ranking
│   └── notify.py             # Notificador Telegram
├── output/                   # Resultados (gitignored)
│   └── YYYY-MM-DD/
│       ├── results.json
│       └── results.md
├── skills/
│   └── job-finder-skill.md   # Skill reutilizable
├── ADR/                      # Decisiones arquitectónicas
├── GLOSSARY.md               # Glosario del dominio
└── README.md                 # Documentación
```

### Flujo de ejecución
```
1. fetch-all.py
   ├── → github_jobs.py   (busca issues con label "job" / "hire")
   ├── → linkedin.py      (via MCP: busca por stack/remoto)
   └── → weremote.py      (parsea RSS → lista de jobs)
       ↓
2. ranker.py
   ├── Lee profile.yaml (skills, preferencias, weights)
   ├── Scorrea cada job según:
   │   - Stack match (0.40)
   │   - Seniority match (0.20)
   │   - Salary match (0.20)
   │   - Remote match (0.10)
   │   - Recency (0.10)
   └── Ordena desc → top 20
       ↓
3. notify.py
   ├── Toma top 10 del ranking
   ├── Envía Telegram con formato:
   │   🎯 Top Jobs for {date}
   │   1. {title} @ {company}
   │      💰 {salary} | 🌍 {remote} | 🏷️ {stack}
   │      🔗 {link}
   └── Guarda output en output/{date}/
```

## Consecuencias
- **Positivo**: Mínimo setup. Solo Python 3.11+ y pip
- **Positivo**: Fácil de forkear y reusar. Templates YAML claros
- **Positivo**: No depende de infraestructura cloud. Corre 100% local
- **Negativo**: LinkedIn scraper MCP puede romperse si LinkedIn cambia su HTML
- **Negativo**: GitHub Issues como fuente de jobs es menos estructurada que una API dedicada

## Alternativas Consideradas
- **Node.js/TypeScript**: Más verbose para scripting. Python es más idiomático para scraping
- **Base de datos**: Innecesaria. Output en filesystem con fechas es suficiente
- **ML model**: Overkill. Weighted scoring es más predecible y configurable
