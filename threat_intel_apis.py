"""
Sistema de verificación de amenazas usando VirusTotal y AbuseIPDB
Para mejorar el scoring de confianza de eventos
"""

import os
import requests
import time
import re
from urllib.parse import urlparse
from typing import Dict, Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# API Keys desde variables de entorno
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY")

# Validar que las keys estén configuradas
if not VIRUSTOTAL_API_KEY:
    raise ValueError("⚠️ VIRUSTOTAL_API_KEY no encontrada. Configura el archivo .env")
if not ABUSEIPDB_API_KEY:
    raise ValueError("⚠️ ABUSEIPDB_API_KEY no encontrada. Configura el archivo .env")

# Rate limits (requests por minuto)
VT_RATE_LIMIT = 4  # Free tier: 4 requests/min
ABUSEIPDB_RATE_LIMIT = 1  # Free tier: 1000/day, ~1/min seguro

# Cache para evitar re-análisis
_vt_cache = {}
_abuseipdb_cache = {}


def extraer_ips_del_texto(texto: str) -> list:
    """
    Extrae direcciones IP del texto de la noticia.
    """
    # Patrón para IPv4
    ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    ips = re.findall(ip_pattern, texto)
    
    # Filtrar IPs privadas
    ips_validas = []
    for ip in ips:
        partes = ip.split('.')
        # Excluir 192.168.x.x, 10.x.x.x, 127.x.x.x
        if not (partes[0] in ['192', '10', '127', '172']):
            ips_validas.append(ip)
    
    return list(set(ips_validas))  # Eliminar duplicados


