import streamlit as st
import pandas as pd
import subprocess
import time
from analysis import cargar_eventos, resumen, top_actores, distrib_confianza, indicadores_top, eventos_por_mes
from gemini_analyzer import analizar_noticia_completa
from datetime import datetime

st.set_page_config(page_title="Dark Web / OSINT — Ransomware Monitor", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "selected_event" not in st.session_state:
    st.session_state.selected_event = None
if "eventos_por_pagina" not in st.session_state:
    st.session_state.eventos_por_pagina = 10
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = 0
if "show_delete_confirmation" not in st.session_state:
    st.session_state.show_delete_confirmation = False

def ir_a_detalle(evento_data):
    st.session_state.selected_event = evento_data
    st.session_state.page = "detalle"
    st.rerun()

def volver_dashboard():
    st.session_state.page = "dashboard"
    st.session_state.selected_event = None
    st.rerun()

try:
    df = cargar_eventos()
except Exception as e:
    st.error(f"Error cargando datos: {str(e)}")
    st.stop()

if st.session_state.page == "detalle" and st.session_state.selected_event is not None:
    evento = st.session_state.selected_event
    
    if st.button("← Volver al Dashboard", type="secondary"):
        volver_dashboard()
    
    st.markdown("---")
    
    # Preparar la fecha para mostrar
    fecha_str = "Sin fecha"
    if pd.notna(evento["fecha"]):
        if hasattr(evento["fecha"], 'date'):
            fecha_str = str(evento["fecha"].date())
        else:
            fecha_str = str(evento["fecha"])
    
    st.markdown(
        f"""
        <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); 
                    padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; margin: 0;">🔍 Análisis Detallado del Evento</h1>
            <p style="color: #dbeafe; margin-top: 0.5rem; font-size: 1.1rem;">
                {fecha_str} | 
                Actor: {evento["actor"]} | 
                Confianza: {evento["confianza"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎭 Actor", evento["actor"])
        st.metric("📊 Tipo", evento["tipo"])
    with col2:
        st.metric("🔒 Confianza", evento["confianza"])
        st.metric("📰 Fuente", evento["fuente"])
    with col3:
        if pd.notna(evento["fecha"]):
            st.metric("📅 Fecha", fecha_str)
        if evento.get("indicador"):
            st.info(f"📌 **Indicadores:**\n\n{evento['indicador']}")
    
    if pd.notna(evento["url"]) and str(evento["url"]).strip():
        st.markdown(f"🔗 **Noticia original:** [{evento['url']}]({evento['url']})")
    
    st.markdown("---")
    st.subheader("🤖 Análisis de Inteligencia con Gemini AI")
    
    # Crear ID único usando la URL o una combinación de campos
    evento_id = f"analisis_{hash(str(evento.get('url', '')) + fecha_str)}"
    
    col_analyze, col_space = st.columns([1, 3])
    with col_analyze:
        if st.button("🚀 Ejecutar Análisis Completo", type="primary", use_container_width=True):
            if pd.notna(evento["url"]) and str(evento["url"]).strip():
                with st.spinner("🔄 Analizando con Gemini AI..."):
                    resultado = analizar_noticia_completa(evento["url"])
                
                if resultado["success"]:
                    st.session_state[evento_id] = resultado["analisis"]
                    st.success("✅ Análisis completado")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {resultado.get('error', 'No se pudo analizar')}")
            else:
                st.error("❌ No hay URL disponible para analizar")
    
    if evento_id in st.session_state:
        st.markdown("---")
        with st.container():
            st.markdown(st.session_state[evento_id])
            
            col_refresh, col_clear, col_space2 = st.columns([1, 1, 2])
            with col_refresh:
                if st.button("🔄 Re-analizar", use_container_width=True):
                    del st.session_state[evento_id]
                    st.rerun()
            with col_clear:
                if st.button("🗑️ Limpiar Análisis", use_container_width=True):
                    del st.session_state[evento_id]
                    st.rerun()
    else:
        st.info("👆 Haz clic en 'Ejecutar Análisis Completo' para obtener información detallada usando IA")

elif st.session_state.page == "dashboard":
    
    # Header principal mejorado
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="font-size: 48px;">🛡️</div>
                <div>
                    <h1 style="color: white; margin: 0; font-size: 32px; font-weight: 800;">
                        Dark Web / OSINT Monitor
                    </h1>
                    <p style="color: #e0e7ff; margin: 5px 0 0 0; font-size: 16px;">
                        Sistema de Inteligencia para Amenazas de Ransomware
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("### 🎛️ Panel de Filtros")
    st.sidebar.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    
    # Botón de actualización de noticias
    st.sidebar.markdown("### 🔄 Actualizar Datos")
    if st.sidebar.button("📰 Actualizar Noticias", type="primary", use_container_width=True, help="Ejecuta ingest_news.py para obtener nuevos eventos"):
        
        # Crear placeholders para el progreso
        progress_placeholder = st.sidebar.empty()
        status_placeholder = st.sidebar.empty()
        
        # Mostrar estado inicial
        progress_placeholder.progress(0)
        status_placeholder.info("🔄 Iniciando actualización...")
        
        try:
            # Iniciar proceso con Python unbuffered (-u)
            process = subprocess.Popen(
                ["python", "-u", "ingest_news.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            total_fuentes = 0
            fuente_actual = 0
            
            # Leer output en tiempo real
            for line in process.stdout:
                line = line.strip()
                
                # Detectar líneas de progreso (formato: PROGRESS:actual/total:descripción)
                if line.startswith("PROGRESS:"):
                    parts = line.replace("PROGRESS:", "").split(":", 1)
                    
                    if parts[0] == "COMPLETE":
                        progress_placeholder.progress(100)
                        status_placeholder.success("✅ Noticias actualizadas exitosamente")
                        break
                    else:
                        # Parsear progreso
                        progress_parts = parts[0].split("/")
                        if len(progress_parts) == 2:
                            fuente_actual = int(progress_parts[0])
                            total_fuentes = int(progress_parts[1])
                            
                            # Calcular porcentaje
                            if total_fuentes > 0:
                                progreso = int((fuente_actual / total_fuentes) * 100)
                                progress_placeholder.progress(progreso)
                                
                                # Mostrar descripción si existe
                                if len(parts) > 1:
                                    status_placeholder.info(f"🔄 {parts[1]} ({fuente_actual}/{total_fuentes})")
                                else:
                                    status_placeholder.info(f"🔄 Procesando... ({fuente_actual}/{total_fuentes})")
            
            # Esperar a que termine
            process.wait(timeout=600)
            
            if process.returncode == 0:
                status_placeholder.success("✅ Noticias actualizadas exitosamente")
                time.sleep(2)
                st.rerun()
            else:
                stderr = process.stderr.read()
                status_placeholder.error(f"❌ Error al actualizar: {stderr[:200]}")
                
        except subprocess.TimeoutExpired:
            status_placeholder.warning("⏱️ La actualización está tomando mucho tiempo. Continúa en segundo plano.")
        except Exception as e:
            status_placeholder.error(f"❌ Error: {str(e)}")
    
    # Botón de borrar base de datos
    st.sidebar.markdown("")
    if st.sidebar.button("🗑️ Borrar Todos los Eventos", use_container_width=True, help="⚠️ Elimina TODOS los eventos de la base de datos"):
        st.session_state.show_delete_confirmation = True
    
    # Diálogo de confirmación de borrado
    if st.session_state.show_delete_confirmation:
        st.sidebar.error("⚠️ **¿ESTÁS SEGURO?**")
        st.sidebar.warning("Esta acción eliminará TODOS los eventos de la base de datos.")
        
        col1, col2 = st.sidebar.columns(2)
        
        with col1:
            if st.button("✅ Sí, borrar", type="primary", use_container_width=True):
                try:
                    import os
                    
                    csv_path = "data/eventos.csv"
                    
                    # Crear nuevo CSV vacío
                    with open(csv_path, 'w', encoding='utf-8') as f:
                        f.write("fecha,actor,fuente,tipo,indicador,url,confianza,threat_intel\n")
                    
                    st.sidebar.success("✅ Todos los eventos han sido eliminados")
                    st.session_state.show_delete_confirmation = False
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Error al borrar: {str(e)}")
                    st.session_state.show_delete_confirmation = False
        
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.show_delete_confirmation = False
                st.rerun()
    
    st.sidebar.markdown("---")
    
    min_date = df["fecha"].min().date() if not df.empty else datetime.today().date()
    max_date = df["fecha"].max().date() if not df.empty else datetime.today().date()
    date_range = st.sidebar.date_input("📅 Rango de fechas", value=(min_date, max_date))

    actor = st.sidebar.multiselect("🎭 Actor", options=sorted(df["actor"].dropna().unique()), help="Filtra por grupo/actor")
    conf = st.sidebar.multiselect("🎯 Confianza", options=sorted(df["confianza"].dropna().unique()))
    tipo = st.sidebar.multiselect("📊 Tipo", options=sorted(df["tipo"].dropna().unique()))
    
    # Checkbox para incluir eventos de confianza baja (desmarcado por defecto)
    incluir_baja = st.sidebar.checkbox(
        "⚠️ Incluir eventos de confianza baja", 
        value=False,
        help="Por defecto solo se muestran eventos de confianza media y alta"
    )
    
    search = st.sidebar.text_input("🔍 Buscar en indicadores", placeholder="ej. lockbit, dump, smb")

    df_f = df.copy()
    
    # Filtrar por confianza PRIMERO (si no incluye bajas, eliminarlas)
    eventos_filtrados_por_confianza = 0
    if not incluir_baja:
        eventos_baja = len(df_f[df_f["confianza"] == "baja"])
        df_f = df_f[df_f["confianza"] != "baja"]
        eventos_filtrados_por_confianza = eventos_baja
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        # Asegurar que la columna fecha es datetime
        if not pd.api.types.is_datetime64_any_dtype(df_f["fecha"]):
            df_f["fecha"] = pd.to_datetime(df_f["fecha"], errors='coerce')
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

    # Mostrar información de eventos filtrados por confianza
    if eventos_filtrados_por_confianza > 0:
        st.sidebar.markdown("---")
        st.sidebar.info(f"🔒 **{eventos_filtrados_por_confianza}** eventos de confianza baja ocultos")

    # Métricas principales con diseño mejorado
    met = resumen(df_f)
    st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <div style="color: white; font-size: 36px; font-weight: 700;">{}</div>
                <div style="color: #e0e7ff; font-size: 14px; margin-top: 5px;">📊 Total Eventos</div>
            </div>
        """.format(met["total_eventos"]), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <div style="color: white; font-size: 36px; font-weight: 700;">{}</div>
                <div style="color: #ffe4e6; font-size: 14px; margin-top: 5px;">🎭 Actores Únicos</div>
            </div>
        """.format(met["actores_unicos"]), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 20px; border-radius: 10px; text-align: center;">
                <div style="color: white; font-size: 36px; font-weight: 700;">{}</div>
                <div style="color: #e0f2fe; font-size: 14px; margin-top: 5px;">🔤 Menciones</div>
            </div>
        """.format(met["menciones_ransomware"]), unsafe_allow_html=True)
    
    with col4:
        rango = f"{df_f['fecha'].min().date() if not df_f.empty else '—'}<br>↓<br>{df_f['fecha'].max().date() if not df_f.empty else '—'}"
        st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 15px; border-radius: 10px; text-align: center;">
                <div style="color: white; font-size: 16px; font-weight: 700;">{}</div>
                <div style="color: #fffbeb; font-size: 14px; margin-top: 5px;">📅 Rango</div>
            </div>
        """.format(rango), unsafe_allow_html=True)

    st.markdown("<div style='margin: 40px 0;'><hr style='border: 2px solid #e0e0e0;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown("### 📈 Timeline de Eventos")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        timeline = eventos_por_mes(df_f)
        if not timeline.empty:
            st.line_chart(timeline.set_index("mes")["eventos"], height=300, use_container_width=True)
        else:
            st.info("📊 Sin datos para la selección actual.")

        st.markdown("<div style='margin: 30px 0;'><hr style='border: 1px solid #e0e0e0;'></div>", unsafe_allow_html=True)
        
        st.markdown("### 🔝 Top Indicadores")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        top_ind = indicadores_top(df_f)
        if not top_ind.empty:
            # Limitar a 10 indicadores y truncar textos largos
            top_ind_display = top_ind.head(10).copy()
            top_ind_display['indicador'] = top_ind_display['indicador'].apply(
                lambda x: (x[:70] + '...') if len(str(x)) > 70 else x
            )
            st.bar_chart(top_ind_display.set_index("indicador")["conteo"], height=400, use_container_width=True)
        else:
            st.info("📊 No hay indicadores para mostrar.")

    with c2:
        st.markdown("### 👥 Top Actores")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        ta = top_actores(df_f)
        if not ta.empty:
            ta_display = ta.head(8).rename(columns={"conteo": "Eventos"})
            # Tabla con estilo mejorado
            st.dataframe(
                ta_display,
                use_container_width=True,
                hide_index=True,
                height=350
            )
        else:
            st.info("👥 Sin actores en la selección.")

        st.markdown("<div style='margin: 20px 0;'></div>", unsafe_allow_html=True)
        
        st.markdown("### 🎯 Nivel de Confianza")
        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        dc = distrib_confianza(df_f)
        if not dc.empty:
            if "confianza" in dc.columns and "conteo" in dc.columns:
                st.bar_chart(dc.set_index("confianza")["conteo"], height=250, use_container_width=True)
            elif dc.shape[1] >= 2:
                label_col, count_col = dc.columns[0], dc.columns[1]
                st.bar_chart(dc.set_index(label_col)[count_col], height=250, use_container_width=True)
            else:
                st.info("📊 Sin datos de confianza.")
        else:
            st.info("📊 Sin datos de confianza.")

    st.markdown("<div style='margin: 40px 0;'><hr style='border: 2px solid #e0e0e0;'></div>", unsafe_allow_html=True)

    st.markdown("### 📋 Registro de Eventos")
    st.caption("💡 Selecciona un evento para ver el análisis completo con IA")
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    if df_f.empty:
        st.info("🔍 No hay eventos para mostrar con los filtros actuales")
    else:
        # Control de cuántos eventos mostrar por página
        col_control1, col_control2, col_control3 = st.columns([1, 2, 1])
        with col_control1:
            items_por_pagina = st.selectbox(
                "Eventos por página:",
                options=[5, 10, 20, 50],
                index=1,  # Default: 10
                key="eventos_selector"
            )
            # Resetear página si cambia el tamaño
            if items_por_pagina != st.session_state.eventos_por_pagina:
                st.session_state.eventos_por_pagina = items_por_pagina
                st.session_state.pagina_actual = 0
        
        with col_control2:
            st.markdown(f"<div style='padding-top: 8px; text-align: center;'>📊 Total: **{len(df_f)}** eventos en la selección</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)
        
        # Calcular paginación
        df_sorted = df_f.sort_values("fecha", ascending=False).reset_index(drop=True)
        total_eventos = len(df_sorted)
        total_paginas = (total_eventos - 1) // st.session_state.eventos_por_pagina + 1
        
        # Asegurar que pagina_actual esté en rango válido
        if st.session_state.pagina_actual >= total_paginas:
            st.session_state.pagina_actual = max(0, total_paginas - 1)
        
        inicio = st.session_state.pagina_actual * st.session_state.eventos_por_pagina
        fin = min(inicio + st.session_state.eventos_por_pagina, total_eventos)
        
        # Mostrar eventos de la página actual
        for i in range(inicio, fin):
            row = df_sorted.iloc[i]
            
            # Preparar datos
            fecha_display = row['fecha'].date() if pd.notna(row['fecha']) else 'Sin fecha'
            indicador_text = str(row.get('indicador', ''))
            indicador_short = (indicador_text[:80] + '...') if len(indicador_text) > 80 else indicador_text
            
            # Colores de confianza
            conf_colors = {
                "alta": {"bg": "#d1fae5", "border": "#10b981", "text": "#065f46"},
                "media": {"bg": "#fef3c7", "border": "#f59e0b", "text": "#92400e"},
                "baja": {"bg": "#fee2e2", "border": "#ef4444", "text": "#991b1b"}
            }
            conf_key = str(row["confianza"]).lower()
            colors = conf_colors.get(conf_key, {"bg": "#f3f4f6", "border": "#6b7280", "text": "#374151"})
            
            # Card con diseño mejorado
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                    border-left: 5px solid {colors['border']};
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    transition: all 0.3s ease;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                                <span style="
                                    background: {colors['bg']};
                                    color: {colors['text']};
                                    padding: 4px 12px;
                                    border-radius: 20px;
                                    font-size: 12px;
                                    font-weight: 600;
                                    border: 1px solid {colors['border']};
                                ">
                                    🎯 {row["confianza"].upper()}
                                </span>
                                <span style="color: #64748b; font-size: 13px; font-weight: 500;">
                                    📅 {fecha_display}
                                </span>
                            </div>
                            <div style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">
                                🎭 {row["actor"]}
                            </div>
                            <div style="display: flex; gap: 15px; margin-bottom: 10px;">
                                <span style="color: #475569; font-size: 14px;">
                                    <b>Tipo:</b> {row["tipo"]}
                                </span>
                                <span style="color: #475569; font-size: 14px;">
                                    <b>Fuente:</b> {row["fuente"]}
                                </span>
                            </div>
                            {f'<div style="background: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 13px; color: #334155; border-left: 3px solid #3b82f6;"><b>📌 Indicador:</b> {indicador_short}</div>' if indicador_short else ''}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Botón debajo del card
            col_btn, col_space = st.columns([1, 4])
            with col_btn:
                if st.button("🔍 Ver Análisis Completo", key=f"detail_{i}", use_container_width=True, type="primary"):
                    ir_a_detalle(row)
        
        # Controles de paginación
        if total_paginas > 1:
            st.markdown("<div style='margin: 30px 0;'><hr style='border: 1px solid #e0e0e0;'></div>", unsafe_allow_html=True)
            
            col_prev, col_info, col_next = st.columns([1, 2, 1])
            
            with col_prev:
                if st.button("⬅️ Anterior", disabled=(st.session_state.pagina_actual == 0), use_container_width=True):
                    st.session_state.pagina_actual -= 1
                    st.rerun()
            
            with col_info:
                st.markdown(f"""
                    <div style='text-align: center; padding: 10px;'>
                        <span style='font-size: 16px; font-weight: 600; color: #1e293b;'>
                            Página {st.session_state.pagina_actual + 1} de {total_paginas}
                        </span>
                        <br>
                        <span style='font-size: 14px; color: #64748b;'>
                            Mostrando eventos {inicio + 1}-{fin} de {total_eventos}
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_next:
                if st.button("Siguiente ➡️", disabled=(st.session_state.pagina_actual >= total_paginas - 1), use_container_width=True):
                    st.session_state.pagina_actual += 1
                    st.rerun()

    st.markdown("<div style='margin: 30px 0;'></div>", unsafe_allow_html=True)
    
    # Botón de descarga mejorado
    csv = df_f.to_csv(index=False).encode("utf-8")
    col_download, col_space = st.columns([1, 3])
    with col_download:
        st.download_button(
            "📥 Descargar CSV Completo",
            data=csv,
            file_name=f"eventos_ransomware_{datetime.today().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
