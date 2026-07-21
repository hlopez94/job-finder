# 🎯 Job Finder

> Buscador inteligente de ofertas de trabajo que rankea posiciones según tu perfil técnico y te notifica por Telegram.

## ✨ Features

- 🔍 **Multi-fuente**: GitHub Issues, LinkedIn, WeWorkRemotely
- 🏆 **Ranking inteligente**: Scoring ponderado según tu stack, seniority, salary y más
- 📱 **Notificaciones Telegram**: Recibís las mejores ofertas al instante
- 📁 **Historial local**: Resultados guardados por fecha en Markdown y JSON
- 🔒 **Privacidad**: Tus datos personales nunca se comparten
- 🧩 **100% reusable**: Cloná, configurá tu perfil, ejecutá

## 🚀 Quick Start

```bash
git clone https://github.com/hlopez94/job-finder.git
cd job-finder
pip install -r requirements.txt
cp profile.template.yaml profile.yaml   # editá con tus datos
cp config.template.yaml config.yaml     # editá con tus tokens
python scripts/fetch-all.py
```

## 📦 Estructura

```
job-finder/
├── scripts/
│   ├── fetch-all.py        # Orquestador
│   ├── ranker.py           # Motor de ranking
│   ├── notify.py           # Telegram notifier
│   └── sources/            # Scrapers por fuente
├── skills/                 # Skill reutilizable
├── ADR/                    # Decisiones arquitectónicas
├── output/                 # Resultados (gitignored)
├── profile.template.yaml   # Template de perfil
├── config.template.yaml    # Template de configuración
└── requirements.txt
```

## ⚙️ Configuración

Ver `profile.template.yaml` para el perfil y `config.template.yaml` para API keys.

## 💰 Salary Mode

Configurá el modo salarial que prefieras — soporta **hora**, **mensual** o **anual**:

```yaml
preferences:
  salary_mode: "annually"   # "hourly" | "monthly" | "annually"
  min_salary: 80000
  max_salary: 150000
```

El motor de ranking normaliza automáticamente todos los salarios a base anual para comparar.
Ej: `30-45/hr` → ~$62k-94k/año • `6000-10000/mes` → ~$72k-120k/año

## 📊 Ranking

| Dimensión | Peso |
|---|---|
| Stack Match | 35% |
| Experience Match | 15% |
| Seniority | 15% |
| Salary | 15% |
| Remote | 10% |
| Recency | 10% |

## 📝 Licencia

MIT — hacé fork, usalo, mejoralo.
