import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar la API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY no encontrada. Configura el archivo .env")
genai.configure(api_key=GEMINI_API_KEY)

def extraer_contenido_web(url: str, timeout: int = 5) -> str:
    """
    Extrae el contenido de texto de una URL usando BeautifulSoup.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        # Si obtenemos 403, intentamos con un user agent diferente
        if response.status_code == 403:
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Eliminar scripts y estilos
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Obtener texto
        texto = soup.get_text(separator=' ', strip=True)
        
        # Limitar a 8000 caracteres (reducido para análisis más rápido)
        return texto[:8000]
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            return f"⚠️ Acceso denegado (403 Forbidden) - El sitio web bloqueó el acceso automatizado. Análisis basado solo en título y descripción disponible."
        return f"Error HTTP {e.response.status_code}: {str(e)}"
    except requests.exceptions.Timeout:
        return f"⚠️ Timeout - El sitio web tardó demasiado en responder. Análisis basado solo en URL."
    except Exception as e:
        return f"Error al extraer contenido: {str(e)}"


def analizar_con_gemini(url: str, contenido: str) -> dict:
    """
    Analiza el contenido de una noticia usando Gemini y extrae información estructurada.
    """
    try:
        # Usar Gemini 2.5 Flash con configuración de timeout
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 2048,  # Limitar salida para respuestas más rápidas
            }
        )
        
        prompt = f"""
Eres un analista experto en ciberseguridad especializado en ransomware y ataques de amenazas avanzadas (APT).
Analiza el siguiente contenido de una noticia sobre un incidente de ransomware/ciberseguridad y extrae la siguiente información estructurada de forma PRECISA Y TÉCNICA.

IMPORTANTE: 
- Si algún dato no está disponible en el contenido, indica "No especificado" o "No disponible en la fuente".
- Usa el framework MITRE ATT&CK para identificar técnicas y tácticas cuando sea posible.
- Sé específico y técnico en tu análisis.

URL: {url}

CONTENIDO DE LA NOTICIA:
{contenido}

---

Por favor, proporciona la información en el siguiente formato ESTRUCTURADO:

## 📰 INFORMACIÓN DE LA FUENTE
**Autor/Medio:** [Nombre del autor o medio de comunicación]
**Fecha de publicación:** [Fecha si está disponible]

---

## 🎭 GRUPO/ACTOR DE AMENAZA
**Nombre:** [Nombre del grupo ransomware o actor (ej: LockBit, BlackCat, Qilin)]
**Alias conocidos:** [Otros nombres con los que se conoce al grupo]
**Nivel de sofisticación:** [Bajo/Medio/Alto/Muy Alto]

---

## 🎯 VÍCTIMA(S)
**Organización(es) afectada(s):** [Nombre de la(s) empresa(s) o entidad(es)]
**Sector/Industria:** [Sector económico: salud, finanzas, manufactura, gobierno, etc.]
**País/Región:** [Ubicación geográfica]
**Tamaño estimado:** [Pequeña/Mediana/Grande empresa]

---

## 🔴 NIVEL DE CRITICIDAD
**Clasificación:** [🔴 CRÍTICO / 🟠 ALTO / 🟡 MEDIO / 🟢 BAJO]

**Justificación:** [Explicación breve del nivel de criticidad basado en: impacto, sector afectado, datos comprometidos, número de víctimas]

**Impacto estimado:**
- Datos comprometidos: [Tipo y cantidad de datos]
- Sistemas afectados: [Servidores, endpoints, bases de datos, etc.]
- Tiempo de inactividad: [Si se menciona]
- Demanda de rescate: [Monto si se conoce]

---

## 🛠️ MODUS OPERANDI (MITRE ATT&CK)

**Vector de entrada inicial:**
[Phishing, explotación de vulnerabilidad, RDP expuesto, VPN comprometida, etc.]

**Técnicas MITRE ATT&CK identificadas:**
(Lista las tácticas y técnicas del framework MITRE ATT&CK si están mencionadas o se pueden inferir)

