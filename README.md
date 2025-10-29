# Dark Web / OSINT — Ransomware Monitor (Demo)

Proyecto mínimo funcional para monitorear y presentar (bonito) eventos relacionados con ransomware usando **datos OSINT públicos** (o simulados).

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

## Ideas de mejora
- Conexión a feeds públicos (MISP/OTX) y normalización.
- Scoring de confianza por fuente.
- Exportación a PDF/imagen desde el dashboard.
