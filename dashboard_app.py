# -*- coding: utf-8 -*-
"""
Dashboard Financiero - Análisis Comparativo del Estado de Resultado Integral
Superintendencia de Sociedades, Colombia
Metodología CRISP-DM | Proyecto de Grado - Especialización en Analítica de Datos
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────────
# RUTA CONFIGURABLE AL ARCHIVO DE DATOS
# Para cambiar la fuente, modifica únicamente DATA_FILE.
# Funciona tanto localmente como en Streamlit Community Cloud.
# ──────────────────────────────────────────────────────────────
DATA_DIR  = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "310030_Estado de resultado integral, resultado del periodo, por funcion de gasto.xlsx"

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Financiero – Supersociedades",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inyectar CSS mínimo para eliminar artefactos visuales de cursores
st.markdown("""
<style>
/* Eliminar cursor de texto en labels de multiselect y sliders */
.stMultiSelect label, .stSlider label, .stRadio label {
    cursor: default !important;
    user-select: none;
}
section[data-testid="stSidebar"] * {
    cursor: default;
}
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] [role="option"] {
    cursor: pointer !important;
}
/* KPI cards */
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 18px 14px;
    border-left: 5px solid #1B4F72;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    margin-bottom: 6px;
}
.kpi-label { font-size:12px; color:#6c757d; text-transform:uppercase; letter-spacing:.5px; }
.kpi-value { font-size:22px; font-weight:700; color:#1B4F72; margin-top:4px; }
.kpi-help  { font-size:11px; color:#adb5bd; margin-top:2px; }
/* Alerta de limitación de datos */
.data-warning {
    background: #fff3cd;
    border-left: 5px solid #f0ad4e;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────
REVENUE_UMBRAL = 1_000_000   # 1 M COP mínimo para calcular márgenes
MARGEN_RANGO   = (-1.0, 2.0) # -100% a +200% = rango "razonable" para visualización

# ──────────────────────────────────────────────────────────────
# UTILIDADES DE FORMATO
# ──────────────────────────────────────────────────────────────
def fmt_cop(v):
    """$1.234.567.890 — formateado al estilo colombiano."""
    if pd.isna(v):
        return "N/A"
    neg = v < 0
    s = f"{abs(v):,.0f}".replace(",", ".")
    return f"-${s}" if neg else f"${s}"

def fmt_pct(v, dec=2):
    if pd.isna(v): return "N/A"
    return f"{v*100:.{dec}f}%"

def margen_ponderado(df_sub):
    """Σ(gan_neta) / Σ(revenue) solo donde revenue >= umbral."""
    mask = df_sub["revenue"] >= REVENUE_UMBRAL
    r = df_sub.loc[mask, "revenue"].sum()
    g = df_sub.loc[mask & df_sub["gan_neta"].notna(), "gan_neta"].sum()
    return g / r if r > 0 else np.nan

# ──────────────────────────────────────────────────────────────
# CARGA Y LIMPIEZA DE DATOS
# ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="⏳ Cargando y procesando datos…")
def cargar_datos():
    if not DATA_FILE.exists():
        st.error(
            f"⛔ **Archivo de datos no encontrado:** `{DATA_FILE.name}`\n\n"
            "Asegúrate de que el archivo Excel esté en la carpeta `/data/` del proyecto. "
            "Puedes obtenerlo del portal SIIS de la Superintendencia de Sociedades."
        )
        st.stop()
    raw = pd.read_excel(DATA_FILE, sheet_name="Sheet1", engine="openpyxl")
    cols = list(raw.columns)          # nombres originales bien codificados

    # ── Mapeo posicional → alias internos ──
    alias = {
        "razon_social": cols[4],
        "ciiu_orig"   : cols[5],
        "tipo_soc"    : cols[6],
        "depto"       : cols[8],
        "ciudad"      : cols[9],
        "revenue"     : cols[11],
        "costo_ventas": cols[12],
        "gan_bruta"   : cols[13],
        "otros_ing"   : cols[14],
        "costos_dist" : cols[15],
        "gtos_admin"  : cols[16],
        "otros_gtos"  : cols[17],
        "otras_gan"   : cols[18],
        "gan_op"      : cols[19],
        "ing_fin"     : cols[22],
        "cos_fin"     : cols[23],
        "gan_neta"    : cols[34],
    }
    inv_alias = {v: k for k, v in alias.items()}

    df = raw.rename(columns=inv_alias).copy()
    df["NIT"]    = df["NIT"].astype(str).str.strip()
    df["Fecha"]  = pd.to_datetime(df["Fecha de Corte"], errors="coerce")
    df["anio"]   = df["Fecha"].dt.year.astype("Int64")

    # Separar CIIU
    ciiu_ext = df["ciiu_orig"].str.extract(r"^([A-Z]{1,2}\d*)\s*-\s*(.+)$")
    df["ciiu_cod"]    = ciiu_ext[0].fillna("Sin clasificar")
    df["ciiu_sector"] = ciiu_ext[1].fillna(df["ciiu_orig"].fillna("Sin clasificar"))

    # Limpiar tipo societario (quitar prefijo "01. ")
    df["tipo_soc"] = df["tipo_soc"].str.replace(r"^\d+\.\s*", "", regex=True).fillna("No especificado")

    # Numéricas financieras (excepto gan_neta que NO imputamos)
    cols_num = ["revenue","costo_ventas","gan_bruta","otros_ing","costos_dist",
                "gtos_admin","otros_gtos","otras_gan","gan_op","ing_fin","cos_fin"]
    for c in cols_num:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    df["gan_neta"] = pd.to_numeric(df["gan_neta"], errors="coerce")

    # ─── INVESTIGACIÓN PUNTO 1: fechas reales ───────────────────────────
    fechas_unicas  = sorted(df["Fecha"].dropna().unique())
    anios_unicos   = sorted(df["anio"].dropna().unique().tolist())
    solo_2025      = set(anios_unicos) == {2025}
    fechas_str     = [pd.Timestamp(f).strftime("%Y-%m-%d") for f in fechas_unicas]
    dist_fechas    = df["Fecha"].value_counts().sort_index()

    # ─── PUNTO 2: identificar duplicados dentro de cada Periodo ─────────
    dup_exactos  = df.duplicated().sum()
    dup_clave    = df.duplicated(subset=["NIT","Fecha","Periodo"]).sum()

    # Duplicados de NIT dentro de "Periodo Actual" (mismo NIT, distintas Fechas de Corte)
    actual_raw = df[df["Periodo"] == "Periodo Actual"].copy()
    conteo_nit = actual_raw.groupby("NIT").size().reset_index(name="n_registros")
    nits_dup   = conteo_nit[conteo_nit["n_registros"] > 1]["NIT"].tolist()
    tabla_dup_nit = actual_raw[actual_raw["NIT"].isin(nits_dup)][
        ["NIT","razon_social","Fecha","revenue","gan_neta"]
    ].sort_values(["NIT","Fecha"]).copy()
    tabla_dup_nit["revenue_fmt"]  = tabla_dup_nit["revenue"].apply(fmt_cop)
    tabla_dup_nit["gan_neta_fmt"] = tabla_dup_nit["gan_neta"].apply(fmt_cop)

    # ─── Deduplicación: por Periodo + NIT → quedarse con Fecha más reciente ──
    df = df.sort_values("Fecha").drop_duplicates(subset=["NIT","Periodo"], keep="last").copy()

    # Verificar que ya no hay discrepancia
    actual_dedup = df[df["Periodo"] == "Periodo Actual"]
    n_act_total  = len(actual_dedup)
    n_act_unicos = actual_dedup["NIT"].nunique()

    # ─── Márgenes (solo donde revenue >= umbral) ─────────────────────────
    mask_rev = df["revenue"] >= REVENUE_UMBRAL
    n_excluidas_margen = (~mask_rev).sum()

    df["margen_bruto"] = np.where(mask_rev, df["gan_bruta"] / df["revenue"], np.nan)
    df["margen_op"]    = np.where(mask_rev, df["gan_op"]    / df["revenue"], np.nan)
    df["margen_neto"]  = np.where(
        mask_rev & df["gan_neta"].notna(),
        df["gan_neta"] / df["revenue"], np.nan
    )

    # ─── Empresas con margen fuera del rango razonable ──────────────────
    lo, hi = MARGEN_RANGO
    mask_out = df["margen_neto"].notna() & ((df["margen_neto"] < lo) | (df["margen_neto"] > hi))
    tabla_outliers = df[mask_out][["NIT","razon_social","revenue","gan_neta","margen_neto"]].copy()
    tabla_outliers = tabla_outliers.sort_values("margen_neto")

    # ─── Validaciones contables ──────────────────────────────────────────
    calc_bruta = df["revenue"] - df["costo_ventas"]
    diff_bruta = (calc_bruta - df["gan_bruta"]).abs()
    inc_bruta  = (diff_bruta > 100).sum()

    calc_op = (df["gan_bruta"] - df["costos_dist"] - df["gtos_admin"]
               - df["otros_gtos"] + df["otros_ing"] + df["otras_gan"])
    diff_op  = (calc_op - df["gan_op"]).abs()
    inc_op   = (diff_op > 100).sum()

    # ─── % Nulos por columna relevante ───────────────────────────────────
    cols_rep = {
        alias["revenue"]    : "revenue",
        alias["costo_ventas"]: "costo_ventas",
        alias["gan_bruta"]  : "gan_bruta",
        alias["gan_op"]     : "gan_op",
        alias["gan_neta"]   : "gan_neta",
        alias["razon_social"]: "razon_social",
        alias["depto"]      : "depto",
        alias["ciudad"]     : "ciudad",
        alias["ciiu_orig"]  : "ciiu_orig",
        alias["tipo_soc"]   : "tipo_soc",
    }
    nulos_pct = {
        disp: round(df[int_name].isna().mean() * 100, 2)
        for disp, int_name in cols_rep.items()
    }

    meta = {
        # Punto 1
        "fechas_str"       : fechas_str,
        "anios_unicos"     : anios_unicos,
        "solo_2025"        : solo_2025,
        "dist_fechas"      : dist_fechas,
        # Punto 2
        "dup_exactos"      : dup_exactos,
        "dup_clave"        : dup_clave,
        "n_dup_nit_actual" : len(nits_dup),
        "tabla_dup_nit"    : tabla_dup_nit,
        "n_act_total_raw"  : n_act_total + len(tabla_dup_nit) // 2,  # antes de dedup
        "n_act_total_dedup": n_act_total,
        "n_act_unicos"     : n_act_unicos,
        # Punto 3
        "tabla_outliers"   : tabla_outliers,
        "n_excluidas_margen": n_excluidas_margen,
        # Calidad
        "nulos_pct"        : nulos_pct,
        "inc_bruta"        : inc_bruta,
        "inc_op"           : inc_op,
        "total_raw"        : len(raw),
        "total_dedup"      : len(df),
    }
    return df, meta


# ──────────────────────────────────────────────────────────────
# FILTROS
# ──────────────────────────────────────────────────────────────
def sidebar_filtros(df, meta):
    st.sidebar.markdown("""
        <div style='text-align:center;padding:8px 0 4px'>
            <span style='font-size:30px'>📊</span><br>
            <strong style='font-size:14px;color:#1B4F72'>Dashboard Financiero</strong><br>
            <span style='font-size:11px;color:#888'>Supersociedades · CRISP-DM</span>
        </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    # Alerta visible si solo hay año 2025
    if meta["solo_2025"]:
        st.sidebar.warning(
            "⚠️ **Datos de un único año**: Todas las Fechas de Corte son de **2025**. "
            "La comparación temporal disponible es **Periodo Actual vs Anterior** (dentro del mismo reporte), "
            "no una serie histórica 2023-2025."
        )

    st.sidebar.subheader("🔧 Filtros Globales")

    periodo = st.sidebar.radio(
        "Periodo", ["Ambos","Periodo Actual","Periodo Anterior"], index=1
    )

    anios_disp = sorted(df["anio"].dropna().unique().tolist())
    anios_sel  = st.sidebar.multiselect("Año (Fecha de Corte)", anios_disp, default=anios_disp)
    if not anios_sel: anios_sel = anios_disp

    sectores_disp = sorted(df["ciiu_sector"].dropna().unique().tolist())
    sectores_sel  = st.sidebar.multiselect("Sector CIIU", ["Todos"]+sectores_disp, default=["Todos"])

    deptos_disp = sorted(df["depto"].dropna().unique().tolist())
    deptos_sel  = st.sidebar.multiselect("Departamento", ["Todos"]+deptos_disp, default=["Todos"])

    ciudades_disp = sorted(df["ciudad"].dropna().unique().tolist())
    ciudades_sel  = st.sidebar.multiselect("Ciudad", ["Todos"]+ciudades_disp, default=["Todos"])

    tipos_disp = sorted(df["tipo_soc"].dropna().unique().tolist())
    tipos_sel  = st.sidebar.multiselect("Tipo Societario", ["Todos"]+tipos_disp, default=["Todos"])

    # ─ PUNTO 4: slider con formato de moneda ─────────────────────────────
    rev_max = int(df["revenue"].max())
    rev_min_slider, rev_max_slider = st.sidebar.slider(
        "Rango de Ingresos (COP)",
        min_value=0, max_value=rev_max,
        value=(0, rev_max), step=5_000_000,
    )
    # Mostrar los valores formateados debajo del slider
    st.sidebar.caption(
        f"**De:** {fmt_cop(rev_min_slider)}  →  **Hasta:** {fmt_cop(rev_max_slider)}"
    )

    st.sidebar.divider()
    st.sidebar.caption(
        f"Umbral mínimo para márgenes: **{fmt_cop(REVENUE_UMBRAL)}**\n\n"
        f"Rango razonable margen: **{MARGEN_RANGO[0]*100:.0f}% a {MARGEN_RANGO[1]*100:.0f}%**"
    )

    return {
        "periodo"       : periodo,
        "anios"         : anios_sel,
        "sectores"      : sectores_sel,
        "deptos"        : deptos_sel,
        "ciudades"      : ciudades_sel,
        "tipos_soc"     : tipos_sel,
        "rev_min"       : rev_min_slider,
        "rev_max"       : rev_max_slider,
    }


def aplicar_filtros(df, f):
    dff = df.copy()
    if f["periodo"] != "Ambos":
        dff = dff[dff["Periodo"] == f["periodo"]]
    dff = dff[dff["anio"].isin(f["anios"])]
    if "Todos" not in f["sectores"] and f["sectores"]:
        dff = dff[dff["ciiu_sector"].isin(f["sectores"])]
    if "Todos" not in f["deptos"] and f["deptos"]:
        dff = dff[dff["depto"].isin(f["deptos"])]
    if "Todos" not in f["ciudades"] and f["ciudades"]:
        dff = dff[dff["ciudad"].isin(f["ciudades"])]
    if "Todos" not in f["tipos_soc"] and f["tipos_soc"]:
        dff = dff[dff["tipo_soc"].isin(f["tipos_soc"])]
    dff = dff[(dff["revenue"] >= f["rev_min"]) & (dff["revenue"] <= f["rev_max"])]
    return dff


def kpis(dff):
    mask = dff["revenue"] >= REVENUE_UMBRAL
    r    = dff.loc[mask, "revenue"].sum()
    g    = dff.loc[mask & dff["gan_neta"].notna(), "gan_neta"].sum()
    mp   = g / r if r > 0 else np.nan
    med  = dff.loc[mask & dff["margen_neto"].notna(), "margen_neto"].median()
    return {
        "n_empresas"   : dff["NIT"].nunique(),
        "ingresos_tot" : dff["revenue"].sum(),
        "ganancia_tot" : dff["gan_neta"].sum(),
        "mg_ponderado" : mp,
        "mg_mediana"   : med,
    }


# ──────────────────────────────────────────────────────────────
# SECCIÓN 1 — RESUMEN GENERAL
# ──────────────────────────────────────────────────────────────
def tab_resumen(dff, k):
    st.header("📋 Resumen General")

    # ── KPIs ──
    c1,c2,c3,c4,c5 = st.columns(5)
    def card(col, icono, label, val, ayuda=""):
        col.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>{icono} {label}</div>
            <div class='kpi-value'>{val}</div>
            <div class='kpi-help'>{ayuda}</div>
        </div>""", unsafe_allow_html=True)

    card(c1,"🏢","Empresas",         f"{k['n_empresas']:,}",         "NITs únicos filtrados")
    card(c2,"💰","Ingresos Totales",  fmt_cop(k["ingresos_tot"]),     "Periodo seleccionado")
    card(c3,"📈","Ganancia Neta",     fmt_cop(k["ganancia_tot"]),     "Suma ProfitLoss")
    card(c4,"📊","Margen Ponderado",  fmt_pct(k["mg_ponderado"]),     "Σ Ganancia / Σ Ingresos")
    card(c5,"📉","Margen Mediana",    fmt_pct(k["mg_mediana"]),       "Medida robusta vs outliers")

    st.divider()

    # ── PUNTO 3: Boxplot + violin del margen neto ──────────────────────────
    mask = dff["revenue"] >= REVENUE_UMBRAL
    data_mg = dff.loc[mask & dff["margen_neto"].notna(), ["NIT","razon_social","margen_neto","revenue","gan_neta"]].copy()

    col1, col2 = st.columns([1,1])

    with col1:
        # Rango razonable configurable
        lo_ui = st.number_input("Eje Y mínimo (%)", value=-100, step=10, key="mg_lo")
        hi_ui = st.number_input("Eje Y máximo (%)", value=200,  step=10, key="mg_hi")
        lo_frac, hi_frac = lo_ui/100, hi_ui/100

        fig_box = go.Figure()
        fig_box.add_trace(go.Box(
            y=data_mg["margen_neto"],
            name="Margen Neto",
            boxpoints="outliers",
            marker=dict(color="#E74C3C", size=4),
            line_color="#1B4F72",
            fillcolor="#D6EAF8",
        ))
        fig_box.update_layout(
            title="Distribución Margen Neto por Empresa",
            yaxis_title="Margen Neto",
            yaxis_tickformat=".0%",
            yaxis_range=[lo_frac, hi_frac],
            height=400, showlegend=False,
        )
        n_dentro = int(data_mg["margen_neto"].between(lo_frac, hi_frac).sum())
        n_fuera  = len(data_mg) - n_dentro
        st.plotly_chart(fig_box, use_container_width=True)
        st.caption(f"Dentro del rango [{lo_ui}%, {hi_ui}%]: **{n_dentro}** empresas. "
                   f"Fuera: **{n_fuera}** (puntos visibles fuera del eje, documentados en 'Calidad de Datos').")

    with col2:
        data_hist = data_mg[data_mg["margen_neto"].between(lo_frac, hi_frac)]
        fig_hist = px.histogram(
            data_hist, x="margen_neto", nbins=40,
            title=f"Histograma Margen Neto [{lo_ui}% – {hi_ui}%]",
            color_discrete_sequence=["#1ABC9C"],
        )
        fig_hist.update_layout(
            xaxis_tickformat=".0%", height=400,
            showlegend=False, bargap=0.05,
            xaxis_title="Margen Neto", yaxis_title="N° Empresas",
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # Tabla resumen por año
    st.subheader("Resumen por Fecha de Corte")
    por_fecha = dff.groupby("Fecha", as_index=False).agg(
        Empresas=("NIT","nunique"),
        Ingresos=("revenue","sum"),
        Ganancia=("gan_neta","sum"),
    )
    por_fecha["Margen_Pond"] = por_fecha.apply(
        lambda row: margen_ponderado(dff[dff["Fecha"]==row["Fecha"]]), axis=1
    )
    por_fecha["Fecha_str"]    = por_fecha["Fecha"].dt.strftime("%Y-%m-%d")
    por_fecha["Ingresos_fmt"] = por_fecha["Ingresos"].apply(fmt_cop)
    por_fecha["Ganancia_fmt"] = por_fecha["Ganancia"].apply(fmt_cop)
    por_fecha["Margen_fmt"]   = por_fecha["Margen_Pond"].apply(fmt_pct)
    st.dataframe(
        por_fecha[["Fecha_str","Empresas","Ingresos_fmt","Ganancia_fmt","Margen_fmt"]].rename(columns={
            "Fecha_str":"Fecha de Corte","Ingresos_fmt":"Ingresos Totales",
            "Ganancia_fmt":"Ganancia Neta","Margen_fmt":"Margen Ponderado"
        }),
        use_container_width=True, hide_index=True
    )


# ──────────────────────────────────────────────────────────────
# SECCIÓN 2 — SECTORES
# ──────────────────────────────────────────────────────────────
def tab_sectores(dff):
    st.header("🏭 Análisis por Sector (CIIU)")
    top_n = st.slider("Número de sectores", 5, 25, 15, key="n_sec")

    por_sec = dff.groupby("ciiu_sector", as_index=False).agg(
        Ingresos=("revenue","sum"),
        Ganancia=("gan_neta","sum"),
        N_Emp=("NIT","nunique"),
    )
    # Margen ponderado por sector
    mp_sec = []
    for sec in por_sec["ciiu_sector"]:
        sub = dff[dff["ciiu_sector"]==sec]
        mp_sec.append(margen_ponderado(sub))
    por_sec["Margen_Pond"] = mp_sec

    c1,c2 = st.columns(2)
    with c1:
        top = por_sec.nlargest(top_n,"Ingresos")
        fig = px.bar(top, x="Ingresos", y="ciiu_sector", orientation="h",
                     color="Ingresos", color_continuous_scale="Blues",
                     title=f"Top {top_n} Sectores — Ingresos",
                     hover_data={"N_Emp":True},
                     labels={"ciiu_sector":"Sector","Ingresos":"COP"})
        fig.update_layout(yaxis={"categoryorder":"total ascending"},
                          height=440, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        top = por_sec.nlargest(top_n,"Ganancia")
        fig = px.bar(top, x="Ganancia", y="ciiu_sector", orientation="h",
                     color="Ganancia", color_continuous_scale="Greens",
                     title=f"Top {top_n} Sectores — Ganancia Neta",
                     hover_data={"N_Emp":True},
                     labels={"ciiu_sector":"Sector","Ganancia":"COP"})
        fig.update_layout(yaxis={"categoryorder":"total ascending"},
                          height=440, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    top_mg = por_sec.dropna(subset=["Margen_Pond"]).nlargest(top_n,"Margen_Pond")
    fig3 = px.bar(top_mg, x="Margen_Pond", y="ciiu_sector", orientation="h",
                  color="Margen_Pond", color_continuous_scale="RdYlGn",
                  title=f"Top {top_n} Sectores — Margen Ponderado",
                  hover_data={"N_Emp":True},
                  labels={"ciiu_sector":"Sector","Margen_Pond":"Margen"})
    fig3.update_layout(yaxis={"categoryorder":"total ascending"},
                       xaxis_tickformat=".1%", height=420, coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# SECCIÓN 3 — EMPRESAS
# ──────────────────────────────────────────────────────────────
def tab_empresas(dff):
    st.header("🏢 Análisis por Empresa")
    top_n = st.slider("Top N empresas en gráfico", 5, 30, 15, key="n_emp")

    tbl = dff.groupby(["NIT","razon_social"], as_index=False).agg(
        Ingresos=("revenue","sum"),
        Ganancia=("gan_neta","sum"),
        M_Bruto=("margen_bruto","mean"),
        M_Op=("margen_op","mean"),
        M_Neto=("margen_neto","mean"),
        Depto=("depto","first"),
        Sector=("ciiu_sector","first"),
    )

    top = tbl.nlargest(top_n,"Ingresos")
    fig = px.bar(top, x="Ingresos", y="razon_social", orientation="h",
                 color="M_Neto", color_continuous_scale="RdYlGn",
                 title=f"Top {top_n} Empresas por Ingresos (color = Margen Neto)",
                 hover_data={"Ganancia":True,"Depto":True,"Sector":True,"M_Neto":True},
                 labels={"razon_social":"Empresa","Ingresos":"COP","M_Neto":"Margen Neto"})
    fig.update_layout(yaxis={"categoryorder":"total ascending"}, height=520)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Tabla de Empresas")
    tbl2 = tbl.copy()
    for col,fn in [("Ingresos",fmt_cop),("Ganancia",fmt_cop),
                   ("M_Bruto",fmt_pct),("M_Op",fmt_pct),("M_Neto",fmt_pct)]:
        tbl2[col+"_f"] = tbl2[col].apply(fn)
    st.dataframe(
        tbl2[["NIT","razon_social","Sector","Depto",
               "Ingresos_f","Ganancia_f","M_Bruto_f","M_Op_f","M_Neto_f"]].rename(columns={
            "razon_social":"Razón Social","Ingresos_f":"Ingresos",
            "Ganancia_f":"Ganancia Neta","M_Bruto_f":"Mg. Bruto",
            "M_Op_f":"Mg. Operacional","M_Neto_f":"Mg. Neto",
            "Depto":"Departamento","Sector":"Sector CIIU",
        }),
        use_container_width=True, hide_index=True, height=420
    )


# ──────────────────────────────────────────────────────────────
# SECCIÓN 4 — COMPARACIÓN TEMPORAL
# ──────────────────────────────────────────────────────────────
def tab_temporal(df_full, filtros, meta):
    st.header("📅 Comparación Temporal: Periodo Actual vs Anterior")

    # Mostrar siempre la advertencia de alcance del dataset
    if meta["solo_2025"]:
        st.markdown("""
        <div class='data-warning'>
            ⚠️ <strong>Limitación del dataset (importante para la sustentación):</strong><br>
            Todas las Fechas de Corte en este archivo pertenecen al año <strong>2025</strong>
            (cortes: {fechas}). <strong>No es una serie histórica 2023-2025</strong>; es un
            único snapshot de extracción. La columna "Periodo Anterior" representa el ejercicio
            inmediatamente anterior al corte de cada empresa (p.ej. para corte 2025-12-31,
            el periodo anterior es el ejercicio 2024), pero ese dato proviene del mismo formulario
            XBRL, no de una extracción separada. Ajusta el alcance de tu proyecto de grado
            en consecuencia.
        </div>
        """.format(fechas=", ".join(meta["fechas_str"])), unsafe_allow_html=True)

    # Filtros sin restricción de Periodo (necesitamos los dos)
    f2 = filtros.copy()
    f2["periodo"] = "Ambos"
    dff_full = aplicar_filtros(df_full, f2)

    actual   = dff_full[dff_full["Periodo"]=="Periodo Actual"].copy()
    anterior = dff_full[dff_full["Periodo"]=="Periodo Anterior"].copy()

    merged = actual.merge(
        anterior[["NIT","Fecha","revenue","gan_neta","gan_bruta","gan_op"]],
        on=["NIT","Fecha"], how="inner", suffixes=("_act","_ant")
    )

    if merged.empty:
        st.warning("No hay empresas con datos en ambos periodos para los filtros aplicados.")
        return

    st.caption(f"Empresas con datos en **ambos** periodos: **{len(merged)}** de {actual['NIT'].nunique()} en Periodo Actual")

    # Variación % con manejo de ceros
    def var_pct(a, b):
        return np.where((b.notna()) & (b.abs() > 0), (a-b)/b.abs(), np.nan)

    merged["var_ing"]  = var_pct(merged["revenue_act"],  merged["revenue_ant"])
    merged["var_gan"]  = var_pct(merged["gan_neta_act"], merged["gan_neta_ant"])

    # Totales
    tot = {
        "ing_act": merged["revenue_act"].sum(),
        "ing_ant": merged["revenue_ant"].sum(),
        "gan_act": merged["gan_neta_act"].sum(),
        "gan_ant": merged["gan_neta_ant"].sum(),
    }

    # Gráfico comparativo
    fig = go.Figure(data=[
        go.Bar(name="Periodo Anterior", x=["Ingresos","Ganancia Neta"],
               y=[tot["ing_ant"],tot["gan_ant"]], marker_color="#85C1E9",
               text=[fmt_cop(tot["ing_ant"]),fmt_cop(tot["gan_ant"])],
               textposition="outside"),
        go.Bar(name="Periodo Actual", x=["Ingresos","Ganancia Neta"],
               y=[tot["ing_act"],tot["gan_act"]], marker_color="#1B4F72",
               text=[fmt_cop(tot["ing_act"]),fmt_cop(tot["gan_act"])],
               textposition="outside"),
    ])
    fig.update_layout(barmode="group",
                      title="Comparación Agregada: Ingresos y Ganancia Neta",
                      height=420)
    st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        vi = merged["var_ing"].replace([np.inf,-np.inf],np.nan).dropna()
        vi = vi[vi.between(-2,2)]
        fig2 = px.histogram(vi, nbins=35, title="Variación % de Ingresos (±200%)",
                            color_discrete_sequence=["#1ABC9C"])
        fig2.update_layout(xaxis_tickformat=".0%", height=360, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        vg = merged["var_gan"].replace([np.inf,-np.inf],np.nan).dropna()
        vg = vg[vg.between(-5,5)]
        fig3 = px.histogram(vg, nbins=35, title="Variación % de Ganancia Neta (±500%)",
                            color_discrete_sequence=["#F39C12"])
        fig3.update_layout(xaxis_tickformat=".0%", height=360, showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    # Top caídas
    st.subheader("Top 10 Empresas con Mayor Caída en Ganancia Neta")
    caidas = merged[merged["var_gan"].notna()].nsmallest(10,"var_gan")[
        ["NIT","razon_social","gan_neta_ant","gan_neta_act","var_gan"]
    ].copy()
    caidas["Ant"] = caidas["gan_neta_ant"].apply(fmt_cop)
    caidas["Act"] = caidas["gan_neta_act"].apply(fmt_cop)
    caidas["Var"] = caidas["var_gan"].apply(fmt_pct)
    st.dataframe(caidas[["NIT","razon_social","Ant","Act","Var"]].rename(
        columns={"razon_social":"Razón Social","Ant":"Ganancia Anterior",
                 "Act":"Ganancia Actual","Var":"Variación"}),
        use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# SECCIÓN 5 — GEOGRÁFICO
# ──────────────────────────────────────────────────────────────
def tab_geografico(dff):
    st.header("🗺️ Análisis Geográfico")
    st.caption("Ingresos y ganancia son **sumas reales** de COP por departamento/ciudad — no conteos de registros.")

    por_dep = dff.groupby("depto", as_index=False).agg(
        Ingresos=("revenue","sum"), Ganancia=("gan_neta","sum"), N_Emp=("NIT","nunique")
    ).sort_values("Ingresos", ascending=False)

    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(por_dep, x="Ingresos", y="depto", orientation="h",
                     color="Ingresos", color_continuous_scale="Blues",
                     title="Ingresos por Departamento",
                     hover_data={"N_Emp":True,"Ganancia":True},
                     labels={"depto":"Departamento","Ingresos":"COP"})
        fig.update_layout(yaxis={"categoryorder":"total ascending"},
                          height=500, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.bar(por_dep.sort_values("Ganancia",ascending=False),
                      x="Ganancia", y="depto", orientation="h",
                      color="Ganancia", color_continuous_scale="RdYlGn",
                      title="Ganancia Neta por Departamento",
                      hover_data={"N_Emp":True},
                      labels={"depto":"Departamento","Ganancia":"COP"})
        fig2.update_layout(yaxis={"categoryorder":"total ascending"},
                           height=500, coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    top_n_c = st.slider("Top N ciudades", 5, 25, 15, key="n_ciu")
    por_ciu = dff.groupby(["ciudad","depto"], as_index=False).agg(
        Ingresos=("revenue","sum"), Ganancia=("gan_neta","sum"), N_Emp=("NIT","nunique")
    ).nlargest(top_n_c,"Ingresos")

    fig3 = px.bar(por_ciu, x="Ingresos", y="ciudad", orientation="h",
                  color="depto", title=f"Top {top_n_c} Ciudades por Ingresos",
                  hover_data={"N_Emp":True,"Ganancia":True,"depto":True},
                  labels={"ciudad":"Ciudad","Ingresos":"COP","depto":"Departamento"})
    fig3.update_layout(yaxis={"categoryorder":"total ascending"}, height=480)
    st.plotly_chart(fig3, use_container_width=True)

    # Correlación
    st.subheader("Correlación entre Indicadores")
    cols_c  = ["revenue","gan_bruta","gan_op","gan_neta","margen_bruto","margen_op","margen_neto"]
    lbl_c   = ["Ingresos","Gan.Bruta","Gan.Op.","Gan.Neta","Mg.Bruto","Mg.Op.","Mg.Neto"]
    corr = dff[cols_c].rename(columns=dict(zip(cols_c,lbl_c))).corr()
    fig4 = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                     zmin=-1, zmax=1, title="Matriz de Correlación", aspect="auto")
    fig4.update_layout(height=430)
    st.plotly_chart(fig4, use_container_width=True)


# ──────────────────────────────────────────────────────────────
# SECCIÓN 6 — CALIDAD DE DATOS (ampliada con puntos 1, 2, 3)
# ──────────────────────────────────────────────────────────────
def tab_calidad(df_full, meta):
    st.header("🔍 Calidad de Datos")

    # ─── PUNTO 1: Limitación de cobertura temporal ───────────────────────
    st.subheader("📅 Cobertura Temporal del Dataset")
    if meta["solo_2025"]:
        st.error(
            "**⚠️ LIMITACIÓN CRÍTICA DEL PROYECTO:**\n\n"
            "Este dataset corresponde a **un único corte de extracción** "
            f"(año **{meta['anios_unicos'][0]}**). "
            "Las Fechas de Corte disponibles son:\n\n"
            + "\n".join(f"- `{f}`" for f in meta["fechas_str"])
            + "\n\n"
            "La comparación disponible es **Periodo Actual vs. Periodo Anterior** "
            "dentro del mismo reporte XBRL de cada empresa, **no una serie histórica 2023-2025**. "
            "Recomendación para el proyecto de grado: ajustar el alcance de la sección "
            "'Evolución 2023-2025' o complementar con descargas adicionales del portal de datos."
        )
    else:
        st.success(f"El dataset cubre múltiples años: {meta['anios_unicos']}")

    dist = meta["dist_fechas"].reset_index()
    dist.columns = ["Fecha de Corte","N° Registros"]
    dist["Fecha de Corte"] = pd.to_datetime(dist["Fecha de Corte"]).dt.strftime("%Y-%m-%d")
    st.dataframe(dist, use_container_width=True, hide_index=True)

    st.divider()

    # ─── PUNTO 2: NITs duplicados en Periodo Actual ──────────────────────
    st.subheader("🔁 NITs Duplicados en Periodo Actual (mismo NIT, distintas Fechas de Corte)")
    n_dup = meta["n_dup_nit_actual"]
    if n_dup > 0:
        st.warning(
            f"Se encontraron **{n_dup} NITs** con más de 1 registro en 'Periodo Actual' "
            "(misma empresa reportando en distintas Fechas de Corte del mismo año).\n\n"
            "**Criterio de deduplicación aplicado:** se conserva la **Fecha de Corte más reciente** "
            "por NIT dentro de cada Periodo, garantizando 1 fila por empresa."
        )
        tbl = meta["tabla_dup_nit"].copy()
        tbl["Fecha"]       = pd.to_datetime(tbl["Fecha"]).dt.strftime("%Y-%m-%d")
        tbl["revenue_fmt"] = tbl["revenue"].apply(fmt_cop)
        tbl["gan_neta_fmt"]= tbl["gan_neta"].apply(fmt_cop)
        st.dataframe(
            tbl[["NIT","razon_social","Fecha","revenue_fmt","gan_neta_fmt"]].rename(columns={
                "razon_social":"Razón Social","Fecha":"Fecha de Corte",
                "revenue_fmt":"Ingresos","gan_neta_fmt":"Ganancia Neta"
            }),
            use_container_width=True, hide_index=True
        )
        st.caption("Después de deduplicar: 1 registro por NIT por Periodo — sin discrepancia.")
    else:
        st.success("No se encontraron NITs duplicados dentro del mismo Periodo.")

    st.divider()

    # ─── PUNTO 3: Empresas con margen fuera del rango razonable ─────────
    st.subheader(f"📊 Empresas con Margen Neto Fuera del Rango Razonable [{MARGEN_RANGO[0]*100:.0f}% – {MARGEN_RANGO[1]*100:.0f}%]")
    outliers = meta["tabla_outliers"].copy()
    n_out = len(outliers)
    if n_out > 0:
        st.warning(
            f"**{n_out} empresa(s)** tienen margen neto fuera del rango "
            f"[{MARGEN_RANGO[0]*100:.0f}%, {MARGEN_RANGO[1]*100:.0f}%]. "
            "Estas aparecen como puntos en el boxplot pero **no distorsionan** el KPI de "
            "margen ponderado (que usa suma de totales, no promedio de individuales). "
            "Se listan aquí para documentación y posible revisión manual."
        )
        outliers["Ingresos"]  = outliers["revenue"].apply(fmt_cop)
        outliers["Ganancia"]  = outliers["gan_neta"].apply(fmt_cop)
        outliers["Margen_f"]  = outliers["margen_neto"].apply(lambda x: f"{x*100:.1f}%")
        st.dataframe(
            outliers[["NIT","razon_social","Ingresos","Ganancia","Margen_f"]].rename(columns={
                "razon_social":"Razón Social","Margen_f":"Margen Neto"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.success("Ninguna empresa tiene margen fuera del rango razonable.")

    st.divider()

    # ─── Nulos ───────────────────────────────────────────────────────────
    st.subheader("❓ Valores Faltantes por Columna Relevante")
    nulos_df = pd.DataFrame.from_dict(
        meta["nulos_pct"], orient="index", columns=["% Nulos"]
    ).reset_index().rename(columns={"index":"Columna"}).sort_values("% Nulos", ascending=False)
    fig_n = px.bar(nulos_df, x="% Nulos", y="Columna", orientation="h",
                   color="% Nulos", color_continuous_scale="Oranges",
                   range_x=[0,100], title="% de Valores Faltantes")
    fig_n.update_layout(yaxis={"categoryorder":"total ascending"},
                        height=400, coloraxis_showscale=False)
    st.plotly_chart(fig_n, use_container_width=True)

    st.divider()

    # ─── Validaciones contables ──────────────────────────────────────────
    st.subheader("✅ Validaciones Contables")
    c1,c2 = st.columns(2)
    with c1:
        ico = "✅" if meta["inc_bruta"]==0 else "⚠️"
        st.info(f"{ico} **Ingresos − Costo = Ganancia Bruta**: {meta['inc_bruta']} inconsistencias (diferencia > 100 COP)")
    with c2:
        ico = "✅" if meta["inc_op"]==0 else "⚠️"
        st.info(f"{ico} **Ganancia Operacional (fórmula)**: {meta['inc_op']} inconsistencias")

    st.divider()

    # ─── Decisiones documentadas ─────────────────────────────────────────
    st.subheader("📋 Decisiones de Limpieza Documentadas")
    with st.expander("Ver tabla completa de decisiones"):
        st.markdown(f"""
| Decisión | Justificación |
|---|---|
| **Deduplicación**: conservar Fecha más reciente por NIT+Periodo | {meta["n_dup_nit_actual"]} NITs reportaron en múltiples fechas de corte. Conservar el más reciente refleja el estado financiero más actualizado. |
| **Nulos en partidas financieras → 0** | NIIF: partida no reportada = saldo cero (ej. empresa sin costos de distribución). |
| **`gan_neta` → NO imputar** | Es la variable objetivo; imputar con 0 generaría márgenes artificiales. |
| **Margen: excluir revenue < {fmt_cop(REVENUE_UMBRAL)}** | Evita márgenes infinitos/absurdos. Filas excluidas: **{meta['n_excluidas_margen']}**. |
| **Margen ponderado = Σ(Ganancia)/Σ(Ingresos)** | Evita el bug del promedio simple que generaba −1.8M%. |
| **Dataset solo cubre 2025** | Limitación de la fuente; la comparación Actual/Anterior es intra-reporte, no interanual multi-año. |
        """)


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
def main():
    df, meta = cargar_datos()
    filtros  = sidebar_filtros(df, meta)
    dff      = aplicar_filtros(df, filtros)
    k        = kpis(dff)

    st.markdown("""
        <h1 style='color:#1B4F72;font-size:24px;margin-bottom:2px'>
        📊 Análisis Comparativo del Estado de Resultado Integral
        </h1>
        <p style='color:#666;font-size:13px;margin-top:0'>
        Superintendencia de Sociedades · Colombia · Metodología CRISP-DM
        </p>
    """, unsafe_allow_html=True)

    # ── ADVERTENCIA DE ALCANCE (Requisito funcional #4) ───────────────────
    fechas_disp = ", ".join(meta["fechas_str"]) if meta["fechas_str"] else "No disponible"
    with st.expander("ℹ️ Alcance y limitaciones del tablero — leer antes de usar", expanded=False):
        st.markdown(f"""
        **Este tablero es una herramienta de análisis académico.** No constituye un aval,
        certificación ni calificación de riesgo crediticio por parte de la
        **Superintendencia de Sociedades de Colombia**.

        **Limitaciones conocidas del dataset:**
        - Los estados financieros corresponden a los **reportados por las propias empresas** al SIIS;
          su veracidad es responsabilidad del reportante.
        - La comparación entre empresas puede no ser homogénea si difieren en **tipo de estado
          financiero** (individual, separado o consolidado) o en **fecha de corte**.
        - Los valores nulos se muestran como **"Sin reporte"**; los márgenes con denominador cero
          se muestran como **"No aplica / No comparable"** (nunca como 0% ni error silencioso).
        - **Este tablero no simula ni imputa datos faltantes.**
        - Las fechas de corte disponibles en el dataset actual son: **{fechas_disp}**
        - Si el dataset contiene un único año de corte, la sección "Temporal" compara
          **Periodo Actual vs. Anterior dentro del mismo reporte XBRL**, no una serie histórica.
        - Al existir más de una Fecha de Corte por empresa, se conserva la **más reciente por NIT+Periodo**
          (criterio explícito, visible en la pestaña "Calidad de Datos").
        """)

    st.divider()

    tabs = st.tabs([
        "📋 Resumen",
        "🏭 Sectores",
        "🏢 Empresas",
        "📅 Temporal",
        "🗺️ Geográfico",
        "🔍 Calidad de Datos",
    ])
    with tabs[0]: tab_resumen(dff, k)
    with tabs[1]: tab_sectores(dff)
    with tabs[2]: tab_empresas(dff)
    with tabs[3]: tab_temporal(df, filtros, meta)
    with tabs[4]: tab_geografico(dff)
    with tabs[5]: tab_calidad(df, meta)

    # ── PIE DE PÁGINA — FUENTE Y FECHA DE CORTE (Requisito funcional #5) ──
    st.divider()
    n_emp_total = df["NIT"].nunique()
    st.markdown(
        f"""
        <div style='font-size:11px;color:#888;text-align:center;padding:8px 0 16px'>
            <strong>Fuente:</strong> Sistema Integrado de Información Societaria (SIIS) —
            Superintendencia de Sociedades de Colombia &nbsp;·&nbsp;
            <strong>Archivo:</strong> {DATA_FILE.name} &nbsp;·&nbsp;
            <strong>Fechas de corte disponibles:</strong> {fechas_disp} &nbsp;·&nbsp;
            <strong>Empresas en el dataset:</strong> {n_emp_total:,} NITs únicos<br>
            <em>Este tablero es de uso académico. No constituye aval de la Superintendencia de Sociedades
            ni calificación de riesgo crediticio.</em>
        </div>
        """,
        unsafe_allow_html=True,
    )



if __name__ == "__main__":
    main()
