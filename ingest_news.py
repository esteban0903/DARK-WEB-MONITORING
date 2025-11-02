import csv
import os
import time
from urllib.parse import urlparse, quote_plus
from datetime import datetime
import json

import feedparser
import requests
from dateutil import parser as dateparser

# Importar el nuevo sistema de confianza
from confidence_scorer import calcular_confianza
# Importar threat intelligence APIs
from threat_intel_apis import analizar_evento_con_threat_intel, ajustar_confianza_con_threat_intel

# Config
CSV_PATH = os.path.join("data", "eventos.csv")

# Fuentes RSS directas de ciberseguridad
FUENTES_RSS_DIRECTAS = [
    {
        "url": "https://www.bleepingcomputer.com/feed/",
        "nombre": "BleepingComputer",
        "keywords": ["ransomware", "data breach", "cybercrime", "threat actor", "leak"]
    },
    {
        "url": "https://thehackernews.com/feeds/posts/default",
        "nombre": "The Hacker News",
        "keywords": ["ransomware", "breach", "malware", "cybercrime"]
    },
    {
        "url": "https://www.darkreading.com/rss.xml",
        "nombre": "Dark Reading",
        "keywords": ["ransomware", "attack", "breach", "threat"]
    },
    {
        "url": "https://www.securityweek.com/feed/",
        "nombre": "SecurityWeek",
        "keywords": ["ransomware", "breach", "attack", "cybercrime"]
    },
    {
        "url": "https://www.cyberscoop.com/feed/",
        "nombre": "CyberScoop",
        "keywords": ["ransomware", "breach", "hack"]
    },
    {
        "url": "https://therecord.media/feed",
        "nombre": "The Record",
        "keywords": ["ransomware", "breach", "cybercrime", "attack"]
    },
    {
        "url": "https://krebsonsecurity.com/feed/",
        "nombre": "Krebs on Security",
        "keywords": ["ransomware", "breach", "cybercrime", "fraud"]
    },
    {
        "url": "https://threatpost.com/feed/",
        "nombre": "Threatpost",
        "keywords": ["ransomware", "malware", "breach", "exploit"]
    },
    {
        "url": "https://www.zdnet.com/news/rss.xml",
        "nombre": "ZDNet Security",
        "keywords": ["ransomware", "hack", "breach", "security"]
    },
    {
        "url": "https://www.infosecurity-magazine.com/rss/news/",
        "nombre": "Infosecurity Magazine",
        "keywords": ["ransomware", "breach", "attack", "cybercrime"]
    },
    {
        "url": "https://cybersecuritynews.com/feed/",
        "nombre": "Cybersecurity News",
        "keywords": ["ransomware", "breach", "malware", "attack"]
    },
    {
        "url": "https://www.helpnetsecurity.com/feed/",
        "nombre": "Help Net Security",
        "keywords": ["ransomware", "breach", "threat", "vulnerability"]
    },
]

# Queries para Google News (backup)
QUERIES = [
    "LockBit ransomware attack",
    "BlackCat ALPHV ransomware",
    "Qilin ransomware attack",
    "Akira ransomware breach",
    "Play ransomware victim",
    "Royal ransomware attack",
    "BianLian ransomware",
    "Medusa ransomware leak",
    "RansomHub attack",
    "8Base ransomware",
    "ransomware data breach 2025",
    "ransomware victim leak site",
    "cybercrime data exfiltration",
    "ransomware double extortion",
    "hospital ransomware attack",
]

REPUTABLE_DOMAINS = {
    "reuters.com": "alta",
    "bbc.co.uk": "alta",
    "nytimes.com": "alta",
    "theguardian.com": "alta",
    "elpais.com": "alta",
    "wired.com": "alta",
}

TERMINOS_ACTORES = [
    # Grupos muy activos 2024-2025
    "lockbit", "blackcat", "alphv", "akira", "play", "royal", "ransomhub", 
    "medusa", "8base", "qilin", "bianlian", "black basta", "blackbasta",
    "clop", "cl0p", "rhysida", "noberus", "cactus", "trigona",
    
    # Grupos establecidos
    "conti", "revil", "darkside", "hive", "ragnar locker", "ragnarlocker",
    "cuba", "vice society", "karakurt", "lorenz", "snatch",
    
    # Grupos emergentes
    "hunters international", "rancoz", "meow", "monti", "stormous",
    "daixin", "royal", "malaslocker", "mars stealer", "avoslocker",
    
    # Variantes y alias
    "lockbit 3.0", "lockbit black", "blackcat 2.0", "alphv-ng"
]

