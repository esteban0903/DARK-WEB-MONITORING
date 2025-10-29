import streamlit as st
import pandas as pd
from analysis import cargar_eventos, resumen, top_actores, distrib_confianza, indicadores_top, eventos_por_mes
from datetime import datetime

st.set_page_config(page_title="Dark Web / OSINT — Ransomware Monitor", layout="wide")

# --- Header estilizado
st.markdown(
    """
    <div style='display:flex;align-items:center;gap:12px'>
      <div style='font-size:30px;font-weight:700'>🛡️ Dark Web / OSINT — Ransomware Monitor</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("---")

# Cargar datos
try:
    df = cargar_eventos()
except Exception as e:
    st.error(f"Error cargando datos: {e}")
    st.stop()

# Sidebar: filtros avanzados
st.sidebar.header("Filtros")
# Rango de fechas
min_date = df["fecha"].min().date() if not df.empty else datetime.today().date()
max_date = df["fecha"].max().date() if not df.empty else datetime.today().date()
date_range = st.sidebar.date_input("Rango de fechas", value=(min_date, max_date))

actor = st.sidebar.multiselect("Actor", options=sorted(df["actor"].dropna().unique()), help="Filtra por grupo/actor")
conf = st.sidebar.multiselect("Confianza", options=sorted(df["confianza"].dropna().unique()))
tipo = st.sidebar.multiselect("Tipo", options=sorted(df["tipo"].dropna().unique()))
search = st.sidebar.text_input("Buscar en indicadores / URL", placeholder="ej. lockbit, dump, smb")
show_links = st.sidebar.checkbox("Mostrar fuentes (en tabla expandida)", value=True)

# Aplicar filtros
df_f = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    df_f = df_f[(df_f["fecha"].dt.date >= start) & (df_f["fecha"].dt.date <= end)]
if actor:
    df_f = df_f[df_f["actor"].isin(actor)]
if conf:
    df_f = df_f[df_f["confianza"].isin(conf)]
if tipo:
    df_f = df_f[df_f["tipo"].isin(tipo)]
if search:
    s = search.lower()
    mask = df_f["indicador"].fillna("").str.lower().str.contains(s) | df_f["url"].fillna("").str.lower().str.contains(s)
    df_f = df_f[mask]

# Top-level métricas
met = resumen(df_f)
col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1])
col1.metric("Total eventos", met["total_eventos"], help="Eventos dentro de la selección actual")
col2.metric("Actores únicos", met["actores_unicos"])
col3.metric("Menciones (términos)", met["menciones_ransomware"])
col4.metric("Rango fechas", f"{df_f['fecha'].min().date() if not df_f.empty else '—'} → {df_f['fecha'].max().date() if not df_f.empty else '—'}")

st.write("---")

# Row: charts
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("Timeline")
    timeline = eventos_por_mes(df_f)
    if not timeline.empty:
        st.line_chart(timeline.set_index("mes")["eventos"])
    else:
        st.info("Sin datos para la selección actual.")

    st.markdown("---")
    st.subheader("Top indicadores")
    top_ind = indicadores_top(df_f)
    if not top_ind.empty:
        st.bar_chart(top_ind.set_index("indicador")["conteo"])
    else:
        st.info("No hay indicadores para mostrar.")

with c2:
    st.subheader("Distribución de actores")
    ta = top_actores(df_f)
    if not ta.empty:
        st.table(ta.rename(columns={"conteo": "# eventos"}).head(10))
    else:
        st.info("Sin actores en la selección.")

    st.subheader("Confianza")
    dc = distrib_confianza(df_f)
    if not dc.empty:
        # Manejar nombres de columnas inesperados (robustez)
        if "confianza" in dc.columns and "conteo" in dc.columns:
            st.bar_chart(dc.set_index("confianza")["conteo"])
        elif dc.shape[1] >= 2:
            # Usar la primera columna como etiqueta y la segunda como conteo
            label_col, count_col = dc.columns[0], dc.columns[1]
            st.bar_chart(dc.set_index(label_col)[count_col])
        else:
            st.info("Sin datos de confianza.")
    else:
        st.info("Sin datos de confianza.")

st.write("---")

# Tabla de detalle (con expander para enlaces)
st.subheader("Detalle de eventos")
st.dataframe(df_f.sort_values("fecha", ascending=False).reset_index(drop=True), use_container_width=True)

if show_links:
    with st.expander("Fuentes / URLs (click para abrir)"):
        if df_f.empty:
            st.write("Sin resultados")
        else:
            for i, row in df_f.sort_values("fecha", ascending=False).iterrows():
                url = row.get("url", "")
                fecha = row.get("fecha")
                actor_row = row.get("actor", "-")
                fuente = row.get("fuente", "-")
                tipo_row = row.get("tipo", "-")
                confianza = row.get("confianza", "-")
                titulo = f"**{fecha.date() if pd.notna(fecha) else ''} — {actor_row}**\nFuente: {fuente} - Tipo: {tipo_row} - Confianza: {confianza}"
                st.markdown(titulo)
                if pd.notna(url) and str(url).strip() != "":
                    st.markdown(f"- Link: [fuente]({url})")
                if str(row.get("indicador", "")).strip():
                    st.markdown(f"- Indicadores: `{row.get('indicador')}`")
                st.write("---")

# Descarga de CSV filtrado
csv = df_f.to_csv(index=False).encode("utf-8")
st.download_button("Descargar CSV filtrado", data=csv, file_name="eventos_filtrados.csv", mime="text/csv")