- **[TA0001] Initial Access:** [Técnica específica - ej: T1566 Phishing]
- **[TA0002] Execution:** [Técnica específica]
- **[TA0003] Persistence:** [Técnica específica]
- **[TA0005] Defense Evasion:** [Técnica específica]
- **[TA0006] Credential Access:** [Técnica específica]
- **[TA0008] Lateral Movement:** [Técnica específica]
- **[TA0010] Exfiltration:** [Técnica específica - ej: T1048 Exfiltration Over C2 Channel]
- **[TA0011] Impact:** [Técnica específica - ej: T1486 Data Encrypted for Impact]

**Descripción del ataque:**
[Narrativa secuencial de cómo se desarrolló el ataque, desde el acceso inicial hasta el cifrado/exfiltración]

---

## 🔍 INDICADORES DE COMPROMISO (IoCs)

**Direcciones IP sospechosas:**
- [Lista de IPs con formato: IP - Descripción/País/ASN si está disponible]
- Ejemplo: 192.168.1.100 - C2 Server (Rusia, AS12345)

**Dominios maliciosos:**
- [Lista de dominios]

**URLs maliciosas:**
- [Lista de URLs completas]

**Hashes de archivos (malware):**
- MD5: [hash]
- SHA-1: [hash]
- SHA-256: [hash]

**Nombres de archivos maliciosos:**
- [Lista de nombres de archivos]

**Emails/Cuentas comprometidas:**
- [Direcciones de email usadas en phishing o comprometidas]

**Otros IoCs técnicos:**
- Claves de registro modificadas
- Procesos sospechosos
- Puertos utilizados
- Servicios comprometidos

---

## 🛡️ SOLUCIONES Y MITIGACIÓN

**Acciones inmediatas recomendadas:**
1. [Acción específica con prioridad ALTA]
2. [Acción específica]
3. [Acción específica]

**Parches/Actualizaciones necesarias:**
- [CVE específico si aplica] - [Software/Sistema afectado]
- [Actualización recomendada]

**Controles de seguridad recomendados:**
- **Detección:** [Reglas SIEM, firmas de IDS/IPS]
- **Prevención:** [Configuraciones de firewall, segmentación de red]
- **Respuesta:** [Procedimientos de IR, aislamiento]
- **Recuperación:** [Backups, planes de contingencia]

**Referencias a guías de seguridad:**
- [Enlaces a CISA, NIST, o guías específicas si se mencionan]

---

## 📊 RESUMEN EJECUTIVO
[Resumen conciso en 3-4 líneas para directivos: qué pasó, quién fue afectado, qué tan grave es, y qué hacer]

---

## 🔗 FUENTES ADICIONALES
[Si se mencionan otras fuentes, reportes técnicos, o referencias en el artículo]

---

## ⚠️ CONFIABILIDAD DEL ANÁLISIS
**Nivel de confianza:** [Alta/Media/Baja]
**Razón:** [Por qué tienes ese nivel de confianza en la información extraída]
"""
        
        response = model.generate_content(prompt)
        
        return {
            "success": True,
            "analisis": response.text,
            "url": url
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analisis": "Error al analizar con Gemini",
            "url": url
        }


def analizar_noticia_completa(url: str) -> dict:
    """
    Función principal que extrae el contenido de una URL y lo analiza con Gemini.
    """
    contenido = extraer_contenido_web(url)
    
    # Si hay error de extracción pero queremos analizar igual
    if contenido.startswith("Error") or contenido.startswith("⚠️"):
        # Analizar solo con la URL y mensaje de error
        return analizar_con_gemini(url, f"⚠️ No se pudo acceder al contenido completo del artículo.\n\nMotivo: {contenido}\n\nPor favor, realiza un análisis basado únicamente en la URL y lo que puedas inferir de ella. Indica claramente que el análisis es limitado debido a restricciones de acceso.")
    
    resultado = analizar_con_gemini(url, contenido)
    return resultado