# Palabras clave que indican que es un ataque real o filtración
PALABRAS_CLAVE_ATAQUE = [
    "attack", "breach", "victim", "infected", "encrypted", "ransomware",
    "leaked", "stolen", "compromised", "hacked", "infiltrated", "exfiltrated",
    "data dump", "dark web", "threat actor", "malware", "exploit", "cybercrime",
    "attacked", "breached", "hacker", "gang", "group", "campaign", "incident",
    "vulnerability", "zero-day", "CVE", "security", "cyber",
    "atacó", "víctima", "filtración", "comprometido", "hackeado", "robo de datos",
    "ataque", "ciberataque", "cibercriminal"
]

HEADER = ["fecha", "actor", "fuente", "tipo", "indicador", "url", "confianza", "threat_intel"]


def resolver_url_real(url: str, timeout: int = 10) -> str:
    """
    Resuelve redirecciones de Google News y otros acortadores para obtener el URL real.
    """
    try:
        # Si es un URL de Google News, seguir la redirección
        if "news.google.com" in url:
            response = requests.head(url, allow_redirects=True, timeout=timeout)
            return response.url
        # Para otros URLs, también resolver por si acaso
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        return response.url
    except Exception as e:
        print(f"⚠️ No se pudo resolver redirección de {url}: {e}")
        return url  # Devolver el original si falla


def es_noticia_relevante(texto: str) -> bool:
    """
    Verifica si la noticia es realmente sobre un ataque o filtración de ransomware.
    Requiere al menos 2 palabras clave para filtrar noticias genéricas.
    """
    texto_lower = texto.lower()
    # Debe contener al menos 2 palabras clave de ataque
    coincidencias = sum(1 for palabra in PALABRAS_CLAVE_ATAQUE if palabra in texto_lower)
    return coincidencias >= 2


def build_google_news_rss(query: str) -> str:
    # Google News search RSS
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=es&gl=ES&ceid=ES:es"


def normalize_date(entry) -> str:
    # feedparser entries may have published or updated
    for attr in ("published", "updated", "pubDate"):
        val = entry.get(attr)
        if val:
            try:
                dt = dateparser.parse(val)
                return dt.date().isoformat()
            except Exception:
                pass
    # fallback: today
    return datetime.utcnow().date().isoformat()


def detect_actor(text: str) -> str:
    """
    Detecta el grupo de ransomware mencionado en el texto.
    Busca coincidencias parciales y maneja alias.
    """
    t = (text or "").lower()
    
    # Buscar coincidencias con los grupos conocidos
    for actor in TERMINOS_ACTORES:
        if actor in t:
            # Capitalizar correctamente nombres conocidos
            if "lockbit" in actor:
                return "LockBit"
            elif "blackcat" in actor or "alphv" in actor:
                return "BlackCat/ALPHV"
            elif "akira" in actor:
                return "Akira"
            elif "play" in actor and ("play ransomware" in t or "play gang" in t):
                return "Play"
            elif "royal" in actor:
                return "Royal"
            elif "ransomhub" in actor:
                return "RansomHub"
            elif "medusa" in actor:
                return "Medusa"
            elif "8base" in actor:
                return "8Base"
            elif "qilin" in actor:
                return "Qilin"
            elif "bianlian" in actor:
                return "BianLian"
            elif "black basta" in actor or "blackbasta" in actor:
                return "Black Basta"
            elif "clop" in actor or "cl0p" in actor:
                return "Clop"
            elif "rhysida" in actor:
                return "Rhysida"
            elif "cactus" in actor:
                return "Cactus"
            elif "conti" in actor:
                return "Conti"
            elif "hive" in actor:
                return "Hive"
            elif "ragnar" in actor:
                return "Ragnar Locker"
            else:
                return actor.title()
    
    return "Desconocido"


def detect_tipo(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["leak", "dump", "exfiltr"]):
        return "leak"
    return "mención"


def detect_confianza_from_domain(domain: str) -> str:
    """
    DEPRECADO: Ahora usamos confidence_scorer.calcular_confianza()
    """
    if not domain:
        return "media"
    for d, conf in REPUTABLE_DOMAINS.items():
        if d in domain:
            return conf
    # heurística por subdominio
    if "blog" in domain or "medium.com" in domain:
        return "media"
    return "baja"


def calcular_confianza_evento(url: str, titulo: str, descripcion: str = "") -> str:
    """
    Calcula la confianza usando el sistema multi-factor.
    """
    resultado = calcular_confianza(url, titulo, descripcion)
    return resultado['nivel']


