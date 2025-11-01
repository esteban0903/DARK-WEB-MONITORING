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
        
        prompt = f"""Eres un analista experto en ciberseguridad especializado en ransomware y ataques APT.

Analiza el siguiente contenido y extrae SOLO la información que esté EXPLÍCITAMENTE mencionada. Si un dato NO aparece en el texto, escribe "No especificado".

URL: {url}

CONTENIDO:
{contenido}

---

Proporciona el análisis en este formato EXACTO:

## 📰 INFORMACIÓN DE LA FUENTE
**Autor/Medio:** [nombre del medio]
**Fecha:** [fecha de publicación]

## 🎭 ACTOR DE AMENAZA
**Nombre:** [grupo ransomware identificado: LockBit, BlackCat, RansomHub, etc.]
**Nivel de sofisticación:** [Bajo/Medio/Alto/Muy Alto]

## 🎯 VÍCTIMA
**Organización:** [nombre de la empresa/entidad afectada]
**Sector:** [industria: salud, finanzas, tecnología, gobierno, etc.]
**País:** [ubicación]
**Tamaño:** [Pequeña/Mediana/Grande empresa]

## 🔴 CRITICIDAD
**Nivel:** [🔴 CRÍTICO / 🟠 ALTO / 🟡 MEDIO / 🟢 BAJO]
**Justificación:** [1-2 líneas explicando por qué]

**Impacto:**
- Datos comprometidos: [tipo y cantidad si se menciona]
- Sistemas afectados: [descripción breve]
- Rescate demandado: [monto si se conoce]

## 🛠️ MODUS OPERANDI
**Vector inicial:** [phishing/vulnerabilidad/RDP/VPN/otro]

**Técnicas MITRE ATT&CK detectadas:**
- Initial Access: [técnica]
- Execution: [técnica]
- Persistence: [técnica]
- Lateral Movement: [técnica]
- Exfiltration: [técnica]
- Impact: [técnica]

**Descripción del ataque:** [2-3 líneas describiendo la secuencia del ataque]

## 🔍 INDICADORES DE COMPROMISO (IoCs)
**IPs sospechosas:** [lista o "No especificado"]
**Dominios maliciosos:** [lista o "No especificado"]
**Hashes de malware:** [MD5/SHA-256 o "No especificado"]
**Archivos maliciosos:** [nombres o "No especificado"]
**Otros IoCs:** [puertos/procesos/registry keys o "No especificado"]

## 🛡️ MITIGACIÓN
**Acciones inmediatas:**
1. [acción prioritaria]
2. [acción recomendada]
3. [acción preventiva]

**Parches necesarios:** [CVE específico o "No especificado"]

**Controles recomendados:**
- Detección: [reglas SIEM/IDS]
- Prevención: [configuraciones firewall/segmentación]
- Respuesta: [procedimiento de IR]

## 📊 RESUMEN EJECUTIVO
[2-3 líneas: qué pasó, quién fue afectado, gravedad, acción requerida]

## ⚠️ CONFIABILIDAD
**Nivel:** [Alta/Media/Baja]
**Razón:** [justificación breve]

IMPORTANTE: Sé CONCISO y PRECISO. Extrae SOLO información presente en el texto. No inventes datos."""
        
        response = model.generate_content(prompt)

        # Extraer texto de la respuesta de forma defensiva: la SDK puede
        # devolver diferentes estructuras (text, candidates, message, etc.).
        analisis_text = None
        try:
            # Intento directo (accesor rápido)
            analisis_text = getattr(response, "text", None)

            # Revisar candidatos si no hay .text
            if not analisis_text:
                candidates = getattr(response, "candidates", None)
                if candidates:
                    cand = candidates[0]
                    analisis_text = getattr(cand, "text", None) or getattr(cand, "content", None) or getattr(cand, "output", None) or None

            # Revisar message / content
            if not analisis_text and hasattr(response, "message"):
                msg = getattr(response, "message")
                # Puede ser dict con 'content' como lista de partes
                if isinstance(msg, dict):
                    content = msg.get("content")
                    if isinstance(content, list) and len(content) > 0:
                        for part in content:
                            if isinstance(part, dict):
                                analisis_text = part.get("text") or part.get("content")
                                if analisis_text:
                                    break
                else:
                    # Fallback a str
                    analisis_text = str(msg)

            # Último recurso: serializar el objeto respuesta
            if not analisis_text:
                try:
                    analisis_text = str(response)
                except Exception:
                    analisis_text = "(no se pudo extraer texto de la respuesta)"

        except Exception as e:
            analisis_text = f"Error extrayendo texto de la respuesta de Gemini: {str(e)}"

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
