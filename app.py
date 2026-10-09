import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Gestión de Plazas | Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Estilos ----------
st.markdown("""
<style>
    .stApp { background: #F4F7FB; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#111827 0%,#1F2937 100%); }
    [data-testid="stSidebar"] * { color: #F9FAFB; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 18px; color: white;
        background: linear-gradient(115deg,#102A43 0%,#1D4ED8 65%,#0EA5E9 100%);
        margin-bottom: 1.1rem;
    }
    .hero h1 { margin: 0; font-size: 1.85rem; }
    .hero p { margin: .45rem 0 0 0; opacity: .92; }
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #E5EAF2; padding: 15px 17px;
        border-radius: 14px; box-shadow: 0 3px 12px rgba(15,23,42,.04);
    }
    div[data-testid="stMetricLabel"] { color: #64748B; }
    div[data-testid="stMetricValue"] { color: #0F172A; }
    h2, h3 { color: #0F172A; }
    .small-note { color: #64748B; font-size: .85rem; }
</style>
""", unsafe_allow_html=True)

DATA_FILE = Path(__file__).with_name("REPORTE DE PLAZAS VACANTES, OCUPADAS Y RESERVADAS.XLSX")

@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        raw = pd.read_excel(uploaded_file)
    elif DATA_FILE.exists():
        raw = pd.read_excel(DATA_FILE)
    else:
        return pd.DataFrame()

    # Normaliza encabezados y elimina filas completamente vacías
    raw.columns = [str(c).strip() for c in raw.columns]
    raw = raw.dropna(how="all").copy()

    expected = [
        "Red", "Unidad organizativa", "Posición", "Plaza", "Cargo", "Nivel",
        "Situación", "Estado", "TIPO DE RESERVA", "FECHA RESERVA"
    ]
    # Algunas exportaciones pueden traer la fila de encabezados dentro de los datos.
    if "Red" not in raw.columns and len(raw) > 0:
        raw.columns = [str(v).strip() for v in raw.iloc[0].tolist()]
        raw = raw.iloc[1:].copy()

    for col in expected:
        if col not in raw.columns:
            raw[col] = pd.NA

    for col in ["Red", "Unidad organizativa", "Cargo", "Nivel", "Situación", "Estado", "TIPO DE RESERVA"]:
        raw[col] = raw[col].astype("string").str.strip()
        raw[col] = raw[col].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})

    raw["FECHA RESERVA"] = pd.to_datetime(raw["FECHA RESERVA"], errors="coerce")
    return raw

