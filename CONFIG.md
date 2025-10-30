# Configuración del Sistema de Monitoreo de Ransomware

## 🎯 Objetivo del Sistema

Este sistema monitorea y analiza **únicamente noticias sobre ataques reales de ransomware**, filtraciones de datos, y amenazas confirmadas. No incluye noticias genéricas sobre ciberseguridad.

## 🔍 Criterios de Filtrado de Noticias

### Búsquedas Específicas
El sistema busca noticias con los siguientes términos:
- `LockBit ransomware attack`
- `Qilin ransomware attack`
- `BlackCat ransomware attack`
- `ransomware data breach`
- `ransomware victim`
- `ransomware leak site`
- `cybercrime data exfiltration`
- `ransomware threat actor`

### Palabras Clave Requeridas
Una noticia debe contener **al menos 2** de estas palabras clave para ser incluida:
- attack, breach, victim, infected, encrypted
- leaked, stolen, compromised, hacked
- infiltrated, exfiltrated, data dump
- dark web, threat actor, malware, exploit

## 🤖 Análisis con Gemini AI

El sistema utiliza **Gemini 2.5 Flash** para analizar cada noticia y extraer:

### 1. Información de la Fuente
- Autor y medio de comunicación
- Fecha de publicación

### 2. Identificación del Actor
- Nombre del grupo ransomware
- Alias conocidos
- Nivel de sofisticación

### 3. Víctima(s)
- Organización afectada
- Sector/Industria
- País/Región
- Tamaño de la empresa

### 4. Nivel de Criticidad
- Clasificación: CRÍTICO/ALTO/MEDIO/BAJO
- Justificación técnica
- Impacto estimado

### 5. Modus Operandi (MITRE ATT&CK)
- Vector de entrada inicial
- Técnicas MITRE ATT&CK identificadas
- Descripción secuencial del ataque

### 6. Indicadores de Compromiso (IoCs)
- ✅ IPs sospechosas
- ✅ Dominios maliciosos
- ✅ URLs maliciosas
- ✅ Hashes de malware (MD5, SHA-1, SHA-256)
- ✅ Nombres de archivos maliciosos
- ✅ Emails comprometidos
- ✅ Otros IoCs técnicos

### 7. Soluciones y Mitigación
- Acciones inmediatas
- Parches necesarios (CVEs)
- Controles de seguridad (Detección, Prevención, Respuesta)
- Referencias a guías oficiales

### 8. Resumen Ejecutivo
- Resumen conciso para directivos

## 🔐 API Key de Gemini

La API key está configurada en: `gemini_analyzer.py`
```
AIzaSyAgILdcUFng3HiepvL5xVMPHnd0vmckidk
```

## 📊 Modelo MITRE ATT&CK

El sistema mapea las técnicas de ataque al framework MITRE ATT&CK:
- **TA0001** Initial Access
- **TA0002** Execution
- **TA0003** Persistence
- **TA0005** Defense Evasion
- **TA0006** Credential Access
- **TA0008** Lateral Movement
- **TA0010** Exfiltration
- **TA0011** Impact

## 🚀 Uso

### Ingestar nuevas noticias:
```bash
python ingest_news.py
```

### Ejecutar el dashboard:
```bash
python -m streamlit run app.py
```

### Analizar una noticia:
1. Abre el dashboard en http://localhost:8501
2. Busca el evento que te interese
3. Haz clic en "🤖 Analizar"
4. Espera el análisis completo de Gemini

## 📝 Notas

- Solo se analizan noticias de **fuentes públicas** y **acceso abierto**
- No se interactúa con foros privados o ilegales
- Toda la información debe ser validada antes de tomar decisiones operativas
