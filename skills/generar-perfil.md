# 🤖 Skill: Generar Perfil de Job Finder

> Genera automáticamente el archivo `profile.yaml` de **Job Finder** a partir de tu CV (PDF/Word), perfil de LinkedIn, o descripción de experiencia.

## 📋 Descripción

Esta skill toma tu CV, perfil de LinkedIn o descripción textual de tu experiencia y genera un archivo `profile.yaml` listo para usar con **Job Finder**. Extrae automáticamente:

- Datos personales (nombre, email, ubicación)
- Stack tecnológico (lenguajes, frameworks, databases, cloud, tools)
- Nivel de seniority y años de experiencia
- Experiencia laboral detallada (rol, empresa, stack usado, período)
- Preferencias de búsqueda (remoto, salario, keywords a excluir)

---

## 🔄 Proceso (cómo funciona)

### Opción 1: Desde CV (PDF/Word) — RECOMENDADA

Usa el **MCP server `markitdown`** (ya configurado en `opencode.json`) para convertir el documento a Markdown, y luego el agente AI extrae la estructura.

**Pasos:**

1. **Convertir el documento** con markitdown:
   ```
   El agente usa la tool convert_to_markdown(uri) del MCP markitdown
   uri = file:///ruta/a/tu/cv.pdf
   ```
   O manualmente:
   ```bash
   pip install 'markitdown[pdf]'
   python -c "from markitdown import MarkItDown; print(MarkItDown().convert('cv.pdf').text_content)" > output/cv-extracted.md
   ```

2. **El agente extrae la estructura** del markdown:
   - Datos personales (regex + NLP sobre header del CV)
   - Stack tecnológico (sección "Skills" del CV)
   - Experiencia laboral (sección "Experience", parseo de roles/empresas/períodos)

3. **El agente genera `profile.yaml`** con la estructura completa.

4. **Validación cruzada**: el agente compara contra un perfil existente (si lo hay) y reporta tecnologías nuevas detectadas que faltaban.

**✅ Caso de uso real (validado 2026-07-21):**
```
CV: hernan-horacio-cv-angular-net.pdf
→ markitdown extrajo 5,938 caracteres con estructura preservada
→ Se detectaron 12 tecnologías adicionales no presentes en el perfil manual
  (Dapper, LINQ, IIS, Oracle, GitLab CI, BitBucket, Swagger, 
   Application Insights, OpenTelemetry, ASP.NET Identity, JWT, Razor)
→ Perfil enriquecido → mejor stack_match en el ranking
```

### Opción 2: Desde LinkedIn URL
```
Pegá el link de tu perfil de LinkedIn. El agente usa el MCP server
linkedin-mcp-server para scrapear tu perfil y extraer experiencia.
(Requiere cookie li_at configurada — ver skills/renovar-linkedin-cookie.md)
```

### Opción 3: Descripción manual
```
Contale al agente tu experiencia y stack en lenguaje natural.
Ej: "Soy Senior .NET/Angular developer con 8 años de exp,
trabajo en BEON.Tech, stack: C#, TypeScript, Angular, Azure, PostgreSQL"
```

---

## 📤 Output generado

La skill genera (o actualiza) el archivo `profile.yaml` en la raíz del proyecto:

```yaml
profile:
  name: "Hernán Horacio López"
  github_handle: "hlopez94"
  description: "Senior Full Stack .NET Engineer | .NET · Angular"
  email: "hernan.lopez@devher.online"
  location: "Paraná, Argentina"

  preferred_stack:
    languages: [".NET", "C#", "TypeScript"]
    frameworks: ["Angular", "ASP.NET Core", "Blazor", "SignalR", "Razor"]
    databases: ["SQL Server", "PostgreSQL", "Redis", "Oracle", "Dapper", "EF Core"]
    cloud: ["Azure", "AWS"]
    tools: ["Docker", "Kubernetes", "GitHub Actions", "OAuth", ...]
    methodologies: ["Clean Architecture", "DDD", "CQRS", "TDD"]

  experience:
    level: "Senior"
    years: 8

  experience_history:
    - role: "Senior Software Engineer"
      company: "BEON.Tech"
      location: "Remote"
      years: "Jun 2025 — Presente"
      stack: [".NET 10", "Angular", "AWS", "TypeScript", "PostgreSQL"]
      description: "..."
    # ... más roles

  preferences:
    remote_only: true
    salary_mode: "monthly"
    min_salary: 6500
    max_salary: 9000
    exclude_keywords: ["python", "php", "wordpress", ...]

  weighting:
    stack_match: 0.35
    experience_match: 0.15
    seniority_match: 0.15
    salary_match: 0.15
    remote_match: 0.10
    recency: 0.10
```

---

## 💡 Tips para mejores resultados

| Tip | Por qué |
|---|---|
| **Más tecnologías = mejor matching** | El `stack_match` del ranker busca keywords del perfil en las ofertas. Cuantas más tecnologías reales tengas, más preciso el score |
| **Incluí herramientas "menores"** | Cosas como `Dapper`, `Swagger`, `OpenTelemetry` aparecen en ofertas y suman puntos |
| **Revisá el `experience_history`** | El ranker lo usa para `experience_match` — jobs con stacks que ya usaste puntúan más alto |
| **Generá los 3 perfiles** | `profile.yaml`, `profile-senior.yaml`, `profile-freelance.yaml` con distinto salary_mode |

---

## 🔄 Después de generar

1. **Revisá y ajustá** los valores generados (salary, remote, excludes)
2. **Ejecutá** `python scripts/fetch-all.py` para buscar jobs
3. **Ajustá los `weighting`** si querés cambiar prioridades
4. **Usá el feedback loop** para refinar: `python scripts/feedback.py --apply/reject/rate`

---

## 🔒 Privacidad

- `profile.yaml` y `profile-*.yaml` están en `.gitignore` — **nunca se suben al repo**
- El CV procesado se guarda en `output/` (también gitignored)
- Solo los templates (`*.template.yaml`) se comparten públicamente