st.markdown("""
<div class="hero">
  <h1>📊 Dashboard de Gestión de Plazas</h1>
  <p>Seguimiento de plazas ocupadas, vacantes y reservadas · Análisis de recursos humanos</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("🔎 Filtros")
    uploaded = st.file_uploader("Cargar archivo Excel (.xlsx)", type=["xlsx"])
    st.caption("Si no cargas otro archivo, se utilizará el Excel incluido junto a app.py.")

df = load_data(uploaded)

if df.empty:
    st.error("No se encontró la base de datos. Coloca el archivo Excel junto a app.py o cárgalo desde el panel lateral.")
    st.stop()

# ---------- Filtros ----------
with st.sidebar:
    filter_columns = [
        ("Red", "Red"),
        ("Unidad organizativa", "Unidad organizativa"),
        ("Cargo", "Cargo"),
        ("Nivel", "Nivel"),
        ("Situación", "Situación"),
        ("Estado", "Estado"),
        ("TIPO DE RESERVA", "Tipo de reserva"),
    ]
    selected = {}
    for col, label in filter_columns:
        options = sorted(df[col].dropna().astype(str).unique().tolist())
        selected[col] = st.multiselect(f"{label}", options, default=[])

filtered = df.copy()
for col, values in selected.items():
    if values:
        filtered = filtered[filtered[col].astype("string").isin(values)]

# ---------- KPIs ----------
total = len(filtered)
occupied = int((filtered["Estado"].str.casefold() == "ocupado").sum())
vacant = int((filtered["Estado"].str.casefold() == "vacante").sum())
reserved = int((filtered["Estado"].str.casefold() == "reservado").sum())
with_budget = int((filtered["Situación"].str.casefold() == "con presupuesto").sum())
without_budget = int((filtered["Situación"].str.casefold() == "sin presupuesto").sum())
occupancy_pct = (occupied / total * 100) if total else 0
vacancy_pct = (vacant / total * 100) if total else 0

st.caption(f"Mostrando **{total:,}** registros de **{len(df):,}** plazas del archivo.")
k1, k2, k3, k4 = st.columns(4)
k1.metric("TOTAL DE PLAZAS", f"{total:,}")
k2.metric("OCUPADAS", f"{occupied:,}", f"{occupancy_pct:.1f}% del total")
k3.metric("VACANTES", f"{vacant:,}", f"{vacancy_pct:.1f}% del total")
k4.metric("RESERVADAS", f"{reserved:,}")

k5, k6, k7 = st.columns(3)
k5.metric("CON PRESUPUESTO", f"{with_budget:,}")
k6.metric("SIN PRESUPUESTO", f"{without_budget:,}")
k7.metric("CARGOS DIFERENTES", f"{filtered['Cargo'].nunique(dropna=True):,}")

st.divider()

# ---------- Gráficos ----------
left, right = st.columns(2)
with left:
    st.subheader("Distribución por estado")
    state_counts = filtered["Estado"].fillna("Sin dato").value_counts().rename_axis("Estado").reset_index(name="Cantidad")
    if not state_counts.empty:
        fig = px.pie(state_counts, names="Estado", values="Cantidad", hole=0.58,
                     color_discrete_sequence=["#16A34A", "#F59E0B", "#7C3AED", "#94A3B8"])
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(l=10,r=10,t=15,b=10), legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar con los filtros seleccionados.")

with right:
    st.subheader("Situación presupuestal")
    budget_counts = filtered["Situación"].fillna("Sin dato").value_counts().rename_axis("Situación").reset_index(name="Cantidad")
    if not budget_counts.empty:
        fig = px.bar(budget_counts, x="Situación", y="Cantidad", text="Cantidad",
                     color="Situación", color_discrete_sequence=["#2563EB", "#F97316", "#94A3B8"])
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Número de plazas",
                          margin=dict(l=10,r=10,t=20,b=10))
        st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Top 10 redes por cantidad de plazas")
    by_red = filtered["Red"].fillna("Sin dato").value_counts().head(10).sort_values().rename_axis("Red").reset_index(name="Cantidad")
    if not by_red.empty:
        fig = px.bar(by_red, x="Cantidad", y="Red", orientation="h", text="Cantidad",
                     color_discrete_sequence=["#2563EB"])
        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_title="Número de plazas", yaxis_title="",
                          margin=dict(l=10,r=30,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Top 10 cargos por cantidad de plazas")
    by_job = filtered["Cargo"].fillna("Sin dato").value_counts().head(10).sort_values().rename_axis("Cargo").reset_index(name="Cantidad")
    if not by_job.empty:
        fig = px.bar(by_job, x="Cantidad", y="Cargo", orientation="h", text="Cantidad",
                     color_discrete_sequence=["#0EA5E9"])
        fig.update_traces(textposition="outside")
        fig.update_layout(xaxis_title="Número de plazas", yaxis_title="",
                          margin=dict(l=10,r=30,t=10,b=10))
        st.plotly_chart(fig, use_container_width=True)

st.subheader("Análisis de reservas")
reservation_data = filtered[filtered["TIPO DE RESERVA"].notna()]
if not reservation_data.empty:
    reserve_counts = reservation_data["TIPO DE RESERVA"].value_counts().head(10).sort_values().rename_axis("Tipo de reserva").reset_index(name="Cantidad")
    fig = px.bar(reserve_counts, x="Cantidad", y="Tipo de reserva", orientation="h", text="Cantidad",
                 color_discrete_sequence=["#7C3AED"])
    fig.update_traces(textposition="outside")
    fig.update_layout(xaxis_title="Número de plazas", yaxis_title="", margin=dict(l=10,r=30,t=10,b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay tipos de reserva registrados para los filtros seleccionados.")

# ---------- Tabla de datos ----------
st.subheader("Detalle de plazas")
search = st.text_input("Buscar por red, unidad organizativa, cargo, plaza o posición", placeholder="Escribe una palabra o código...")
table = filtered.copy()
if search.strip():
    mask = table.astype(str).apply(lambda col: col.str.contains(search.strip(), case=False, na=False)).any(axis=1)
    table = table[mask]

display_cols = [c for c in [
    "Red", "Unidad organizativa", "Posición", "Plaza", "Cargo", "Nivel",
    "Situación", "Estado", "TIPO DE RESERVA", "FECHA RESERVA"
] if c in table.columns]
st.dataframe(table[display_cols], use_container_width=True, hide_index=True, height=420)

csv_data = table[display_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Descargar datos filtrados (CSV)", data=csv_data,
                   file_name="plazas_filtradas.csv", mime="text/csv")

st.markdown('<p class="small-note">Dashboard desarrollado con Python, Streamlit, Pandas y Plotly. Verifica que la información publicada esté autorizada para su divulgación.</p>', unsafe_allow_html=True)
