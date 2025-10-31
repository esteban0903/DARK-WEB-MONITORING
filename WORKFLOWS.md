# 🤖 GitHub Actions - Automatización CI/CD

Este proyecto incluye **pipelines automáticos** para mantener la base de datos de ransomware actualizada sin intervención manual.

---

## 📋 Workflows Disponibles

### 1. 🤖 Automated Ransomware News Ingestion
**Archivo:** `.github/workflows/daily-ingest.yml`

**Frecuencia:** 3 veces al día
- 🕐 8:00 AM UTC (4:00 AM ET)
- 🕐 2:00 PM UTC (10:00 AM ET)
- 🕐 8:00 PM UTC (4:00 PM ET)

**Qué hace:**
1. ✅ Descarga noticias de 5+ fuentes RSS especializadas
2. 🔍 Filtra solo eventos relevantes de ransomware
3. 🛡️ Analiza eventos sospechosos con VirusTotal + AbuseIPDB
4. 💾 Hace commit automático si encuentra nuevos eventos
5. 📊 Genera reporte de ejecución con estadísticas

**Duración estimada:** 10-30 minutos (dependiendo de eventos nuevos)

**Ejecución manual:**
1. Ve a tu repo → **Actions** tab
2. Selecciona "Automated Ransomware News Ingestion"
3. Clic en **"Run workflow"**
4. (Opcional) Marca "Skip threat intelligence analysis" para más velocidad

---

### 2. 📊 Weekly Deep Analysis Report
**Archivo:** `.github/workflows/weekly-report.yml`

**Frecuencia:** Semanal (Domingos a medianoche UTC)

**Qué hace:**
1. 📊 Genera estadísticas de la última semana
2. 👥 Top 5 actores más activos
3. 📈 Tendencias y métricas clave
4. 📝 Guarda reporte como artifact (30 días de retención)

**Duración estimada:** 2-5 minutos

---

## 🔐 Configuración de Secrets

Los workflows usan **GitHub Secrets** para las API keys. Debes configurar:

1. Ve a: `Settings → Secrets and variables → Actions`
2. Agrega estos secrets:

| Secret Name | Descripción | Dónde obtenerla |
|-------------|-------------|-----------------|
| `GEMINI_API_KEY` | Google Gemini AI API | https://makersuite.google.com/app/apikey |
| `VIRUSTOTAL_API_KEY` | VirusTotal API | https://www.virustotal.com/gui/my-apikey |
| `ABUSEIPDB_API_KEY` | AbuseIPDB API | https://www.abuseipdb.com/account/api |

📚 **Guía detallada:** [API_KEYS_SETUP.md](../API_KEYS_SETUP.md)

---

## 📊 Monitoreo de Ejecuciones

### Ver estado de workflows
1. Ve a tu repositorio en GitHub
2. Clic en la pestaña **"Actions"**
3. Verás historial de ejecuciones:
   - ✅ Verde = Exitoso
   - ❌ Rojo = Error
   - 🟡 Amarillo = En progreso

### Ver logs detallados
1. Clic en cualquier ejecución
2. Clic en el job "ingest-news"
3. Expande cada step para ver logs

### Descargar artifacts (reportes)
1. En la página de una ejecución
2. Scroll abajo a "Artifacts"
3. Descarga:
   - `ingestion-logs-XXX.txt` - Logs completos
   - `weekly-report-XXX.txt` - Reporte semanal

---

## 🎯 Rate Limits y Optimizaciones

### Consumo Estimado de APIs (por ejecución)

| API | Requests por ejecución | Límite diario |
|-----|------------------------|---------------|
| **RSS Feeds** | 13 requests | Sin límite |
| **VirusTotal** | 0-20 requests* | 500/día |
| **AbuseIPDB** | 0-10 requests* | 1000/día |

*Solo para eventos de confianza baja/media

### Estrategias de optimización implementadas

✅ **Caché de resultados** - No re-analiza URLs ya procesadas
✅ **Rate limiting** - Esperas de 15 seg entre requests de VT
✅ **Análisis selectivo** - Solo eventos baja/media confianza
✅ **Timeout de 45 min** - Evita consumir runners eternamente
✅ **Detección de duplicados** - No ingesta URLs repetidas

---

## ⚙️ Personalización de Workflows

### Cambiar frecuencia de ejecución

Edita el `cron` en `.github/workflows/daily-ingest.yml`:

```yaml
schedule:
  - cron: '0 8 * * *'   # Formato: minuto hora día mes día-semana
```

**Ejemplos:**
- Cada hora: `'0 * * * *'`
- Cada 6 horas: `'0 */6 * * *'`
- Solo lunes: `'0 8 * * 1'`
- Cada 30 minutos: `'*/30 * * * *'`

🔧 **Herramienta:** https://crontab.guru/

### Desactivar análisis de threat intelligence

Para ahorrar cuota de APIs, puedes comentar esta sección en `ingest_news.py`:

```python
# Solo analizar con APIs si la confianza es BAJA o MEDIA
# if confianza in ["baja", "media"]:
#     print(f"   🛡️  Analizando con Threat Intel...")
#     ...
```

O ejecutar manualmente con el parámetro `skip_threat_intel: true`

---

## 🚨 Troubleshooting

### Error: "Secret not found"
**Solución:** Verifica que configuraste los 3 secrets en GitHub

### Error: "Rate limit exceeded"
**Solución:** 
- Reduce la frecuencia del workflow (1-2 veces al día)
- Usa el parámetro `skip_threat_intel: true`

### Error: "Permission denied"
**Solución:** 
1. Ve a `Settings → Actions → General`
2. En "Workflow permissions", selecciona:
   - ✅ "Read and write permissions"
   - ✅ "Allow GitHub Actions to create and approve pull requests"

### No se hacen commits automáticos
**Solución:** Verifica que hay eventos nuevos:
- El workflow solo hace commit si `data/eventos.csv` cambia
- Si no hay noticias nuevas, no habrá commit (esto es normal)

---

## 📈 Métricas de Performance

### Histórico de ejecuciones

Puedes ver métricas en la pestaña **Actions**:
- ⏱️ Tiempo promedio de ejecución
- ✅ Tasa de éxito
- 📊 Eventos agregados por día/semana

### Ejemplo de Summary
Cada ejecución genera un summary visible en GitHub:

```
📊 Ingestion Summary

✅ Status: Success
📰 New Events: 15
🕐 Timestamp: 2025-10-30 14:23 UTC
🔄 Run: #42
```

---

## 🔄 Mantenimiento

### Actualizar dependencias
```bash
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt
git commit -am "⬆️ Update dependencies"
git push
```

### Rotar API keys
1. Genera nuevas keys en los portales respectivos
2. Actualiza los GitHub Secrets
3. Las nuevas keys se usarán en la próxima ejecución

---

## 📚 Referencias

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Cron Schedule](https://crontab.guru/)
- [GitHub Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
