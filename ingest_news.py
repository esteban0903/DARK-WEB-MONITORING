import csv
import os
import time
from urllib.parse import urlparse, quote_plus
from datetime import datetime

import feedparser
import requests
from dateutil import parser as dateparser

# Config
CSV_PATH = os.path.join("data", "eventos.csv")
QUERIES = [
    "LockBit",
    "Qilin",
    "BlackCat",
    "ransomware",
    "data leak",
]

REPUTABLE_DOMAINS = {
    "reuters.com": "alta",
    "bbc.co.uk": "alta",
    "nytimes.com": "alta",
    "theguardian.com": "alta",
    "elpais.com": "alta",
    "wired.com": "alta",
}

TERMINOS_ACTORES = ["lockbit", "qilin", "blackcat"]

HEADER = ["fecha", "actor", "fuente", "tipo", "indicador", "url", "confianza"]


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
    t = (text or "").lower()
    for a in TERMINOS_ACTORES:
        if a in t:
            return a.capitalize()
    return "Desconocido"


def detect_tipo(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in ["leak", "dump", "exfiltr"]):
        return "leak"
    return "mención"


def detect_confianza_from_domain(domain: str) -> str:
    if not domain:
        return "media"
    for d, conf in REPUTABLE_DOMAINS.items():
        if d in domain:
            return conf
    # heurística por subdominio
    if "blog" in domain or "medium.com" in domain:
        return "media"
    return "baja"


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
        writer = csv.DictWriter(fh, fieldnames=HEADER)
        if not exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)


def run():
    existing = load_existing_urls(CSV_PATH)
    new_rows = []

    for q in QUERIES:
        rss = build_google_news_rss(q)
        print(f"Consultando: {rss}")
        d = feedparser.parse(rss)
        for e in d.entries:
            link = (e.get("link") or "").strip()
            if not link or link in existing:
                continue
            title = e.get("title", "").strip()
            summary = e.get("summary", "") or e.get("description", "") or ""
            text = f"{title} {summary}"
            fecha = normalize_date(e)
            actor = detect_actor(text)
            tipo = detect_tipo(text)
            dominio = urlparse(link).netloc.lower()
            confianza = detect_confianza_from_domain(dominio)

            # Verificar accesibilidad de la URL; si no accesible, marcar confianza baja
            ok = url_is_accessible(link)
            if not ok:
                confianza = "baja"

            indicador = ", ".join([t for t in [a for a in TERMINOS_ACTORES if a in text.lower()]]) or title

            row = {
                "fecha": fecha,
                "actor": actor,
                "fuente": "noticia pública",
                "tipo": tipo,
                "indicador": indicador,
                "url": link,
                "confianza": confianza,
            }
            new_rows.append(row)
            existing.add(link)
            # evitar sobrecarga en queries
            time.sleep(0.1)

    if new_rows:
        append_rows(CSV_PATH, new_rows)
        print(f"Agregados {len(new_rows)} eventos nuevos.")
    else:
        print("No se agregaron eventos nuevos.")


if __name__ == "__main__":
    run()
