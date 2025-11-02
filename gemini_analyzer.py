import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configurar la API de Gemini
# Intentar obtener de secrets de Streamlit primero, luego de .env
try:
    import streamlit as st
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
except:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY no encontrada. Configura el archivo .env o Streamlit secrets")
genai.configure(api_key=GEMINI_API_KEY)

def extraer_contenido_web(url: str, timeout: int = 10) -> str:
    """
    Extrae el contenido de texto de una URL usando BeautifulSoup con múltiples intentos.
    """
    # Lista de user agents a probar
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    ]
    
    for i, ua in enumerate(user_agents):
        try:
            headers = {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.google.com/'
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=timeout, 
                allow_redirects=True,
                verify=True
            )
            
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Eliminar scripts, estilos, y elementos no útiles
            for element in soup(["script", "style", "nav", "footer", "header", "aside", "iframe"]):
                element.decompose()
            
            # Intentar extraer el contenido principal
            contenido_principal = None
            
            # Buscar en selectores comunes de artículos
            for selector in ['article', 'main', '.article-content', '.post-content', '.entry-content']:
                contenido = soup.select_one(selector)
                if contenido:
                    contenido_principal = contenido
                    break
            
            # Si no encontramos contenido principal, usar body
            if not contenido_principal:
                contenido_principal = soup.find('body')
            
            if contenido_principal:
                texto = contenido_principal.get_text(separator=' ', strip=True)
            else:
                texto = soup.get_text(separator=' ', strip=True)
            
            # Limpiar texto: remover espacios múltiples
            texto = ' '.join(texto.split())
            
            # Limitar a 12000 caracteres para más contexto
            if len(texto) > 100:  # Si tiene contenido útil
                return texto[:12000]
            else:
                # Contenido muy corto, probar siguiente user agent
                if i < len(user_agents) - 1:
                    continue
                    
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403 and i < len(user_agents) - 1:
                # Intentar con siguiente user agent
                continue
            elif e.response.status_code == 403:
                return "⚠️ ACCESO_BLOQUEADO"
            else:
                return f"⚠️ ERROR_HTTP_{e.response.status_code}"
                
        except requests.exceptions.Timeout:
            if i < len(user_agents) - 1:
                continue
            return "⚠️ TIMEOUT"
            
        except Exception as e:
            if i < len(user_agents) - 1:
                continue
            return f"⚠️ ERROR: {str(e)[:100]}"
    
    return "⚠️ NO_CONTENIDO"


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
        
        prompt = f"""Eres un analista experto en ciberseguridad. Analiza esta noticia de ransomware y EXTRAE TODA LA INFORMACIÓN POSIBLE.

INSTRUCCIONES CRÍTICAS:
1. Si un dato está en el texto, EXTRÁELO
2. Si puedes INFERIR algo razonablemente del contexto, HAZLO (marca como "Inferido:")
3. SOLO si realmente no hay NADA, escribe "No disponible"

URL: {url}

CONTENIDO:
{contenido}

---

COMPLETA ESTE ANÁLISIS:

## 📰 FUENTE
**Autor/Medio:** [Busca el nombre del sitio web en la URL o en el texto. Si dice "BleepingComputer" o "The Hacker News", úsalo]
**Fecha:** [Busca cualquier fecha mencionada: "October 2024", "2 days ago", etc.]

## 🎭 ATACANTE
**Nombre del grupo:** [Busca nombres como: LockBit, BlackCat, ALPHV, Akira, Play, Royal, RansomHub, Medusa, 8Base, Qilin, BianLian, Clop, Conti, etc. Si no hay nombre pero dice "ransomware gang" o "threat actors", escribe "Grupo no identificado"]
**Sofisticación:** [Si menciona táctica avanzada=Alto, si es ataque común=Medio, si no dice=Medio]

## 🎯 VÍCTIMA
**Organización:** [BUSCA NOMBRES DE EMPRESAS EN MAYÚSCULAS o con Ltd/Inc/Corp/GmbH. Pueden estar en el título. Si dice "major hospital" sin nombre="Hospital no identificado"]
**Sector:** [Si es hospital=salud, si es banco=finanzas, si es gobierno=gobierno, si dice "tech company"=tecnología, si dice "manufacturer"=manufactura. INFIERE del contexto]
**País:** [Busca nombres de países, ciudades, o dominios (.uk=Reino Unido, .de=Alemania, etc.)]
**Tamaño:** [Si dice "major"=Grande, "small"=Pequeña, "mid-size"=Mediana, si no especifica=Mediana]

## 🔴 CRITICIDAD
**Nivel:** [Si es hospital/gobierno/infraestructura crítica=🔴 CRÍTICO, si menciona millones de datos=🟠 ALTO, si es empresa pequeña=🟡 MEDIO]
**Justificación:** [Explica por qué según sector y datos comprometidos]

**Impacto:**
- Datos comprometidos: [Busca: "X GB", "Y million records", "patient data", "financial records", etc.]
- Sistemas afectados: [Busca: "servers", "network", "database", "backup", etc.]
- Rescate: [Busca: "$X million", "ransom demand", etc.]

## 🛠️ MODUS OPERANDI
**Vector inicial:** [Si menciona email=phishing, si dice vulnerability/CVE=vulnerabilidad, si dice RDP/remote=RDP, si no especifica="Inferido: Probablemente phishing o vulnerabilidad"]

**Técnicas MITRE:**
- Initial Access: [Si hay phishing=T1566, si vulnerabilidad=T1190, sino="Técnica no especificada"]
- Execution: [Si menciona scripts/malware=especificarlo, sino="No especificado"]
- Lateral Movement: [Si menciona red interna="Movimiento lateral detectado", sino="No especificado"]
- Impact: [SIEMPRE poner "T1486 Data Encrypted for Impact" porque es ransomware]

**Descripción:** [Resume en 2-3 líneas QUÉ PASÓ según el artículo]

## 🔍 IOCs
**IPs:** [Busca números tipo 192.168.x.x o menciones de "IP address"]
**Dominios:** [Busca URLs .com/.net o menciones de C2]
**Hashes:** [Busca códigos MD5/SHA256 largos]
**Archivos:** [Busca menciones de .exe/.dll/.bat]
**Otros:** [Cualquier indicador técnico mencionado]

## 🛡️ MITIGACIÓN
**Acciones inmediatas:**
1. Aislar sistemas afectados y desconectar de la red
2. [Acción específica según el ataque]
3. Contactar equipo de respuesta a incidentes

**Parches:** [Si menciona CVE, especificarlo]

**Controles:**
- Detección: Monitorear tráfico anómalo y cifrado de archivos
- Prevención: [Específico según vector de ataque]
- Respuesta: Activar plan de recuperación y backups

## 📊 RESUMEN
[En 2-3 líneas: "El grupo [ATACANTE] atacó a [VÍCTIMA] mediante [VECTOR] comprometiendo [DATOS/SISTEMAS]. Nivel de gravedad [NIVEL] debido a [RAZÓN]."]

## ⚠️ CONFIABILIDAD
**Nivel:** [Alta si es fuente reconocida + detalles técnicos, Media si falta info, Baja si es rumor]
**Razón:** [Por qué]

REGLAS:
- NO dejes TODO en "No especificado" - BUSCA ACTIVAMENTE en el texto
- USA el título y URL para inferir información si el contenido es limitado
- Si es ransomware, SIEMPRE hay al menos: grupo O víctima O sector
- Sé inteligente: si dice "healthcare provider" = salud, "financial institution" = finanzas"""
        
        response = model.generate_content(prompt)

        # Extraer texto de la respuesta de forma defensiva
        analisis_text = None
        finish_reason = None
        
        try:
            # Revisar finish_reason primero para detectar bloqueos de seguridad
            candidates = getattr(response, "candidates", None)
            if candidates and len(candidates) > 0:
                finish_reason = getattr(candidates[0], "finish_reason", None)
                
                # finish_reason = 2 es SAFETY (contenido bloqueado por seguridad)
                # finish_reason = 3 es RECITATION (contenido bloqueado por derechos de autor)
                if finish_reason in [2, 3]:
                    razon_bloqueo = "restricciones de seguridad" if finish_reason == 2 else "derechos de autor"
                    analisis_text = f"""⚠️ **Análisis bloqueado por Gemini ({razon_bloqueo})**

El contenido de esta noticia activó filtros de seguridad de Gemini y no pudo ser analizado completamente.

**Información básica disponible:**
- **URL:** {url}
- **Título:** {titulo_rss if 'titulo_rss' in locals() else 'No disponible'}

**Posibles razones del bloqueo:**
- El contenido contiene información sensible sobre vulnerabilidades activas
- Descripción detallada de técnicas de ataque
- Contenido relacionado con malware activo

**Recomendación:** Revisa manualmente la noticia en la URL original para obtener detalles completos."""
                    
                    return {
                        "success": True,
                        "analisis": analisis_text,
                        "url": url,
                        "_blocked": True
                    }
            
            # Intento directo (accesor rápido)
            analisis_text = getattr(response, "text", None)

            # Revisar candidatos si no hay .text
            if not analisis_text and candidates:
                cand = candidates[0]
                # Intentar extraer contenido de diferentes atributos
                content = getattr(cand, "content", None)
                if content:
                    # content puede ser un objeto con 'parts'
                    parts = getattr(content, "parts", None)
                    if parts and len(parts) > 0:
                        analisis_text = getattr(parts[0], "text", None)
                
                if not analisis_text:
                    analisis_text = getattr(cand, "text", None) or getattr(cand, "output", None)

            # Revisar message / content alternativo
            if not analisis_text and hasattr(response, "message"):
                msg = getattr(response, "message")
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, list) and len(content) > 0:
                        for part in content:
                            if isinstance(part, dict):
                                analisis_text = part.get("text") or part.get("content")
                                if analisis_text:
                                    break
                else:
                    analisis_text = str(msg)

            # Si aún no hay texto, dar mensaje informativo
            if not analisis_text:
                analisis_text = f"""⚠️ **No se pudo extraer respuesta de Gemini**

La API de Gemini respondió pero no devolvió contenido analizable.

**Finish reason:** {finish_reason if finish_reason else 'Desconocido'}

**Información disponible:**
- **URL:** {url}

**Acción sugerida:** Intenta el análisis nuevamente en unos minutos."""

        except Exception as e:
            error_msg = str(e)
            if "finish_reason is 2" in error_msg or "SAFETY" in error_msg:
                analisis_text = f"""⚠️ **Contenido bloqueado por filtros de seguridad de Gemini**

La noticia contiene información que activó los filtros de seguridad de Gemini.

**URL:** {url}

**Recomendación:** Revisa la noticia manualmente en el navegador."""
            else:
                analisis_text = f"""⚠️ **Error al procesar respuesta de Gemini**

Detalles técnicos: {error_msg[:200]}

**URL:** {url}

Intenta nuevamente o revisa la noticia manualmente."""

        # Limitar tamaño de la respuesta devuelta al front-end
        if isinstance(analisis_text, str) and len(analisis_text) > 20000:
            analisis_text = analisis_text[:20000] + "\n\n...respuesta truncada..."

        return {
            "success": True,
            "analisis": analisis_text,
            "url": url,
            "_raw_response_debug": None  # campo reservado para debugging en logs (no expuesto en UI)
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analisis": "Error al analizar con Gemini",
            "url": url
        }


