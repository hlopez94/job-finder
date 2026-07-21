# Glosario del Dominio — Job Finder

> Lenguaje ubicuo del proyecto. Toda comunicación y código debe usar estos términos.

| Término | Definición | Sinónimos / Notas |
|---|---|---|
| **Job** | Oferta de trabajo publicada en una fuente (GitHub, LinkedIn, etc.) | Position, Job Posting, Vacancy |
| **Source** | Plataforma o sitio web de donde se extraen jobs | Feeds, Origin |
| **Profile** | Documento YAML que describe las skills, experiencia y preferencias del usuario | — |
| **Scraper** | Script que extrae jobs de una source específica | Crawler, Fetcher, Source Adapter |
| **Ranking** | Score numérico (0–100) que indica qué tan bien un job matchea con el profile | Score, Match % |
| **Weight** | Coeficiente de ponderación para cada dimensión del ranking (stack, salary, etc.) | Weighting factor |
| **Match** | Resultado del ranking ≥ threshold configurable | Coincidencia, Hit |
| **Notification** | Mensaje enviado por Telegram con los top matches | Alert, Digest |
| **Run** | Ejecución completa del pipeline: fetch → rank → notify → report | Session, Execution |
| **Output** | Directorio con resultados de cada run, organizado por fecha | Report, Artifact |
| **Skill** | Archivo `.md` que define cómo usar job-finder como una skill de agente | — |
| **Digest** | Resumen de los top jobs enviados al usuario | Summary, Briefing |
| **Feedback** | Acción del usuario para mejorar rankings futuros (apply, reject, seen) | — |
