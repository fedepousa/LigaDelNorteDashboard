import streamlit as st
import os
import glob
from procesamiento import cargar_y_procesar_categoria

st.set_page_config(page_title="Liga del Norte - Ajedrez", layout="wide", page_icon="♟️")

st.markdown("""
    <style>
    /* Importar fuente Google Fonts (Inter) para un look más moderno */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Título principal con más presencia */
    h1 { 
        color: #1E293B; 
        font-weight: 800; 
        letter-spacing: -1px;
        padding-bottom: 0px;
    }

    /* Convertir los resúmenes (KPIs) en Tarjetas Flotantes */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 20px 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        text-align: center;
        transition: transform 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Etiquetas de los KPIs (Gris sutil) */
    div[data-testid="metric-container"] label {
        color: #64748B !important;
        font-size: 1.05rem !important;
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* Números de los KPIs */
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #0F172A;
        font-weight: 800;
    }

    /* Tunear las Pestañas (Tabs) */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 8px; 
        border-bottom: 2px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        white-space: pre-wrap; 
        background-color: #F1F5F9; 
        border-radius: 8px 8px 0px 0px; 
        padding: 10px 24px; 
        font-size: 15px; 
        font-weight: 600;
        color: #64748B;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        background-color: #FFFFFF !important;
        border-color: #E2E8F0 !important;
        border-bottom-color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("♟️ Liga del Norte de Ajedrez")
st.markdown("<br>", unsafe_allow_html=True)

st.sidebar.title("⚙️ Categorías")

archivos_csv = glob.glob("data/fase_*/*.csv")
categorias_detectadas = set()
for archivo in archivos_csv:
    nombre_archivo = os.path.basename(archivo)
    if nombre_archivo.startswith("posiciones_"):
        cat = nombre_archivo.replace("posiciones_", "").replace(".csv", "")
        categorias_detectadas.add(cat)

categorias_lista = sorted(list(categorias_detectadas)) if categorias_detectadas else ["Libres"]
categoria_sel = st.sidebar.selectbox("Seleccioná la categoría que querés ver:", categorias_lista)

df_fases_todas, acumulado_puntos, acumulado_gp = cargar_y_procesar_categoria(categoria_sel)

if df_fases_todas.empty:
    st.warning(f"No hay datos cargados para la categoría: {categoria_sel}. Ejecutá el scraper primero.")
else:
    col1, col2, col3 = st.columns(3)
    
    total_jugadores = len(acumulado_puntos)
    fases_jugadas = df_fases_todas['Fase'].nunique()
    lider_gp = acumulado_gp.iloc[0]['Jugador'] if not acumulado_gp.empty else "-"
    puntos_lider = acumulado_gp.iloc[0]['Puntos_GP'] if not acumulado_gp.empty else 0

    col1.metric("👥 Jugadores Únicos", total_jugadores)
    col2.metric("🗓️ Fases Disputadas", fases_jugadas)
    col3.metric("🏆 Líder Grand Prix", lider_gp, f"{int(puntos_lider)} pts")

    st.markdown("<br><br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "🏎️ Acumulado Grand Prix", 
        "📈 Acumulado Puntos Tablero",
        "📍 Resultados por Fase"
    ])

    with tab1:
        st.caption("Puntuación por terminar en el Top 10 de cada fase (1°=25pts, 2°=18pts, etc.). Premia la regularidad.")
        max_gp = int(acumulado_gp['Puntos_GP'].max()) if not acumulado_gp.empty and acumulado_gp['Puntos_GP'].max() > 0 else 100
        
        st.dataframe(
            acumulado_gp,
            use_container_width=True,
            hide_index=False,
            column_config={
                "Jugador": st.column_config.TextColumn("Ajedrecista", width="large"),
                "Puntos_GP": st.column_config.ProgressColumn(
                    "Puntos GP",
                    help="Suma de puntos Grand Prix",
                    format="%d pts",
                    min_value=0,
                    max_value=max_gp,
                    width="medium"
                )
            }
        )

    with tab2:
        st.caption("Suma directa de todos los puntos obtenidos en las partidas jugadas a lo largo del año.")
        
        st.dataframe(
            acumulado_puntos,
            use_container_width=True,
            hide_index=False,
            column_config={
                "Jugador": st.column_config.TextColumn("Ajedrecista", width="large"),
                "Puntos": st.column_config.NumberColumn(
                    "Puntos Totales",
                    help="Suma de puntos reales en el tablero",
                    format="%.1f pts",
                    width="medium"
                )
            }
        )

    with tab3:
        fases_disponibles = sorted(df_fases_todas['Fase'].unique())
        fase_sel = st.selectbox("Seleccionar Fase para ver el detalle", fases_disponibles)
        
        df_fase_individual = df_fases_todas[df_fases_todas['Fase'] == fase_sel].copy()
        columnas_visibles = [c for c in df_fase_individual.columns if c not in ['Fase', 'Puntos_GP']]
        
        st.dataframe(
            df_fase_individual[columnas_visibles], 
            use_container_width=True, 
            hide_index=True
        )
