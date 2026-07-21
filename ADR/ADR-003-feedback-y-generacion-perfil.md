# ADR-003: Feedback Loop y Generación Automática de Perfil

## Estado
**ACEPTADO** — 2026-07-21

## Contexto
El usuario necesita:
1. Poder **marcar jobs como vistos/aplicados/rechazados** para que el sistema aprenda de sus preferencias
2. Un mecanismo para **generar el `profile.yaml` inicial** sin escribirlo a mano desde su CV, LinkedIn o descripción textual
3. Poder **comparar su experiencia laboral previa** con los requisitos de los jobs

## Decisión

### 1. Feedback CLI
Comando `scripts/feedback.py` con las siguientes operaciones:

| Operación | Comando | Efecto |
|---|---|---|
| Listar | `--list` | Muestra todo el historial de feedback |
| Aplicado | `--apply <url>` | Marca job como postulado. Se excluye de futuras búsquedas |
| Rechazado | `--reject <url>` | Marca job como no interesante. Peso negativo |
| Visto | `--seen <url>` | Marca job como ya visto. Se excluye |
| Puntuar | `--rate <url> <1-10>` | Rating manual para ajustar preferencias |
| Estadísticas | `--stats` | Muestra métricas de feedback |

Los datos se guardan en `output/feedback.json` (gitignored).

### 2. Generación de Perfil Asistida por IA
Skill `skills/generar-perfil.md` que acepta como input:
- **LinkedIn URL** → usa MCP server `linkedin-mcp-server` para extraer perfil
- **CV (PDF/Word)** → parsea el documento y extrae skills/experiencia
- **Descripción textual** → NLP simple para estructurar la información

El output es un `profile.yaml` completo con `experience_history` incluido.

### 3. Experience History en el Ranking
Se agrega `experience_history` al perfil con roles anteriores (empresa, stack, descripción). El ranker compara el stack usado en experiencia previa contra los requisitos del job.

**Fórmula**: `experience_score = (techs_en_historial_que_matchen_con_job / total_techs_en_historial) * 120`

Esto da una bonificación a jobs que requieren stacks que el usuario ya usó profesionalmente.

## Fuentes de Jobs Actualizadas

| Fuente | Método | Estado |
|---|---|---|
| LinkedIn | MCP Server (`@stickerdaniel/linkedin-mcp-server`) | Requiere cookie `li_at` |
| WeWorkRemotely | RSS feed | ✅ Público |
| RemoteOK | API pública | ✅ Sin auth |
| StackOverflow Jobs | Scraping HTML | ✅ Público |

*GitHub Issues descartado por baja calidad de datos.*

## Features Adicionales (V2)

### Multi-Perfil
Soporte para múltiples perfiles via flag `--profile`:
```bash
python scripts/fetch-all.py                    # → profile.yaml
python scripts/fetch-all.py --profile senior   # → profile-senior.yaml
python scripts/fetch-all.py --profile freelance # → profile-freelance.yaml
```

Cada perfil puede tener distinto `salary_mode`, `weighting` y `preferences`.

### Deduplicación
Deduplicación inteligente por título normalizado + empresa. Usa `SequenceMatcher` para detectar variaciones textuales (ej: "Senior .NET Developer" ≈ ".NET Developer Senior").

### Auto-Cleanup
Limpieza automática de resultados anteriores a 15 días al inicio de cada ejecución.

### Terminal Table
Tabla estilizada con `rich` (colores, scores, indicadores de salario). Modo fallback si rich no está instalado.

### Company Research + Interview Prep
Comando `--research <url>` que investiga una empresa y genera tips de entrevista basados en el stack del puesto. Cachea resultados por 7 días.

### Market Stats
Análisis del mercado al final de cada run:
- Tecnologías más demandadas
- Distribución remote/hybrid/onsite
- Empresas que más contratan
- Distribución por fuente

### LinkedIn Cookie Renewal
Skill `renovar-linkedin-cookie.md` que guía al usuario para renovar la cookie `li_at` de LinkedIn usando Browser MCP (DevTools).

## Consecuencias
- **Positivo**: Feedback permite refinar rankings sin ML complejo
- **Positivo**: `generar-perfil` reduce fricción de onboarding
- **Positivo**: Experience history da matches más relevantes
- **Positivo**: Multi-perfil permite buscar full-time y freelance sin conflictos
- **Positivo**: Market stats dan visibilidad del mercado actual
- **Positivo**: Company research + interview prep ahorran horas de preparación
- **Negativo**: LinkedIn scraping requiere cookie que expira (mitigado con skill renovar)
- **Negativo**: StackOverflow scraping puede romperse si cambian HTML
