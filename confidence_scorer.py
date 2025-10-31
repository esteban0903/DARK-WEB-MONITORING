"""
Sistema de Scoring de Confiabilidad para noticias de ransomware
Evalúa múltiples factores para determinar si una noticia es alta, media o baja confianza
"""

from urllib.parse import urlparse
from datetime import datetime
import re

# Dominios de fuentes altamente confiables (medios reconocidos, instituciones oficiales)
DOMINIOS_ALTA_CONFIANZA = {
    # Medios internacionales top-tier
    "reuters.com", "bbc.co.uk", "bbc.com", "nytimes.com", "wsj.com",
    "theguardian.com", "washingtonpost.com", "apnews.com", "bloomberg.com",
    "ft.com", "economist.com", "cnn.com", "nbcnews.com", "cbsnews.com",
    
    # Medios especializados en tecnología/seguridad
    "wired.com", "arstechnica.com", "techcrunch.com", "zdnet.com",
    "theverge.com", "bleepingcomputer.com", "securityweek.com",
    
    # Sitios especializados en ciberseguridad
    "krebs.com", "krebsonsecurity.com", "darkreading.com", 
    "therecord.media", "cyberscoop.com", "threatpost.com",
    
    # Instituciones oficiales
    "cisa.gov", "fbi.gov", "ic3.gov", "cert.org", "nist.gov",
    "europol.europa.eu", "ncsc.gov.uk",
    
    # Medios españoles reconocidos
    "elpais.com", "elmundo.es", "abc.es", "lavanguardia.com",
}

# Dominios de confianza media (blogs técnicos, medios regionales)
DOMINIOS_MEDIA_CONFIANZA = {
    "medium.com", "substack.com", "hackernoon.com", "dev.to",
    "linkedin.com", "github.com", "reddit.com", "twitter.com",
    "infosecurity-magazine.com", "securityintelligence.com",
}

# Indicadores de contenido técnico confiable
INDICADORES_TECNICOS = [
    "CVE-", "MITRE ATT&CK", "IOC", "indicator of compromise",
    "malware sample", "hash", "IP address", "command and control",
    "C2 server", "TTPs", "forensic analysis", "incident response",
    "vulnerability", "exploit", "payload", "encryption algorithm",
]

# Indicadores de fuentes oficiales
INDICADORES_OFICIALES = [
    "press release", "official statement", "government agency",
    "law enforcement", "FBI", "CISA", "Europol", "advisory",
    "security bulletin", "threat intelligence", "CERT",
]

# Indicadores de baja calidad
INDICADORES_BAJA_CALIDAD = [
    "clickbait", "you won't believe", "shocking", "unconfirmed",
    "rumor", "alleged", "speculation", "anonymous source",
    "breaking news", "exclusive leak",
]


def evaluar_dominio(url: str) -> tuple[int, str]:
    """
    Evalúa el dominio de la URL
    Retorna: (puntos, razón)
    """
    if not url:
        return (0, "Sin URL")
    
    try:
        domain = urlparse(url).netloc.lower()
        domain = domain.replace("www.", "")
        
        # Alta confianza: +40 puntos
        if any(d in domain for d in DOMINIOS_ALTA_CONFIANZA):
            return (40, f"Fuente reconocida: {domain}")
        
        # Media confianza: +20 puntos
        if any(d in domain for d in DOMINIOS_MEDIA_CONFIANZA):
            return (20, f"Fuente técnica: {domain}")
        
        # Dominios sospechosos: -20 puntos
        if any(x in domain for x in [".xyz", ".tk", ".ml", "bit.ly", "tinyurl"]):
            return (-20, f"Dominio sospechoso: {domain}")
        
        # Blogs personales o sitios desconocidos: 0 puntos
        return (0, f"Fuente desconocida: {domain}")
    
    except Exception:
        return (0, "Error al parsear URL")


def evaluar_contenido_tecnico(titulo: str, descripcion: str) -> tuple[int, str]:
    """
    Evalúa si el contenido tiene indicadores técnicos
    Retorna: (puntos, razón)
    """
    texto = f"{titulo} {descripcion}".lower()
    
    # Buscar indicadores técnicos
    indicadores_encontrados = [ind for ind in INDICADORES_TECNICOS if ind.lower() in texto]
    
    if len(indicadores_encontrados) >= 3:
        return (30, f"Contenido técnico detallado ({len(indicadores_encontrados)} indicadores)")
    elif len(indicadores_encontrados) >= 1:
        return (15, f"Contiene indicadores técnicos ({len(indicadores_encontrados)})")
    else:
        return (0, "Sin indicadores técnicos")


def evaluar_fuente_oficial(titulo: str, descripcion: str) -> tuple[int, str]:
    """
    Evalúa si es una fuente oficial (gobierno, agencias)
    Retorna: (puntos, razón)
    """
    texto = f"{titulo} {descripcion}".lower()
    
    indicadores_encontrados = [ind for ind in INDICADORES_OFICIALES if ind.lower() in texto]
    
    if len(indicadores_encontrados) >= 2:
        return (25, "Fuente oficial confirmada")
    elif len(indicadores_encontrados) >= 1:
        return (10, "Posible fuente oficial")
    else:
        return (0, "No es fuente oficial")