def analizar_noticia_completa(url: str, titulo_rss: str = "", descripcion_rss: str = "") -> dict:
    """
    Función principal que extrae el contenido de una URL y lo analiza con Gemini.
    Si no puede acceder al contenido, usa el título y descripción del RSS.
    
    Args:
        url: URL de la noticia
        titulo_rss: Título extraído del feed RSS (opcional)
        descripcion_rss: Descripción extraída del feed RSS (opcional)
    """
    contenido = extraer_contenido_web(url)
    
    # Si hay error de extracción, usar título y descripción del RSS
    if contenido.startswith("⚠️"):
        contexto_adicional = ""
        if titulo_rss or descripcion_rss:
            contexto_adicional = f"\n\n📰 INFORMACIÓN DISPONIBLE DEL RSS:\nTítulo: {titulo_rss}\nDescripción: {descripcion_rss}\n"
        
        contenido_fallback = f"""⚠️ No se pudo acceder al contenido completo del artículo web.
Motivo: {contenido}
{contexto_adicional}
INSTRUCCIONES: Analiza la noticia basándote en:
1. La URL (puede indicar el tipo de ataque, víctima, o grupo)
2. El título y descripción del RSS si están disponibles
3. Infiere información técnica razonable basada en el contexto

Sé lo más específico posible con la información disponible. Si algo no se puede determinar, marca como "No especificado"."""
        
        return analizar_con_gemini(url, contenido_fallback)
    
    resultado = analizar_con_gemini(url, contenido)
    return resultado