def verificar_url_virustotal(url: str) -> Optional[Dict]:
    """
    Verifica una URL en VirusTotal.
    Retorna: {
        'malicious': int,    # Número de motores que detectaron malware
        'suspicious': int,   # Número de motores sospechosos
        'clean': int,        # Número de motores que dicen que es limpia
        'score': float       # Score de 0-100 (100 = muy malo)
    }
    """
    if url in _vt_cache:
        return _vt_cache[url]
    
    try:
        # VirusTotal API v3
        headers = {
            "x-apikey": VIRUSTOTAL_API_KEY
        }
        
        # Analizar URL
        vt_url = "https://www.virustotal.com/api/v3/urls"
        data = {"url": url}
        
        response = requests.post(vt_url, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            analysis_id = response.json()["data"]["id"]
            
            # Esperar un poco para que se complete el análisis
            time.sleep(2)
            
            # Obtener resultados
            result_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
            result = requests.get(result_url, headers=headers, timeout=10)
            
            if result.status_code == 200:
                stats = result.json()["data"]["attributes"]["stats"]
                
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                clean = stats.get("harmless", 0)
                total = malicious + suspicious + clean + stats.get("undetected", 0)
                
                # Calcular score: más detecciones = peor
                score = 0
                if total > 0:
                    score = ((malicious * 2) + suspicious) / total * 100
                
                resultado = {
                    'malicious': malicious,
                    'suspicious': suspicious,
                    'clean': clean,
                    'score': round(score, 2)
                }
                
                _vt_cache[url] = resultado
                return resultado
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error en VirusTotal: {e}")
        return None


def verificar_ip_abuseipdb(ip: str) -> Optional[Dict]:
    """
    Verifica una IP en AbuseIPDB.
    Retorna: {
        'abuse_score': int,      # Score de 0-100 (100 = muy maliciosa)
        'total_reports': int,    # Número de reportes
        'is_whitelisted': bool   # Si está en whitelist
    }
    """
    if ip in _abuseipdb_cache:
        return _abuseipdb_cache[ip]
    
    try:
        headers = {
            "Key": ABUSEIPDB_API_KEY,
            "Accept": "application/json"
        }
        
        params = {
            "ipAddress": ip,
            "maxAgeInDays": 90  # Reportes de los últimos 90 días
        }
        
        response = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()["data"]
            
            resultado = {
                'abuse_score': data.get("abuseConfidenceScore", 0),
                'total_reports': data.get("totalReports", 0),
                'is_whitelisted': data.get("isWhitelisted", False)
            }
            
            _abuseipdb_cache[ip] = resultado
            return resultado
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error en AbuseIPDB: {e}")
        return None


def analizar_evento_con_threat_intel(url: str, titulo: str, descripcion: str = "") -> Dict:
    """
    Análisis completo de un evento usando VirusTotal y AbuseIPDB.
    
    Retorna: {
        'vt_analysis': {...},
        'ip_analysis': [{...}, {...}],
        'threat_score': float,  # Penalización de 0-50 puntos
        'recomendacion': str
    }
    """
    resultado = {
        'vt_analysis': None,
        'ip_analysis': [],
        'threat_score': 0,  # Penalización
        'recomendacion': 'Sin análisis'
    }
    
    # 1. Analizar URL en VirusTotal
    print(f"   🔍 Analizando URL en VirusTotal...")
    vt_result = verificar_url_virustotal(url)
    
    if vt_result:
        resultado['vt_analysis'] = vt_result
        
        # Penalización según detecciones
        if vt_result['malicious'] > 0:
            resultado['threat_score'] += min(vt_result['malicious'] * 10, 50)  # Max 50 pts
            resultado['recomendacion'] = f"⚠️ URL MALICIOSA ({vt_result['malicious']} detecciones)"
        elif vt_result['suspicious'] > 2:
            resultado['threat_score'] += 20
            resultado['recomendacion'] = "⚠️ URL sospechosa"
        else:
            resultado['recomendacion'] = "✅ URL parece limpia"
    
    time.sleep(5)  # Rate limit de VT (reducido para mejorar velocidad)
    
    # 2. Extraer y analizar IPs del contenido
    texto_completo = f"{titulo} {descripcion}"
    ips = extraer_ips_del_texto(texto_completo)
    
    if ips:
        print(f"   🔍 IPs encontradas: {', '.join(ips[:3])}...")
        
        for ip in ips[:3]:  # Máximo 3 IPs para no saturar
            print(f"      Verificando IP {ip} en AbuseIPDB...")
            ip_result = verificar_ip_abuseipdb(ip)
            
            if ip_result:
                resultado['ip_analysis'].append({
                    'ip': ip,
                    'data': ip_result
                })
                
                # Penalización según abuse score
                if ip_result['abuse_score'] > 75:
                    resultado['threat_score'] += 30
                elif ip_result['abuse_score'] > 50:
                    resultado['threat_score'] += 15
            
            time.sleep(1)  # Rate limit prudente
    
    return resultado


def ajustar_confianza_con_threat_intel(
    confianza_base: str, 
    threat_analysis: Dict
) -> str:
    """
    Ajusta el nivel de confianza basado en el análisis de threat intelligence.
    
    Si se detectan amenazas significativas, baja la confianza.
    """
    threat_score = threat_analysis.get('threat_score', 0)
    
    # Si hay amenazas graves, bajar automáticamente
    if threat_score > 40:
        return "baja"  # URL/IPs muy sospechosas
    elif threat_score > 20 and confianza_base == "alta":
        return "media"  # Bajar de alta a media
    elif threat_score > 10 and confianza_base == "media":
        return "baja"  # Bajar de media a baja
    
    return confianza_base


# TEST
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TEST - Threat Intelligence APIs")
    print("=" * 60)
    
    # Test 1: URL limpia
    print("\n📝 Test 1: URL conocida (bleepingcomputer)")
    url_limpia = "https://www.bleepingcomputer.com"
    vt = verificar_url_virustotal(url_limpia)
    print(f"   Resultado: {vt}")
    
    # Test 2: IP conocida maliciosa (ejemplo)
    print("\n📝 Test 2: IP de ejemplo")
    ip_test = "8.8.8.8"  # Google DNS (debería estar limpia)
    abuse = verificar_ip_abuseipdb(ip_test)
    print(f"   Resultado: {abuse}")
    
    print("\n✅ Tests completados")
    print("⚠️  NOTA: VirusTotal tiene rate limit de 4 req/min")
    print("⚠️  NOTA: AbuseIPDB tiene límite de 1000 req/día")
