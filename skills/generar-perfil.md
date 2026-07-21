# 🤖 Skill: Generar Perfil de Job Finder

> Genera automáticamente el archivo `profile.yaml` de **Job Finder** a partir de tu CV (PDF/Word), perfil de LinkedIn, o descripción de experiencia.

## 📋 Descripción

Esta skill toma tu CV, perfil de LinkedIn o descripción textual de tu experiencia y genera un archivo `profile.yaml` listo para usar con **Job Finder**. Extrae automáticamente:

- Stack tecnológico (lenguajes, frameworks, databases, cloud, tools)
- Nivel de seniority y años de experiencia
- Experiencia laboral detallada (rol, empresa, stack usado)
- Preferencias de búsqueda (remoto, salario, etc.)

## 🚀 Cómo usar

### Opción 1: Desde LinkedIn URL
```
Pegá el link de tu perfil de LinkedIn y esta skill lo parsea 
(vía el MCP server linkedin-mcp-server) para extraer tu experiencia.
```

### Opción 2: Desde CV (PDF/Word)
```
Subí tu CV en PDF o Word. La skill extrae:
• Habilidades técnicas
• Experiencia laboral
• Educación
• Certificaciones
```

### Opción 3: Descripción manual
```
Contame tu experiencia y stack, y la skill genera el perfil.
Ej: "Soy Senior .NET/Angular developer con 8 años de exp,
trabajo en BEON.Tech, stack: C#, TypeScript, Angular, Azure, PostgreSQL"
```

## 📤 Output

La skill genera (o actualiza) el archivo `profile.yaml` en la raíz del proyecto con esta estructura:

```yaml
profile:
  name: "Tu Nombre"
  github_handle: "tu-user"
  description: "Senior .NET/Angular developer"
  preferred_stack:
    languages: [".NET", "C#", "TypeScript", "Python"]
    frameworks: ["Angular", "ASP.NET Core", "Blazor"]
    databases: ["PostgreSQL", "SQL Server", "Redis"]
    cloud: ["Azure", "AWS"]
    tools: ["Docker", "Kubernetes", "GitHub Actions"]
    methodologies: ["Clean Architecture", "DDD", "CQRS"]
  experience:
    level: "Senior"
    years: 8
  experience_history:
    - role: "Senior Software Engineer"
      company: "BEON.Tech"
      years: "2021-presente"
      stack: [".NET", "Angular", "Azure", "TypeScript", "PostgreSQL"]
      description: "Desarrollo SaaS multi-tenant, Clean Architecture"
  preferences:
    remote_only: true
    min_salary_usd: 80000
    max_salary_usd: 150000
    exclude_keywords: ["blockchain", "crypto"]
  weighting:
    stack_match: 0.35
    experience_match: 0.15
    seniority_match: 0.15
    salary_match: 0.15
    remote_match: 0.10
    recency: 0.10
```

## 🔄 Después de generar

1. Revisá y ajustá los valores generados
2. Ejecutá `python scripts/fetch-all.py` para buscar jobs
3. Ajustá los `weighting` si querés cambiar prioridades
4. Usá `python scripts/feedback.py --apply/reject/rate` para refinar