def url_is_accessible(url: str, timeout: int = 6) -> bool:
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        if r.status_code >= 200 and r.status_code < 400:
            return True
        # algunas webs no permiten HEAD
        r = requests.get(url, timeout=timeout)
        return 200 <= r.status_code < 400
    except Exception:
        return False


def load_existing_urls(csv_path: str):
    urls = set()
    if not os.path.exists(csv_path):
        return urls
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            u = (r.get("url") or "").strip()
            if u:
                urls.add(u)
    return urls


def append_rows(csv_path: str, rows):
    exists = os.path.exists(csv_path)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=HEADER, quoting=csv.QUOTE_ALL)
        if not exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)


def run():
    existing = load_existing_urls(CSV_PATH)
    new_rows = []
    eventos_analizados_con_apis = 0
    
    # Imprimir total de fuentes para la barra de progreso
    total_fuentes = len(FUENTES_RSS_DIRECTAS) + len(QUERIES)
    print(f"PROGRESS:0/{total_fuentes}", flush=True)

    # 1. PROCESAR FUENTES RSS DIRECTAS (mejor calidad)
    print("=" * 60, flush=True)
    print("📰 PROCESANDO FUENTES RSS DIRECTAS", flush=True)
    print("=" * 60, flush=True)
    
    fuente_actual = 0
    for fuente in FUENTES_RSS_DIRECTAS:
        fuente_actual += 1
        print(f"PROGRESS:{fuente_actual}/{total_fuentes}:Procesando {fuente['nombre']}...", flush=True)
        rss_url = fuente["url"]
        nombre = fuente["nombre"]
        keywords = fuente["keywords"]
        
        print(f"\n🔍 Consultando: {nombre}")
        print(f"   URL: {rss_url}")
        
        try:
            d = feedparser.parse(rss_url)
            count = 0
            api_analysis_count = 0  # Contador de análisis con APIs por fuente
            max_api_analysis_per_source = 3  # Límite de análisis por fuente
            
            for e in d.entries:
                link = (e.get("link") or "").strip()
                if not link or link in existing:
                    continue
                
                title = e.get("title", "").strip()
                summary = e.get("summary", "") or e.get("description", "") or ""
                text = f"{title} {summary}".lower()
                
                # Verificar si contiene keywords relevantes
                if not any(kw in text for kw in keywords):
                    continue
                
                # Filtrar: solo noticias relevantes sobre ataques reales
                if not es_noticia_relevante(text):
                    continue
                
                fecha = normalize_date(e)
                actor = detect_actor(text)
                tipo = detect_tipo(text)
                
                # Calcular confianza con el nuevo sistema
                confianza = calcular_confianza_evento(link, title, summary)
                
                # 🔍 ANÁLISIS CON THREAT INTELLIGENCE APIs
                threat_intel_data = None
                
                # Solo analizar con APIs si la confianza es BAJA y no hemos superado el límite
                if confianza == "baja" and api_analysis_count < max_api_analysis_per_source:
                    print(f"   🛡️  Analizando con Threat Intel: {title[:50]}...", flush=True)
                    try:
                        threat_analysis = analizar_evento_con_threat_intel(link, title, summary)
                        
                        # Ajustar confianza según el análisis
                        confianza_original = confianza
                        confianza = ajustar_confianza_con_threat_intel(confianza, threat_analysis)
                        
                        if confianza != confianza_original:
                            print(f"      ⚠️  Confianza ajustada: {confianza_original} → {confianza}", flush=True)
                        
                        # Guardar datos de threat intel como JSON
                        threat_intel_data = json.dumps(threat_analysis, ensure_ascii=False)
                        eventos_analizados_con_apis += 1
                        api_analysis_count += 1
                        print(f"      ✅ Análisis completado ({eventos_analizados_con_apis} analizados en total)", flush=True)
                        
                    except Exception as e:
                        print(f"      ❌ Error en análisis de threat intel: {e}", flush=True)
                        api_analysis_count += 1  # Contar también los errores
                
                indicador = ", ".join([t for t in [a for a in TERMINOS_ACTORES if a in text]]) or title[:100]
                
                row = {
                    "fecha": fecha,
                    "actor": actor,
                    "fuente": f"{nombre}",
                    "tipo": tipo,
                    "indicador": indicador,
                    "url": link,
                    "confianza": confianza,
                    "threat_intel": threat_intel_data or "",
                }
                new_rows.append(row)
                existing.add(link)
                count += 1
                time.sleep(0.1)
            
            print(f"   ✅ {count} nuevas noticias de {nombre}")
            
        except Exception as e:
            print(f"   ❌ Error procesando {nombre}: {e}")
    
    # 2. PROCESAR GOOGLE NEWS (backup, resolviendo redirecciones)
    print("\n" + "=" * 60, flush=True)
    print("🔍 PROCESANDO GOOGLE NEWS (backup)", flush=True)
    print("=" * 60, flush=True)
    
    for q in QUERIES:
        fuente_actual += 1
        print(f"PROGRESS:{fuente_actual}/{total_fuentes}:Google News ({q[:30]}...)", flush=True)
        rss = build_google_news_rss(q)
        print(f"\n🔎 Query: {q}")
        
        try:
            d = feedparser.parse(rss)
            count = 0
            api_analysis_count = 0  # Contador de análisis con APIs por query
            max_api_analysis_per_source = 2  # Límite reducido para Google News
            
            for e in d.entries:
                link_google = (e.get("link") or "").strip()
                if not link_google:
                    continue
                
                # RESOLVER REDIRECCIÓN para obtener URL real
                link = resolver_url_real(link_google)
                
                if link in existing:
                    continue
                
                title = e.get("title", "").strip()
                summary = e.get("summary", "") or e.get("description", "") or ""
                text = f"{title} {summary}"
                
                # Filtrar: solo noticias relevantes sobre ataques reales
                if not es_noticia_relevante(text):
                    continue
                
                fecha = normalize_date(e)
                actor = detect_actor(text)
                tipo = detect_tipo(text)
                
                # Calcular confianza con el nuevo sistema
                confianza = calcular_confianza_evento(link, title, summary)
                
                # Verificar accesibilidad de la URL
                ok = url_is_accessible(link)
                if not ok:
                    confianza = "baja"
                
                # 🔍 ANÁLISIS CON THREAT INTELLIGENCE APIs
                threat_intel_data = None
                
                # Solo analizar con APIs si la confianza es BAJA y no hemos superado el límite
                if confianza == "baja" and api_analysis_count < max_api_analysis_per_source:
                    print(f"   🛡️  Analizando con Threat Intel: {title[:50]}...", flush=True)
                    try:
                        threat_analysis = analizar_evento_con_threat_intel(link, title, summary)
                        
                        # Ajustar confianza según el análisis
                        confianza_original = confianza
                        confianza = ajustar_confianza_con_threat_intel(confianza, threat_analysis)
                        
                        if confianza != confianza_original:
                            print(f"      ⚠️  Confianza ajustada: {confianza_original} → {confianza}", flush=True)
                        
                        # Guardar datos de threat intel como JSON
                        threat_intel_data = json.dumps(threat_analysis, ensure_ascii=False)
                        eventos_analizados_con_apis += 1
                        api_analysis_count += 1
                        print(f"      ✅ Análisis completado ({eventos_analizados_con_apis} analizados en total)", flush=True)
                        
                    except Exception as e:
                        print(f"      ❌ Error en análisis de threat intel: {e}", flush=True)
                        api_analysis_count += 1  # Contar también los errores
                
                indicador = ", ".join([t for t in [a for a in TERMINOS_ACTORES if a in text.lower()]]) or title[:100]
                
                row = {
                    "fecha": fecha,
                    "actor": actor,
                    "fuente": "Google News",
                    "tipo": tipo,
                    "indicador": indicador,
                    "url": link,
                    "confianza": confianza,
                    "threat_intel": threat_intel_data or "",
                }
                new_rows.append(row)
                existing.add(link)
                count += 1
                time.sleep(0.2)  # Más lento para no saturar
            
            print(f"   ✅ {count} nuevas noticias")
            
        except Exception as e:
            print(f"   ❌ Error procesando query: {e}")

    # 3. GUARDAR RESULTADOS
    print(f"PROGRESS:{total_fuentes}/{total_fuentes}:Guardando resultados...", flush=True)
    
    if new_rows:
        append_rows(CSV_PATH, new_rows)
        print("\n" + "=" * 60, flush=True)
        print(f"✅ COMPLETADO: {len(new_rows)} eventos nuevos agregados", flush=True)
        print(f"🛡️  Analizados con Threat Intel APIs: {eventos_analizados_con_apis}", flush=True)
        print("=" * 60, flush=True)
        print("PROGRESS:COMPLETE", flush=True)
    else:
        print("\n" + "=" * 60, flush=True)
        print("ℹ️  No se agregaron eventos nuevos", flush=True)
        print("=" * 60, flush=True)
        print("PROGRESS:COMPLETE", flush=True)


if __name__ == "__main__":
    run()
