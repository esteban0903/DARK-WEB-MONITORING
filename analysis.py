import pandas as pd

TERMINOS = ["lockbit", "qilin", "blackcat", "ransomware"]

def cargar_eventos(path="data/eventos.csv"):
    df = pd.read_csv(path, parse_dates=["fecha"])
    return df

def resumen(df: pd.DataFrame):
    # Conteo simple de menciones a términos en la columna "indicador"
    indic = df["indicador"].fillna("").str.lower()
    menciones = indic.str.contains("|".join(TERMINOS)).sum()
    return {
        "total_eventos": int(len(df)),
        "actores_unicos": int(df["actor"].nunique()),
        "menciones_ransomware": int(menciones)
    }


def top_actores(df: pd.DataFrame, n: int = 10):
    """Devuelve un DataFrame con los actores más frecuentes."""
    return df["actor"].fillna("Desconocido").value_counts().nlargest(n).reset_index().rename(columns={"index": "actor", "actor": "conteo"})


def distrib_confianza(df: pd.DataFrame):
    """Distribución de niveles de confianza."""
    return df["confianza"].fillna("sin etiqueta").value_counts().reset_index().rename(columns={"index": "confianza", "confianza": "conteo"})


def indicadores_top(df: pd.DataFrame, n: int = 15):
    """Extrae términos de la columna 'indicador' asumiendo separadores por comas u espacios y devuelve los top N."""
    s = df["indicador"].fillna("").astype(str).str.lower()
    # Separar por comas y también por espacios si no hay comas
    tokens = s.str.split(",")
    # aplanar
    exploded = tokens.explode().astype(str).str.strip()
    # eliminar cadenas vacías
    exploded = exploded[exploded.str.len() > 0]
    top = exploded.value_counts().nlargest(n).reset_index()
    top.columns = ["indicador", "conteo"]
    return top


def eventos_por_mes(df: pd.DataFrame):
    """Agrupa eventos por mes (YYYY-MM) y devuelve DataFrame ordenado por fecha."""
    if df.empty:
        return df
    s = df.copy()
    s["mes"] = s["fecha"].dt.to_period("M").dt.to_timestamp()
    out = s.groupby("mes").size().reset_index(name="eventos").sort_values("mes")
    return out
