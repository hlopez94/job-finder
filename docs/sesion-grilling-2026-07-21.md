# Sesión de Grilling — 21 Julio 2026

> Sesión de domain modeling para el proyecto **Job Finder**

## 🧠 Problema
Buscar ofertas de trabajo que matcheen con mi perfil técnico es tedioso. Hay múltiples fuentes, poco rankeo inteligente, y configurar alertas en cada portal es una pérdida de tiempo.

## 🎯 Solución Propuesta
Un sistema local (CLI) que:
1. Busque ofertas en múltiples fuentes (GitHub Issues, LinkedIn, WeWorkRemotely)
2. Las rankee según un perfil YAML configurable
3. Notifique por Telegram las mejores coincidencias
4. Guarde resultados históricos por fecha

## 🧩 User Persona
- **Nombre**: Dev Senior .NET/Angular
- **Stack**: C#, TypeScript, Angular, Azure, PostgreSQL
- **Preferencias**: Remoto, Senior, USD 80k-150k
- **Pain**: Revisar N portales de jobs diariamente

## 🔥 Preguntas Clave (Grilling)

### Ronda 1 — Core
1. ¿Usuario único o multi? → Primero personal, luego compartible
2. ¿App o skill? → Skill ejecutable vía CLI
3. ¿Qué define un match? → Stack, seniority, salary, remoto, recencia

### Ronda 2 — Fuentes
4. ¿Qué fuentes? → GitHub Issues, LinkedIn, WeWorkRemotely
5. ¿Perfil? → YAML editable manualmente
6. ¿Ejecución? → Local (Python CLI)

### Ronda 3 — Privacidad
7. Datos personales → profile.yaml + config.yaml (gitignored)
8. Templates → profile.template.yaml + config.template.yaml

### Ronda 4 — Output
9. Notificación → Telegram
10. Ranking → Weighted scoring (sin ML)

## 🏗️ Decisiones Tomadas
- **Stack**: Python 3.11+ (scripts), YAML (config)
- **No app web**: CLI es suficiente
- **No ML**: Weighted scoring es más predecible y configurable
- **Un solo repo**: público con gitignore para datos privados
- **Obsidian Vault**: Documentación del proyecto en el mismo repo

## 📝 Próximos Pasos
- [ ] Probar GitHub Issues scraper con token real
- [ ] Configurar MCP LinkedIn Scraper
- [ ] Crear bot de Telegram y probar notificaciones
- [ ] Ejecutar primera búsqueda real
