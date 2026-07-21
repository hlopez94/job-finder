# ADR-002: Estrategia de Repositorio Público + Privado

## Estado
**ACEPTADO** — 2026-07-21

## Contexto
Queremos compartir la skill con la comunidad para que otros la reusen, pero mantener los datos personales (perfil, tokens, preferencias) privados.

## Decisión
Usar una **estrategia de template + gitignore** en un único repositorio público, sin fork privado:

| Archivo | Público | Privado | Propósito |
|---|---|---|---|
| `profile.template.yaml` | ✅ Sí | — | Template con valores dummy |
| `config.template.yaml` | ✅ Sí | — | Template con placeholders |
| `profile.yaml` | ❌ No (gitignored) | Local only | Perfil real del usuario |
| `config.yaml` | ❌ No (gitignored) | Local only | API keys reales |
| `output/` | ❌ No (gitignored) | Local only | Resultados de ejecuciones |
| `scripts/` | ✅ Sí | — | Core de la skill |
| `skills/` | ✅ Sí | — | Skill reutilizable |
| `ADR/` | ✅ Sí | — | Decisiones arquitectónicas |

### Flujo para el usuario que quiere reusar
```bash
git clone https://github.com/hlopez94/job-finder.git
cd job-finder
cp profile.template.yaml profile.yaml    # editar con datos reales
cp config.template.yaml config.yaml      # editar con tokens reales
pip install -r requirements.txt
python scripts/fetch-all.py
```

## Consecuencias
- **Positivo**: Setup simple. Un solo repo. Sin gestión de forks
- **Positivo**: El `.gitignore` evita leaks accidentales
- **Positivo**: La skill es inmediatamente reusable
- **Negativo**: Si alguien hace fork, debe crear sus propios `profile.yaml` y `config.yaml`

## Alternativas Consideradas
- **Repo público + fork privado automático**: Complejidad innecesaria, sync constante
- **Repo privado con submodule público**: Overkill para este alcance
- **Variables de entorno + encrypt**: Menos amigable para compartir
