# 🔐 Configuración de API Keys

Este proyecto utiliza varias APIs externas para análisis de inteligencia de amenazas. Sigue estos pasos para configurar tus credenciales de forma segura.

## 📋 APIs Utilizadas

1. **Google Gemini AI** - Análisis inteligente de noticias de ransomware
2. **VirusTotal** - Verificación de URLs y dominios maliciosos
3. **AbuseIPDB** - Verificación de IPs comprometidas

## 🚀 Configuración Rápida

### 1. Copiar el archivo de plantilla

```bash
cp .env.example .env
```

### 2. Editar el archivo `.env` con tus API keys

Abre el archivo `.env` y reemplaza los valores de ejemplo con tus API keys reales:

```bash
# Google Gemini AI API Key
GEMINI_API_KEY=tu_gemini_api_key_aqui

# VirusTotal API Key
VIRUSTOTAL_API_KEY=tu_virustotal_api_key_aqui

# AbuseIPDB API Key
ABUSEIPDB_API_KEY=tu_abuseipdb_api_key_aqui
```

## 🔑 Cómo Obtener las API Keys

### Google Gemini AI

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en "Create API Key"
4. Copia la key y pégala en `.env`

**Límites:** 60 requests/minuto (Free tier)

---

### VirusTotal

1. Ve a [VirusTotal](https://www.virustotal.com/gui/join-us)
2. Crea una cuenta gratuita
3. Ve a tu perfil → [API Key](https://www.virustotal.com/gui/my-apikey)
4. Copia la key y pégala en `.env`

**Límites:** 4 requests/minuto, 500/día (Free tier)

---

### AbuseIPDB

1. Ve a [AbuseIPDB](https://www.abuseipdb.com/register)
2. Crea una cuenta gratuita
3. Ve a tu cuenta → [API](https://www.abuseipdb.com/account/api)
4. Copia la key y pégala en `.env`

**Límites:** 1,000 requests/día (Free tier)

---

## ⚠️ Seguridad

### ✅ Buenas Prácticas

- ✅ **NUNCA** subas el archivo `.env` a GitHub
- ✅ El archivo `.env` ya está en `.gitignore`
- ✅ Usa `.env.example` como plantilla (este SÍ se sube a GitHub)
- ✅ Rota tus API keys periódicamente
- ✅ No compartas tus keys en Slack, Discord, etc.

### 🔒 GitHub Secrets (Para CI/CD)

Si quieres usar GitHub Actions en el futuro:

1. Ve a tu repositorio → Settings → Secrets and variables → Actions
2. Haz clic en "New repository secret"
3. Agrega cada key:
   - Nombre: `GEMINI_API_KEY`
   - Valor: tu key
   - Repite para `VIRUSTOTAL_API_KEY` y `ABUSEIPDB_API_KEY`

---

## 🧪 Verificar Configuración

Ejecuta este comando para probar que las APIs funcionan:

```bash
python threat_intel_apis.py
```

Deberías ver:

```
============================================================
🧪 TEST - Threat Intelligence APIs
============================================================

📝 Test 1: URL conocida (bleepingcomputer)
   Resultado: {'malicious': 0, 'suspicious': 0, 'clean': 0, 'score': 0}

📝 Test 2: IP de ejemplo
   Resultado: {'abuse_score': 0, 'total_reports': 169, 'is_whitelisted': True}

✅ Tests completados
```

---

## 🆘 Troubleshooting

### Error: "⚠️ GEMINI_API_KEY no encontrada"

**Solución:** Asegúrate de que:
1. El archivo `.env` existe en la raíz del proyecto
2. La key está correctamente escrita sin espacios extras
3. El formato es: `GEMINI_API_KEY=tu_key_aqui` (sin comillas)

### Error: "KeyboardInterrupt" o timeout

**Solución:** Puede ser un problema de red o rate limit. Espera 1 minuto y vuelve a intentar.

### Error: "API key invalid"

**Solución:** 
1. Verifica que copiaste la key completa
2. Verifica que la key no haya expirado
3. Genera una nueva key desde el portal de la API

---

## 📚 Documentación Adicional

- [Gemini API Docs](https://ai.google.dev/docs)
- [VirusTotal API Docs](https://developers.virustotal.com/reference/overview)
- [AbuseIPDB API Docs](https://docs.abuseipdb.com/)
