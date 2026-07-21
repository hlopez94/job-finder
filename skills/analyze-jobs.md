# Skill: Analyze Jobs (Geo-Filter + Quality Filter)

## Propósito
Analizar resultados de job scraping con IA para filtrar ofertas geo-restringidas
y mejorar la calidad del ranking. El Python hace el scraping, la IA analiza.

## Cuándo usar
- Después de ejecutar `python scripts/fetch-all.py`
- Cuando el usuario dice: "analiza los resultados", "filtra por LATAM", "cuáles puedo aplicar"
- Para decidir qué jobs son realmente aplicables desde Argentina

## Flujo

### Paso 1: Leer resultados
```
Leer output/$(fecha)/results.json
```

### Paso 2: Analizar cada job
Para CADA job en `top_results`, analizar:

1. **Geo-restricción**: ¿Está restringido a un país/región?
   - Keywords de restricción: "US only", "US authorization", "US citizenship", "must be located in US", "Europe only", "UK only", "Canada only", "Australia only"
   - Keywords amigables LATAM: "Worldwide", "Global", "Anywhere", "LATAM", "Latin America", "South America", "Argentina", "Remote (Global)"
   - Si no hay info clara → marcar como "unknown" (potencialmente aplicable)

2. **Tipo de contrato**: ¿Es full-time, contract, freelance?
   - El usuario busca: full-time Y freelance
   - Si es "contract-to-hire" o "temp" → marcar pero no descartar

3. **Nivel de seniority**: ¿Matchea con el perfil?
   - Senior/Staff/Lead → OK para perfil senior
   - Junior/Mid → descartar

4. **Stack relevance**: ¿El stack es relevante?
   - .NET, C#, Angular, TypeScript, Blazor → core
   - React, Node, Python → secundario
   - Go, Rust, PHP → probablemente no match

### Paso 3: Clasificar
Cada job recibe una de estas etiquetas:
- ✅ **APLICAR**: Geo-compatible + stack relevante + seniority OK
- ⚠️ **REVISAR**: No hay info clara de geo o stack parcial
- ❌ **DESCARTAR**: Geo-restringido o stack no relevante o seniority incorrecto

### Paso 4: Output
Producir:
1. Lista filtrada de jobs ✅ + ⚠️
2. Resumen de cuántos se descartaron y por qué
3. Opcionalmente: enviar notificación Telegram solo con los ✅

## Formato de análisis

```markdown
## Análisis de Jobs — $(fecha)

### Resumen
- Total analizados: X
- ✅ Aplicar: Y
- ⚠️ Revisar: Z
- ❌ Descartar: W

### ✅ Aplicar (listos para postularse)
| # | Job | Empresa | Razón | Link |
|---|-----|---------|-------|------|

### ⚠️ Revisar (verificar detalles)
| # | Job | Empresa | Preocupación | Link |
|---|-----|---------|-------------|------|

### ❌ Descartar (no aplican)
| # | Job | Empresa | Razón de descarte | Link |
|---|-----|---------|------------------|------|
```

## Templates de análisis

### Detección de geo-restricción
```
Patrones de RESTRICCIÓN (❌):
- "US only", "US-based only", "United States only"
- "Must be authorized to work in the US"
- "US citizenship required", "US work authorization"
- "Must be located in [país no-LATAM]"
- "Europe only", "EU only", "UK only"
- "Canada only", "Australia only"

Patrones de COMPATIBILIDAD (✅):
- "Worldwide", "Global", "Anywhere"
- "LATAM", "Latin America", "South America"
- "Argentina"
- "Remote (Global)", "Fully Remote"
- "No location requirement"
- "Open to worldwide candidates"

Sin info clara → ⚠️ REVISAR (asumir que puede ser aplicable)
```

### Detección de seniority
```
Senior/Staff/Lead/Principal → ✅ para perfil senior
Mid-level/Junior/Entry → ❌ descartar
```

### Detección de stack
```
Core (match alto): .NET, C#, ASP.NET, Blazor, Angular, TypeScript, Entity Framework
Secundario (match medio): React, Node.js, Python, SQL Server, PostgreSQL, Docker, Kubernetes
Bajo match: Go, Rust, PHP, Ruby, Swift, Kotlin, Java (salvo que combine con .NET)
```
