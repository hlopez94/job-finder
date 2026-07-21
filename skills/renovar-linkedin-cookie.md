# 🍪 Skill: Renovar LinkedIn Cookie

> Verifica y renueva automáticamente la cookie `li_at` de LinkedIn usando el Browser MCP.

## 📋 Descripción

La cookie `li_at` de LinkedIn **expira periódicamente**. Cuando esto pasa, el scraper de LinkedIn deja de funcionar. Esta skill:

1. **Verifica** si la cookie actual sigue siendo válida
2. **Abre LinkedIn** en el navegador (via Browser MCP)
3. **Extrae** la nueva cookie `li_at` de la sesión activa
4. **Actualiza** la variable de entorno o el archivo de configuración

## 🚀 Cómo usar

### Estado de la cookie
```
Ejecutá fetch-all.py y fijate si LinkedIn falla con:
  ⚠️ LinkedIn no configurado
  ⚠️ LinkedIn: email/password no configurados
Si LinkedIn no trae resultados, probablemente la cookie expiró.
```

### Renovar (automático con Browser MCP)

**Opción 1: Con Playwright/Browser MCP**
```
1. Abrí LinkedIn en el navegador: https://linkedin.com/login
2. Iniciá sesión manualmente (2FA si es necesario)
3. Ejecutá en DevTools (F12 → Console):
   document.cookie.split('; ').find(c => c.startsWith('li_at=')).split('=')[1]
4. Copiá el valor y ejecutá:
   $env:LINKEDIN_LI_AT_COOKIE = "nuevo-valor"
```

**Opción 2: Script automatizado**
```python
# Pseudocódigo para renovación automática vía Browser MCP:
# 1. Navegar a linkedin.com/login
# 2. Completar email y password
# 3. Esperar redirección al feed
# 4. Extraer cookie li_at
# 5. Guardar en variable de entorno
```

## 🔧 Configuración post-renovación

```bash
# Windows PowerShell
$env:LINKEDIN_LI_AT_COOKIE = "nueva-cookie-aqui"

# Para persistir, agregar al perfil de PowerShell:
# $PROFILE → Add-Content $PROFILE '$env:LINKEDIN_LI_AT_COOKIE = "..."'

# O en .env.local (ya está en .gitignore)
echo "LINKEDIN_LI_AT_COOKIE=nueva-cookie" >> .env.local
```

## 🔍 Verificar que funciona

```bash
python scripts/fetch-all.py --profile senior --no-telegram --no-cleanup
```

Si LinkedIn ahora muestra resultados, la cookie funciona ✅

## ⏰ Frecuencia de expiración

- **Cookie `li_at`**: suele durar entre 7 y 30 días
- Recomendación: renovar cada **15 días** o ante el primer error
- Una skill de programación tipo `recordatorio-linkedin-cookie` podría avisarte