def evaluar_calidad_contenido(titulo: str, descripcion: str) -> tuple[int, str]:
    """
    Detecta indicadores de baja calidad (clickbait, rumores)
    Retorna: (puntos, razón)
    """
    texto = f"{titulo} {descripcion}".lower()
    
    indicadores_encontrados = [ind for ind in INDICADORES_BAJA_CALIDAD if ind.lower() in texto]
    
    if len(indicadores_encontrados) >= 2:
        return (-30, "Múltiples indicadores de baja calidad")
    elif len(indicadores_encontrados) >= 1:
        return (-15, "Posible clickbait o rumor")
    else:
        return (10, "Contenido aparentemente serio")


def evaluar_especificidad(titulo: str, descripcion: str) -> tuple[int, str]:
    """
    Evalúa si menciona víctimas específicas, fechas, números concretos
    Retorna: (puntos, razón)
    """
    texto = f"{titulo} {descripcion}"
    
    puntos = 0
    razones = []
    
    # Buscar nombres de empresas (mayúsculas seguidas)
    if re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', texto):
        puntos += 10
        razones.append("menciona empresa específica")
    
    # Buscar fechas
    if re.search(r'\b(202[0-9]|20[1-2][0-9])\b', texto):
        puntos += 5
        razones.append("incluye fecha")
    
    # Buscar números (millones, miles, cantidades)
    if re.search(r'\b\d+[\.,]?\d*\s?(million|thousand|GB|TB|users|records|files)\b', texto, re.IGNORECASE):
        puntos += 10
        razones.append("incluye cifras concretas")
    
    if razones:
        return (puntos, ", ".join(razones))
    else:
        return (0, "Información genérica")


def calcular_confianza(url: str, titulo: str, descripcion: str = "") -> dict:
    """
    Calcula el nivel de confianza total basado en múltiples factores
    
    Retorna:
        dict con 'nivel' (alta/media/baja), 'puntos' (0-100), 'factores' (lista de evaluaciones)
    """
    factores = []
    puntos_total = 0
    
    # Factor 1: Dominio (peso alto)
    pts_dominio, razon_dominio = evaluar_dominio(url)
    puntos_total += pts_dominio
    factores.append({"factor": "Dominio", "puntos": pts_dominio, "razon": razon_dominio})
    
    # Factor 2: Contenido técnico
    pts_tecnico, razon_tecnico = evaluar_contenido_tecnico(titulo, descripcion)
    puntos_total += pts_tecnico
    factores.append({"factor": "Contenido Técnico", "puntos": pts_tecnico, "razon": razon_tecnico})
    
    # Factor 3: Fuente oficial
    pts_oficial, razon_oficial = evaluar_fuente_oficial(titulo, descripcion)
    puntos_total += pts_oficial
    factores.append({"factor": "Fuente Oficial", "puntos": pts_oficial, "razon": razon_oficial})
    
    # Factor 4: Calidad del contenido
    pts_calidad, razon_calidad = evaluar_calidad_contenido(titulo, descripcion)
    puntos_total += pts_calidad
    factores.append({"factor": "Calidad", "puntos": pts_calidad, "razon": razon_calidad})
    
    # Factor 5: Especificidad
    pts_especif, razon_especif = evaluar_especificidad(titulo, descripcion)
    puntos_total += pts_especif
    factores.append({"factor": "Especificidad", "puntos": pts_especif, "razon": razon_especif})
    
    # Normalizar a escala 0-100
    puntos_normalizados = max(0, min(100, puntos_total))
    
    # Determinar nivel
    if puntos_normalizados >= 60:
        nivel = "alta"
    elif puntos_normalizados >= 30:
        nivel = "media"
    else:
        nivel = "baja"
    
    return {
        "nivel": nivel,
        "puntos": puntos_normalizados,
        "factores": factores
    }


# Ejemplo de uso
if __name__ == "__main__":
    # Test 1: Fuente confiable con contenido técnico
    resultado = calcular_confianza(
        url="https://www.bleepingcomputer.com/news/security/lockbit-ransomware-attack",
        titulo="LockBit ransomware gang attacks major hospital with CVE-2024-1234",
        descripcion="Forensic analysis reveals the threat actor used C2 servers and encrypted 500GB of patient data"
    )
    print(f"Test 1: {resultado['nivel']} ({resultado['puntos']} puntos)")
    for f in resultado['factores']:
        print(f"  - {f['factor']}: {f['puntos']} pts - {f['razon']}")
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Fuente desconocida sin detalles
    resultado = calcular_confianza(
        url="https://random-blog.xyz/post/123",
        titulo="Shocking ransomware attack you won't believe!",
        descripcion="Unconfirmed reports suggest a major breach"
    )
    print(f"Test 2: {resultado['nivel']} ({resultado['puntos']} puntos)")
    for f in resultado['factores']:
        print(f"  - {f['factor']}: {f['puntos']} pts - {f['razon']}")
