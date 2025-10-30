# Dark Web / OSINT — Ransomware Monitor (Demo)

Proyecto mínimo funcional para monitorear y analizar **ataques reales de ransomware** usando:
- 📰 **Datos OSINT públicos** (Google News RSS)
- 🤖 **Análisis automático con Gemini AI**
- 🎯 **Framework MITRE ATT&CK** para identificación de técnicas
- 🔍 **Extracción de IoCs** (IPs, dominios, hashes)

## ✨ Características Principales

### 🔍 Filtrado Inteligente
- Solo captura noticias sobre **ataques reales confirmados**
- Filtra por palabras clave específicas (attack, breach, victim, leaked, etc.)
- Búsquedas especializadas en grupos ransomware conocidos

### 🤖 Análisis con Gemini AI
Cada noticia puede ser analizada con Gemini 2.5 Flash para extraer:
- 👤 Autor y fuente de la noticia
- 🎭 Grupo/Actor de amenaza y nivel de sofisticación
- 🏢 Víctimas (organización, sector, país)
- 🔴 Nivel de criticidad (Crítico/Alto/Medio/Bajo)
- 🎯 Modus operandi con mapeo a MITRE ATT&CK
- 🔍 Indicadores de Compromiso (IPs, dominios, hashes, emails)
- 🛡️ Soluciones y mitigación recomendadas
- 📊 Resumen ejecutivo

### 📊 Dashboard Interactivo
- Timeline de eventos
- Top actores de amenaza
- Distribución por confianza
- Filtros avanzados (fecha, actor, tipo, búsqueda)
- Descarga de datos filtrados

## Estructura
```
darkweb_monitor/
├─ data/
│  └─ eventos.csv
├─ app.py
├─ analysis.py
├─ requirements.txt
└─ README.md
```

## Cómo correr
1) Crear entorno e instalar dependencias:
```
pip install -r requirements.txt
```
2) Ejecutar Streamlit:
```
streamlit run app.py
```
3) Abrir el enlace local que muestre la consola (por defecto http://localhost:8501).

## Dataset
- Edita `data/eventos.csv` para agregar eventos reales **de fuentes públicas**.
- Columnas:
  - `fecha` (YYYY-MM-DD)
  - `actor` (LockBit, Qilin, BlackCat, etc.)
  - `fuente` (noticia pública, blog técnico, etc.)
  - `tipo` (mención, leak, rumor...)
  - `indicador` (palabras clave, IoCs públicos)
  - `url` (enlace a la fuente pública)
  - `confianza` (alta, media, baja)

## Avisos legales y éticos
- Solo utilizar **fuentes públicas** y de acceso abierto.
- No interactuar ni acceder a foros privados/ilegales.
- Validar la **autenticidad** de la información antes de tomar decisiones.
- Este demo es educativo y no sustituye un SOC ni una plataforma de TI.
