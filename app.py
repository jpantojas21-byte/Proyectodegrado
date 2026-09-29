import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ==========================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y TEMA PROFESIONAL
# ==========================================================================
st.set_page_config(
    page_title="DataMetrics — Business Intelligence Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText, button, input, select {
        font-family: 'Inter', sans-serif !important;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1440px;
    }

    /* ─── KPI CARDS ─────────────────────────────────────────────────────── */
    .kpi-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(139,92,246,0.04) 100%);
        border: 1px solid rgba(99,102,241,0.18);
        border-radius: 14px;
        padding: 1.25rem 1.5rem;
        position: relative;
        overflow: hidden;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0;
        width: 4px; height: 100%;
        background: linear-gradient(180deg, #6366f1, #8b5cf6);
        border-radius: 4px 0 0 4px;
    }
    .kpi-card:hover {
        box-shadow: 0 8px 24px rgba(99,102,241,0.15);
        transform: translateY(-1px);
    }
    .kpi-card-positive::before { background: linear-gradient(180deg, #10b981, #059669); }
    .kpi-card-negative::before { background: linear-gradient(180deg, #ef4444, #dc2626); }
    .kpi-card-neutral::before  { background: linear-gradient(180deg, #6366f1, #8b5cf6); }
    .kpi-card-count::before    { background: linear-gradient(180deg, #0ea5e9, #0284c7); }

    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #94a3b8;
        margin-bottom: 0.35rem;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        line-height: 1.1;
        color: #1e293b;
    }
    .kpi-sub {
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 0.4rem;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .sub-positive { color: #10b981; }
    .sub-negative { color: #ef4444; }
    .sub-neutral  { color: #64748b; }

    /* ─── SECTION HEADERS ────────────────────────────────────────────────── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 0.75rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(99,102,241,0.15);
    }
    .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1e293b;
        letter-spacing: -0.2px;
    }
    .section-badge {
        font-size: 0.7rem;
        font-weight: 600;
        background: rgba(99,102,241,0.12);
        color: #6366f1;
        padding: 2px 8px;
        border-radius: 99px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ─── DASHBOARD HEADER ───────────────────────────────────────────────── */
    .dash-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 60%, #4338ca 100%);
        border-radius: 16px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        color: #fff;
    }
    .dash-title {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0 0 0.2rem 0;
    }
    .dash-subtitle {
        font-size: 0.88rem;
        color: rgba(255,255,255,0.65);
        margin: 0;
    }
    .dash-meta {
        display: flex;
        gap: 20px;
        margin-top: 1rem;
        flex-wrap: wrap;
    }
    .dash-meta-item {
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 8px;
        padding: 0.35rem 0.8rem;
        font-size: 0.78rem;
        color: rgba(255,255,255,0.9);
        font-weight: 500;
    }
    .dash-meta-item b { color: #fff; }

    /* ─── FILTER CHIP ACTIVE ─────────────────────────────────────────────── */
    .filter-active-bar {
        background: rgba(99,102,241,0.08);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 8px;
        padding: 0.5rem 0.85rem;
        font-size: 0.78rem;
        color: #4f46e5;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    /* ─── DARK MODE OVERRIDES ────────────────────────────────────────────── */
    @media (prefers-color-scheme: dark) {
        .kpi-card { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.09); }
        .kpi-value { color: #f1f5f9; }
        .section-title { color: #e2e8f0; }
    }

    /* ─── SIDEBAR ────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] { background: #0f172a; }
    section[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 { color: #f8fafc !important; }

    .sidebar-brand {
        font-size: 1.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #818cf8, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.3px;
    }
    .sidebar-section {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: #475569 !important;
        margin: 1rem 0 0.35rem 0;
    }
    .file-badge {
        background: rgba(99,102,241,0.15);
        border: 1px solid rgba(99,102,241,0.35);
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
    }

    /* ─── INSIGHT CARDS ──────────────────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 10px !important;
        border-left-width: 4px !important;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================================================
# 2. FUNCIONES DE DETECCIÓN Y PROCESAMIENTO
# ==========================================================================

def fmt_number(val, is_currency=True):
    """Formatea número de forma compacta y profesional."""
    if abs(val) >= 1_000_000:
        formatted = f"{val/1_000_000:.2f}M"
    elif abs(val) >= 1_000:
        formatted = f"{val/1_000:.1f}K"
    else:
        formatted = f"{val:,.2f}"
    return f"${formatted}" if is_currency else formatted

def limpiar_columna_numerica(series):
    s_clean = series.astype(str).str.replace(r'[^0-9.\-]', '', regex=True)
    return pd.to_numeric(s_clean, errors='coerce').fillna(0.0)

def procesar_columna_fecha(series):
    return pd.to_datetime(series, errors='coerce').fillna(pd.Timestamp.now())

def detectar_columnas(df):
    num_cols, cat_cols, date_cols = [], [], []
    for col in df.columns:
        if df[col].isna().all():
            continue
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
            continue
        col_str = str(col).lower()
        if pd.api.types.is_numeric_dtype(df[col]):
            is_id = any(w in col_str for w in ['id', 'code', 'codigo', 'key', 'pk'])
            is_year = col_str in ['year', 'año', 'anio']
            if not is_id and not is_year:
                num_cols.append(col)
            if df[col].nunique() <= 30:
                cat_cols.append(col)
            continue
        try:
            sample = df[col].dropna().head(100)
            if not sample.empty:
                has_date_pattern = sample.astype(str).str.contains(r'\d[-/]\d', regex=True).any()
                if has_date_pattern:
                    parsed = pd.to_datetime(sample, errors='coerce')
                    if parsed.notna().sum() / len(sample) >= 0.8:
                        date_cols.append(col)
                        continue
        except Exception:
            pass
        if df[col].nunique() > 0:
            cat_cols.append(col)

    metric_keys = ['sale', 'venta', 'profit', 'ganancia', 'utilidad', 'monto', 'total',
                   'price', 'precio', 'amount', 'revenue', 'ingreso', 'cost', 'costo', 'qty', 'cantidad']
    cat_keys = ['category', 'categoría', 'categoria', 'region', 'región', 'zona',
                'segment', 'segmento', 'sub', 'rubro', 'tipo', 'departamento', 'department']

    def score_metric(c):
        c_l = str(c).lower()
        for i, w in enumerate(metric_keys):
            if w in c_l:
                return i
        return len(metric_keys)

    def score_cat(c):
        c_l = str(c).lower()
        card = df[c].nunique()
        s = 100
        for i, w in enumerate(cat_keys):
            if w in c_l:
                s = i
                break
        if card > 30: s += 50
        if card <= 1: s += 150
        return s

    return sorted(num_cols, key=score_metric), sorted(cat_cols, key=score_cat), date_cols


def generar_mock_data():
    categorias = {
        'Tecnología': ['Teléfonos', 'Computadoras', 'Accesorios'],
        'Material de Oficina': ['Almacenamiento', 'Papel', 'Carpetas'],
        'Muebles': ['Sillas', 'Mesas', 'Libreros']
    }
    regiones = ['Norte', 'Sur', 'Este', 'Centro', 'Oeste']
    segmentos = ['Consumidor', 'Corporativo', 'Oficina en Casa']
    clientes = ['A. Gómez', 'M. Rodríguez', 'J. Pérez', 'S. Martínez',
                'C. Sánchez', 'L. Díaz', 'A. Castro', 'V. Ruiz',
                'D. Morales', 'C. Fernández', 'J. Lopez', 'I. Silva']
    np.random.seed(42)
    rows = []
    idx = 1000
    for year in [2023, 2024, 2025]:
        for month in range(1, 13):
            for _ in range(np.random.randint(2, 5)):
                idx += 1
                cat = np.random.choice(list(categorias.keys()))
                sub = np.random.choice(categorias[cat])
                sales = round(np.random.uniform(
                    200, 2200 if cat == 'Tecnología' else (300, 1500)[cat == 'Muebles']), 2)
                profit = round(sales * np.random.uniform(
                    0.12, 0.45) if cat == 'Tecnología' else
                    sales * np.random.uniform(-0.15, 0.28) if cat == 'Muebles' else
                    sales * np.random.uniform(0.18, 0.60), 2)
                rows.append({
                    'Order ID': f"CA-{year}-{idx}",
                    'Order Date': pd.Timestamp(year, month, np.random.randint(1, 29)).strftime('%Y-%m-%d'),
                    'Customer Name': np.random.choice(clientes),
                    'Segment': np.random.choice(segmentos),
                    'Region': np.random.choice(regiones),
                    'Category': cat, 'Sub-Category': sub,
                    'Sales': sales, 'Profit': profit
                })
    return pd.DataFrame(rows)


def descargar_plantilla():
    headers = ['Order ID', 'Order Date', 'Customer Name', 'Segment', 'Region',
               'Category', 'Sub-Category', 'Sales', 'Profit']
    rows = [
        ['CA-2026-0001', '2026-05-26', 'Nombre Cliente', 'Consumidor', 'Norte', 'Tecnología', 'Teléfonos', '899.99', '150.00'],
        ['CA-2026-0002', '2026-05-27', 'Otro Cliente', 'Corporativo', 'Sur', 'Muebles', 'Sillas', '350.50', '-12.00'],
    ]
    return pd.DataFrame(rows, columns=headers).to_csv(index=False).encode('utf-8-sig')


# ==========================================================================
# 3. SIDEBAR — CARGA DE DATOS
# ==========================================================================
if 'df_persistido' not in st.session_state:
    st.session_state.df_persistido = None
if 'nombre_archivo_activo' not in st.session_state:
    st.session_state.nombre_archivo_activo = None

st.sidebar.markdown('<div class="sidebar-brand">DataMetrics</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div style="font-size:0.72rem;color:#475569;margin-top:2px;margin-bottom:14px;">Business Intelligence Dashboard</div>', unsafe_allow_html=True)


# Resolver fuente de datos
if st.session_state.df_persistido is not None:
    df_raw = st.session_state.df_persistido.copy()
else:
    if os.path.exists('datos_ejemplo.csv'):
        df_raw = pd.read_csv('datos_ejemplo.csv')
    else:
        df_raw = generar_mock_data()

df = df_raw.copy()
num_cols, cat_cols, date_cols = detectar_columnas(df)

if not num_cols:
    df['Conteo'] = 1.0
    num_cols = ['Conteo']
if not cat_cols:
    df['Categoría'] = 'General'
    cat_cols = ['Categoría']

archivo_id = st.session_state.nombre_archivo_activo or 'default'

# ==========================================================================
# 4. SIDEBAR — CONFIGURACIÓN DE COLUMNAS
# ==========================================================================
st.sidebar.markdown('<div class="sidebar-section">Mapeo de Columnas</div>', unsafe_allow_html=True)

with st.sidebar.expander("Configurar columnas del análisis", expanded=False):
    sel_m1 = st.selectbox("Métrica Principal", num_cols, index=0,
                          key=f"cfg_m1_{archivo_id}",
                          help="Columna numérica a analizar como indicador principal (ej. Ventas, Ingresos).")
    sel_m2 = st.selectbox("Métrica Secundaria", num_cols,
                          index=min(1, len(num_cols) - 1),
                          key=f"cfg_m2_{archivo_id}",
                          help="Segunda métrica de comparación (ej. Ganancias, Costos).")
    sel_c1 = st.selectbox("Dimensión Principal", cat_cols, index=0,
                          key=f"cfg_c1_{archivo_id}",
                          help="Columna categórica para el eje principal de agrupación.")
    sel_c2 = st.selectbox("Dimensión Secundaria", cat_cols,
                          index=min(1, len(cat_cols) - 1),
                          key=f"cfg_c2_{archivo_id}",
                          help="Segunda dimensión categórica para distribución y comparación.")
    if date_cols:
        sel_fecha = st.selectbox("Columna de Fecha", ["(Ninguna)"] + date_cols,
                                 index=1 if date_cols else 0,
                                 key=f"cfg_fecha_{archivo_id}")
    else:
        sel_fecha = "(Ninguna)"

# Preparar columnas
df[sel_m1] = limpiar_columna_numerica(df[sel_m1])
if sel_m2 != sel_m1:
    df[sel_m2] = limpiar_columna_numerica(df[sel_m2])
else:
    df['__m2__'] = df[sel_m1].copy()
    sel_m2 = '__m2__'

tiene_fecha = sel_fecha != "(Ninguna)"
if tiene_fecha:
    df['__date__'] = procesar_columna_fecha(df[sel_fecha])
    df['__year__'] = df['__date__'].dt.year.astype(int)
    df['__ym__'] = df['__date__'].dt.to_period('M')

# ==========================================================================
# 5. SIDEBAR — FILTROS ANALÍTICOS
# ==========================================================================
st.sidebar.markdown('<div class="sidebar-section">Filtros Analíticos</div>', unsafe_allow_html=True)

# Limpiar filtros si cambió el archivo
if st.session_state.get('_last_file') != archivo_id:
    for k in list(st.session_state.keys()):
        if k.startswith('flt_'):
            del st.session_state[k]
    st.session_state['_last_file'] = archivo_id

c1_opts = sorted(df[sel_c1].dropna().unique().tolist())
flt_c1 = st.sidebar.selectbox(f"{sel_c1}", ["Todos"] + c1_opts, key=f"flt_c1_{archivo_id}")

c2_opts = sorted(df[sel_c2].dropna().unique().tolist())
flt_c2 = st.sidebar.selectbox(f"{sel_c2}", ["Todos"] + c2_opts, key=f"flt_c2_{archivo_id}")

if tiene_fecha:
    year_opts = sorted(df['__year__'].dropna().unique().tolist(), reverse=True)
    flt_year = st.sidebar.selectbox("Año", ["Todos"] + [str(y) for y in year_opts],
                                    key=f"flt_year_{archivo_id}")
else:
    flt_year = "Todos"

n_active = sum([flt_c1 != "Todos", flt_c2 != "Todos", flt_year != "Todos"])
if st.sidebar.button(f"Restablecer filtros{(' (' + str(n_active) + ' activos)') if n_active else ''}",
                     use_container_width=True):
    for k in [f"flt_c1_{archivo_id}", f"flt_c2_{archivo_id}", f"flt_year_{archivo_id}"]:
        st.session_state.pop(k, None)
    st.rerun()

# Aplicar filtros
df_f = df.copy()
if flt_c1 != "Todos":
    df_f = df_f[df_f[sel_c1] == flt_c1]
if flt_c2 != "Todos":
    df_f = df_f[df_f[sel_c2] == flt_c2]
if tiene_fecha and flt_year != "Todos":
    df_f = df_f[df_f['__year__'] == int(flt_year)]

# Plantilla sidebar
st.sidebar.markdown('<div class="sidebar-section">Recursos</div>', unsafe_allow_html=True)
st.sidebar.download_button("Descargar plantilla CSV", data=descargar_plantilla(),
                           file_name="plantilla_datos.csv", mime="text/csv",
                           use_container_width=True)

# ==========================================================================
# 6. CABECERA PRINCIPAL
# ==========================================================================
nombre_dataset = st.session_state.nombre_archivo_activo or "Datos de demostración"
filtros_desc = []
if flt_c1 != "Todos": filtros_desc.append(f"{sel_c1}: {flt_c1}")
if flt_c2 != "Todos": filtros_desc.append(f"{sel_c2}: {flt_c2}")
if flt_year != "Todos": filtros_desc.append(f"Año: {flt_year}")
filtros_str = " · ".join(filtros_desc) if filtros_desc else "Sin filtros activos"
pct_shown = (len(df_f) / len(df) * 100) if len(df) > 0 else 0

st.markdown(f"""
<div class="dash-header">
    <div class="dash-title">Panel de Análisis de Datos</div>
    <div class="dash-meta">
        <div class="dash-meta-item">Registros visibles: <b>{len(df_f):,}</b> / {len(df):,} ({pct_shown:.0f}%)</div>
        <div class="dash-meta-item">Métrica principal: <b>{sel_m1}</b></div>
        <div class="dash-meta-item">Dimensión principal: <b>{sel_c1}</b></div>
        <div class="dash-meta-item">Filtros: <b>{filtros_str}</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

if n_active > 0:
    st.markdown(
        f'<div class="filter-active-bar">Mostrando datos filtrados por: {filtros_str}</div>',
        unsafe_allow_html=True
    )

# ==========================================================================
# 7. KPIs — INDICADORES CLAVE
# ==========================================================================
total_m1  = df_f[sel_m1].sum()
total_m2  = df_f[sel_m2].sum()
avg_m1    = df_f[sel_m1].mean() if len(df_f) > 0 else 0
max_m1    = df_f[sel_m1].max() if len(df_f) > 0 else 0
n_records = len(df_f)

# Calcular benchmarks vs total
total_m1_all = df[sel_m1].sum()
total_m2_all = df[sel_m2].sum()
ratio_m2_m1  = (total_m2 / total_m1 * 100) if total_m1 != 0 else 0
vs_total_pct = ((total_m1 / total_m1_all) * 100 - 100) if total_m1_all > 0 else 0

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card kpi-card-neutral">
        <div class="kpi-label">{sel_m1} Total</div>
        <div class="kpi-value">{fmt_number(total_m1)}</div>
        <div class="kpi-sub sub-neutral">Suma acumulada del período</div>
    </div>""", unsafe_allow_html=True)

with k2:
    m2_cls = "positive" if total_m2 >= 0 else "negative"
    m2_arrow = "▲" if total_m2 >= 0 else "▼"
    ratio_lbl = f"{m2_arrow} {abs(ratio_m2_m1):.1f}% de {sel_m1}"
    m2_name = sel_m2 if sel_m2 != '__m2__' else sel_m1
    st.markdown(f"""
    <div class="kpi-card kpi-card-{m2_cls}">
        <div class="kpi-label">{m2_name} Total</div>
        <div class="kpi-value">{fmt_number(total_m2)}</div>
        <div class="kpi-sub sub-{m2_cls}">{ratio_lbl}</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card kpi-card-neutral">
        <div class="kpi-label">Promedio por Registro</div>
        <div class="kpi-value">{fmt_number(avg_m1)}</div>
        <div class="kpi-sub sub-neutral">Media de {sel_m1}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card kpi-card-count">
        <div class="kpi-label">Registros Analizados</div>
        <div class="kpi-value">{n_records:,}</div>
        <div class="kpi-sub sub-neutral">{pct_shown:.0f}% del total cargado</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================================
# 8. GRÁFICAS PRINCIPALES (FILA 1)
# ==========================================================================
PALETTE_GRAD  = ['#c7d2fe', '#a5b4fc', '#818cf8', '#6366f1', '#4f46e5', '#4338ca', '#3730a3']
PALETTE_MULTI = ['#6366f1', '#10b981', '#0ea5e9', '#f59e0b', '#ec4899', '#8b5cf6', '#14b8a6']
CHART_H = 340

def apply_common_layout(fig, height=CHART_H):
    fig.update_layout(
        height=height,
        margin=dict(l=16, r=16, t=32, b=16),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter, sans-serif', size=12, color='#475569'),
        legend=dict(font=dict(size=11), bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(showgrid=True, gridcolor='rgba(100,116,139,0.1)', zeroline=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(100,116,139,0.1)', zeroline=False),
    )
    return fig

g1, g2 = st.columns([1.1, 0.9])

# --- Gráfica 1: Barras horizontales por Dimensión Principal ---
with g1:
    top_n = min(15, df_f[sel_c1].nunique())
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">{sel_m1} por {sel_c1}</span>
        <span class="section-badge">Top {top_n}</span>
    </div>""", unsafe_allow_html=True)

    if not df_f.empty:
        df_bar = (df_f.groupby(sel_c1)[sel_m1].sum()
                  .reset_index()
                  .sort_values(sel_m1, ascending=True)
                  .tail(top_n))
        df_bar['pct'] = df_bar[sel_m1] / df_bar[sel_m1].sum() * 100

        fig_bar = px.bar(df_bar, x=sel_m1, y=sel_c1, orientation='h',
                         text=df_bar[sel_m1].apply(fmt_number),
                         color=sel_m1, color_continuous_scale=PALETTE_GRAD,
                         custom_data=['pct'])
        fig_bar.update_traces(
            textposition='outside',
            hovertemplate=f"<b>%{{y}}</b><br>{sel_m1}: %{{x:,.2f}}<br>Participación: %{{customdata[0]:.1f}}%<extra></extra>"
        )
        fig_bar.update_layout(coloraxis_showscale=False, yaxis_title='', xaxis_title=sel_m1)
        apply_common_layout(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay datos para mostrar con los filtros actuales.")

# --- Gráfica 2: Evolución temporal o ranking por dimensión secundaria ---
with g2:
    if tiene_fecha and '__ym__' in df_f.columns and not df_f.empty:
        st.markdown(f"""
        <div class="section-header">
            <span class="section-title">Tendencia Temporal</span>
            <span class="section-badge">{sel_m1}</span>
        </div>""", unsafe_allow_html=True)

        df_time = (df_f.groupby('__ym__')[sel_m1].sum().reset_index())
        df_time['__ym__'] = df_time['__ym__'].astype(str)

        fig_area = go.Figure()
        fig_area.add_trace(go.Scatter(
            x=df_time['__ym__'], y=df_time[sel_m1],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#6366f1', width=2.5, shape='spline'),
            fillcolor='rgba(99,102,241,0.10)',
            marker=dict(size=5, color='#6366f1'),
            hovertemplate='<b>%{x}</b><br>' + sel_m1 + ': %{y:,.2f}<extra></extra>'
        ))
        fig_area.update_layout(xaxis_title='Período', yaxis_title=sel_m1,
                               showlegend=False)
        apply_common_layout(fig_area)
        st.plotly_chart(fig_area, use_container_width=True)
    else:
        top_n2 = min(12, df_f[sel_c2].nunique())
        st.markdown(f"""
        <div class="section-header">
            <span class="section-title">{sel_m1} por {sel_c2}</span>
            <span class="section-badge">Top {top_n2}</span>
        </div>""", unsafe_allow_html=True)

        if not df_f.empty:
            df_c2 = (df_f.groupby(sel_c2)[sel_m1].sum()
                     .reset_index()
                     .sort_values(sel_m1, ascending=False)
                     .head(top_n2))
            fig_c2 = px.bar(df_c2, x=sel_c2, y=sel_m1,
                            color=sel_m1, color_continuous_scale=PALETTE_GRAD,
                            text=df_c2[sel_m1].apply(fmt_number))
            fig_c2.update_traces(textposition='outside',
                                 hovertemplate=f"<b>%{{x}}</b><br>{sel_m1}: %{{y:,.2f}}<extra></extra>")
            fig_c2.update_layout(coloraxis_showscale=False, xaxis_title=sel_c2, yaxis_title=sel_m1)
            apply_common_layout(fig_c2)
            st.plotly_chart(fig_c2, use_container_width=True)
        else:
            st.info("No hay datos para mostrar.")

# --- Explicaciones Gráficas 1 y 2 ---
if not df_f.empty:
    _ex1, _ex2 = st.columns([1.1, 0.9])
    with _ex1:
        _lider1     = df_f.groupby(sel_c1)[sel_m1].sum().idxmax()
        _lider1_val = df_f.groupby(sel_c1)[sel_m1].sum().max()
        _lider1_pct = _lider1_val / df_f[sel_m1].sum() * 100 if df_f[sel_m1].sum() > 0 else 0
        _n_seg      = df_f[sel_c1].nunique()
        with st.expander("📖 Análisis e interpretación — Gráfica 1", expanded=False):
            st.markdown(f"""
            **¿Qué se analiza?**
            Muestra el ranking de los **Top {top_n} segmentos de {sel_c1}** ordenados
            de mayor a menor **{sel_m1}** acumulado. El color más oscuro indica mayor
            valor. Permite identificar qué segmentos generan más volumen y su peso
            relativo sobre el total.

            **¿A qué conclusión se llega?**
            - **{_lider1}** es el segmento líder, concentrando el **{_lider1_pct:.1f}%**
              del total de {sel_m1} ({fmt_number(_lider1_val)}).
            - Se analizan **{_n_seg}** segmentos únicos en total.
            - {"⚠️ Alta concentración: un solo segmento supera el 50% del total, lo que implica alta dependencia." if _lider1_pct > 50 else "✅ La distribución es relativamente equilibrada entre los segmentos analizados."}
            """)
    with _ex2:
        if tiene_fecha and '__ym__' in df_f.columns:
            _dt2    = df_f.groupby('__ym__')[sel_m1].sum()
            _mx_lbl = str(_dt2.idxmax())
            _mn_lbl = str(_dt2.idxmin())
            _mx_val = _dt2.max()
            _mn_val = _dt2.min()
            _varpct = (_mx_val - _mn_val) / _mn_val * 100 if _mn_val > 0 else 0
            with st.expander("📖 Análisis e interpretación — Gráfica 2", expanded=False):
                st.markdown(f"""
                **¿Qué se analiza?**
                La línea de área muestra la **evolución mes a mes** de **{sel_m1}** a lo
                largo del tiempo. Detecta estacionalidad, picos de demanda, caídas abruptas
                o tendencias sostenidas de crecimiento o decrecimiento.

                **¿A qué conclusión se llega?**
                - El **mejor período** fue **{_mx_lbl}** con {fmt_number(_mx_val)}.
                - El **peor período** fue **{_mn_lbl}** con {fmt_number(_mn_val)}.
                - La variación pico–valle es del **{abs(_varpct):.1f}%**
                  ({fmt_number(abs(_mx_val - _mn_val))}),
                  {"indicando **alta estacionalidad** o eventos puntuales de gran impacto." if abs(_varpct) > 50 else "indicando una evolución relativamente estable con variaciones moderadas."}
                """)
        else:
            _dc2    = df_f.groupby(sel_c2)[sel_m1].sum()
            _l2     = _dc2.idxmax()
            _l2_val = _dc2.max()
            _l2_pct = _l2_val / _dc2.sum() * 100 if _dc2.sum() > 0 else 0
            with st.expander("📖 Análisis e interpretación — Gráfica 2", expanded=False):
                st.markdown(f"""
                **¿Qué se analiza?**
                Barras verticales que comparan **{sel_m1}** entre los **Top {top_n2}
                segmentos de {sel_c2}**. Complementa la Gráfica 1 mostrando la segunda
                dimensión categórica del dataset.

                **¿A qué conclusión se llega?**
                - **{_l2}** lidera en {sel_c2} con {fmt_number(_l2_val)}
                  ({_l2_pct:.1f}% del total).
                - La distribución entre subcategorías
                  {"es **concentrada**: pocos grupos dominan el resultado." if _l2_pct > 40 else "es **equilibrada** entre las subcategorías analizadas."}
                """)

# ==========================================================================
# 9. GRÁFICAS SECUNDARIAS (FILA 2)
# ==========================================================================
g3, g4 = st.columns([0.9, 1.1])

m2_label = sel_m2 if sel_m2 != '__m2__' else sel_m1

# --- Gráfica 3: Donut de participación ---
with g3:
    top_pie = min(8, df_f[sel_c2].nunique())
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">Participación por {sel_c2}</span>
        <span class="section-badge">{m2_label}</span>
    </div>""", unsafe_allow_html=True)

    if not df_f.empty:
        df_pie = (df_f.groupby(sel_c2)[sel_m2].sum()
                  .abs().reset_index()
                  .sort_values(sel_m2, ascending=False)
                  .head(top_pie))

        fig_pie = go.Figure(go.Pie(
            labels=df_pie[sel_c2],
            values=df_pie[sel_m2],
            hole=0.62,
            marker=dict(colors=PALETTE_MULTI, line=dict(color='white', width=2)),
            textinfo='label+percent',
            textfont=dict(size=11),
            hovertemplate='<b>%{label}</b><br>Valor: %{value:,.2f}<br>Participación: %{percent}<extra></extra>'
        ))
        fig_pie.update_layout(
            showlegend=False,
            annotations=[dict(text=f"<b>{top_pie}</b><br>grupos", x=0.5, y=0.5,
                              font_size=13, font_color='#475569', showarrow=False)]
        )
        apply_common_layout(fig_pie)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")

# --- Gráfica 4: Scatter comparativo ---
with g4:
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">Correlación: {sel_m1} vs {m2_label}</span>
        <span class="section-badge">por {sel_c1}</span>
    </div>""", unsafe_allow_html=True)

    if not df_f.empty:
        df_sc = df_f.copy()
        df_sc['__estado__'] = df_sc[sel_m2].apply(lambda x: 'Positivo' if x >= 0 else 'Negativo')
        hover_extra = [c for c in [sel_c1, sel_c2] if c in df_sc.columns]

        fig_sc = px.scatter(
            df_sc, x=sel_m1, y=sel_m2,
            color='__estado__',
            color_discrete_map={'Positivo': '#10b981', 'Negativo': '#ef4444'},
            symbol=sel_c1 if df_sc[sel_c1].nunique() <= 6 else None,
            opacity=0.72,
            hover_data=hover_extra,
            trendline=None,
            labels={sel_m1: sel_m1, sel_m2: m2_label, '__estado__': 'Estado'},
        )
        # Añadir línea de referencia en y=0
        fig_sc.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.5)", line_width=1.5)
        fig_sc.update_traces(marker=dict(size=8, line=dict(width=0.5, color='white')))
        fig_sc.update_layout(
            legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center', title=''),
            xaxis_title=sel_m1, yaxis_title=m2_label
        )
        apply_common_layout(fig_sc)
        st.plotly_chart(fig_sc, use_container_width=True)
    else:
        st.info("No hay datos para mostrar.")

# --- Explicaciones Gráficas 3 y 4 ---
if not df_f.empty:
    _ex3, _ex4 = st.columns([0.9, 1.1])
    with _ex3:
        _pie_ldr     = df_f.groupby(sel_c2)[sel_m2].sum().abs().idxmax()
        _pie_ldr_pct = (df_f.groupby(sel_c2)[sel_m2].sum().abs().max()
                        / df_f.groupby(sel_c2)[sel_m2].sum().abs().sum() * 100)
        with st.expander("📖 Análisis e interpretación — Gráfica 3", expanded=False):
            st.markdown(f"""
            **¿Qué se analiza?**
            El gráfico de dona muestra la **participación porcentual** de cada segmento
            de **{sel_c2}** sobre el total de **{m2_label}**. Cada sector del anillo
            representa cuánto aporta ese grupo al resultado global, facilitando la
            comparación proporcional de un solo vistazo.

            **¿A qué conclusión se llega?**
            - **{_pie_ldr}** es el segmento más pesado con el **{_pie_ldr_pct:.1f}%**
              del total de {m2_label}.
            - {"⚠️ Un solo segmento concentra más del 50% del valor; alta dependencia de ese grupo." if _pie_ldr_pct > 50 else "📊 La distribución es diversificada; ningún segmento domina de forma abrumadora."}
            - Se visualizan los **Top {top_pie} segmentos** más relevantes por volumen.
            """)
    with _ex4:
        _n_pos   = int((df_f[sel_m2] >= 0).sum())
        _n_neg   = int((df_f[sel_m2] < 0).sum())
        _pct_pos = _n_pos / len(df_f) * 100 if len(df_f) > 0 else 0
        _corr    = df_f[[sel_m1, sel_m2]].corr().iloc[0, 1] if len(df_f) > 2 else 0
        if _corr > 0.6:
            _corr_txt = f"correlación **fuerte positiva** ({_corr:.2f}): a mayor {sel_m1}, mayor {m2_label}."
        elif _corr < -0.6:
            _corr_txt = f"correlación **fuerte negativa** ({_corr:.2f}): a mayor {sel_m1}, menor {m2_label}."
        else:
            _corr_txt = f"correlación **débil o moderada** ({_corr:.2f}): ambas métricas no se mueven de forma consistente juntas."
        with st.expander("📖 Análisis e interpretación — Gráfica 4", expanded=False):
            st.markdown(f"""
            **¿Qué se analiza?**
            El diagrama de dispersión enfrenta **{sel_m1}** (eje X) contra **{m2_label}**
            (eje Y) registro a registro. Los puntos **verdes** tienen {m2_label} positivo
            y los **rojos** negativo. La línea punteada en Y=0 separa ganancias de
            pérdidas. Revela la relación o correlación entre las dos métricas.

            **¿A qué conclusión se llega?**
            - **{_n_pos} registros ({_pct_pos:.1f}%)** tienen {m2_label} positivo;
              **{_n_neg}** lo tienen negativo.
            - Existe una {_corr_txt}
            - {"✅ La mayoría de los registros son rentables (sobre la línea Y=0)." if _pct_pos >= 70 else "⚠️ Una proporción significativa de registros muestra pérdidas — conviene revisar los segmentos en rojo."}
            """)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================================
# 10. GRÁFICAS ADICIONALES — ANÁLISIS EN PROFUNDIDAD
# ==========================================================================

# --- Gráfica 5: Comparación anual de métricas (agrupada por año) ---
if tiene_fecha and not df_f.empty and '__year__' in df_f.columns:
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">Evolución Anual Comparada</span>
        <span class="section-badge">{sel_m1} vs {m2_label}</span>
    </div>""", unsafe_allow_html=True)

    df_anual = df_f.groupby('__year__').agg(
        m1=(sel_m1, 'sum'),
        m2=(sel_m2, 'sum'),
        n=(sel_m1, 'count')
    ).reset_index().rename(columns={'__year__': 'Año'})

    fig_anual = go.Figure()
    fig_anual.add_trace(go.Bar(
        x=df_anual['Año'].astype(str), y=df_anual['m1'],
        name=sel_m1, marker_color='#6366f1',
        text=df_anual['m1'].apply(fmt_number), textposition='outside',
        hovertemplate=f'<b>%{{x}}</b><br>{sel_m1}: %{{y:,.2f}}<extra></extra>'
    ))
    fig_anual.add_trace(go.Bar(
        x=df_anual['Año'].astype(str), y=df_anual['m2'],
        name=m2_label, marker_color='#10b981',
        text=df_anual['m2'].apply(fmt_number), textposition='outside',
        hovertemplate=f'<b>%{{x}}</b><br>{m2_label}: %{{y:,.2f}}<extra></extra>'
    ))
    fig_anual.update_layout(
        barmode='group', xaxis_title='Año',
        yaxis_title='Valor acumulado',
        legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center')
    )
    apply_common_layout(fig_anual, height=380)
    st.plotly_chart(fig_anual, use_container_width=True)

    # Análisis dinámico de la gráfica 5
    if len(df_anual) >= 2:
        mejor_anio     = df_anual.loc[df_anual['m1'].idxmax(), 'Año']
        peor_anio      = df_anual.loc[df_anual['m1'].idxmin(), 'Año']
        max_val        = df_anual['m1'].max()
        min_val        = df_anual['m1'].min()
        variacion_tot  = ((max_val - min_val) / abs(min_val) * 100) if min_val != 0 else 0
        ratio_anio     = df_anual.set_index('Año').apply(
            lambda r: (r['m2'] / r['m1'] * 100) if r['m1'] != 0 else 0, axis=1
        )
        mejor_ratio_anio = ratio_anio.idxmax()
        with st.expander("📖 Análisis e interpretación de esta gráfica", expanded=False):
            st.markdown(f"""
            **¿Qué se analiza?**
            Este gráfico de barras agrupadas compara año a año el comportamiento de
            **{sel_m1}** (métrica principal) frente a **{m2_label}** (métrica secundaria).
            Permite identificar si ambas variables crecen de forma paralela o si existe una
            brecha que se amplía o reduce con el tiempo.

            **¿A qué conclusión se llega?**
            - El año con mayor **{sel_m1}** acumulado fue **{mejor_anio}**
              ({fmt_number(max_val)}), mientras que el menor fue **{peor_anio}**
              ({fmt_number(min_val)}), una diferencia del **{abs(variacion_tot):.1f}%**.
            - El año **{mejor_ratio_anio}** mostró la mejor relación
              **{m2_label} / {sel_m1}** ({ratio_anio[mejor_ratio_anio]:.1f}%),
              lo que indica mayor eficiencia o rentabilidad relativa en ese período.
            - {"📈 La tendencia general es **creciente**, lo que sugiere expansión del negocio." if df_anual['m1'].is_monotonic_increasing else "📉 La tendencia **no es consistentemente creciente**, lo que indica volatilidad interanual que merece atención."}
            """)
    st.markdown("<br>", unsafe_allow_html=True)

# --- Gráfica 6: Top 5 Mejores y Peores por Dimensión Principal ---
if not df_f.empty and df_f[sel_c1].nunique() >= 4:
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">Mejores y Peores por {sel_c1}</span>
        <span class="section-badge">Top 5 · Bottom 5</span>
    </div>""", unsafe_allow_html=True)

    df_rank = df_f.groupby(sel_c1)[sel_m2].sum().reset_index().sort_values(sel_m2)
    n_rank  = min(5, len(df_rank) // 2)
    bottom5 = df_rank.head(n_rank).copy()
    top5    = df_rank.tail(n_rank).copy()
    df_tb   = pd.concat([bottom5, top5])
    df_tb['color'] = df_tb[sel_m2].apply(lambda v: '#10b981' if v >= 0 else '#ef4444')
    df_tb['label'] = df_tb[sel_m2].apply(fmt_number)

    fig_rank = go.Figure(go.Bar(
        x=df_tb[sel_m2],
        y=df_tb[sel_c1],
        orientation='h',
        marker_color=df_tb['color'],
        text=df_tb['label'],
        textposition='outside',
        hovertemplate=f'<b>%{{y}}</b><br>{m2_label}: %{{x:,.2f}}<extra></extra>'
    ))
    fig_rank.add_vline(x=0, line_color='rgba(100,116,139,0.4)', line_width=1.5)
    fig_rank.update_layout(xaxis_title=m2_label, yaxis_title='')
    apply_common_layout(fig_rank, height=max(320, n_rank * 80))
    st.plotly_chart(fig_rank, use_container_width=True)

    # Análisis dinámico de la gráfica 6
    top_cat    = top5.iloc[-1][sel_c1]
    top_val    = top5.iloc[-1][sel_m2]
    bottom_cat = bottom5.iloc[0][sel_c1]
    bottom_val = bottom5.iloc[0][sel_m2]
    n_neg      = (df_rank[sel_m2] < 0).sum()
    with st.expander("📖 Análisis e interpretación de esta gráfica", expanded=False):
        st.markdown(f"""
        **¿Qué se analiza?**
        Este gráfico de barras horizontales enfrenta los **{n_rank} segmentos con mayor
        {m2_label}** (verde) contra los **{n_rank} con menor {m2_label}** (rojo/verde según valor).
        Identifica rápidamente los extremos del espectro de desempeño en la dimensión
        **{sel_c1}**.

        **¿A qué conclusión se llega?**
        - **Mejor desempeño:** **{top_cat}** lidera con {fmt_number(top_val)} en {m2_label}.
        - **Peor desempeño:** **{bottom_cat}** tiene el resultado más bajo
          ({fmt_number(bottom_val)}).
        - {"⚠️ Hay **" + str(n_neg) + " segmento(s) con valor negativo** en " + m2_label + ", lo que requiere revisión de su estructura de costos o estrategia." if n_neg > 0 else "✅ Todos los segmentos muestran **valores positivos** en " + m2_label + ", indicando un desempeño general saludable."}
        - La brecha entre el mejor y peor es de **{fmt_number(abs(top_val - bottom_val))}**,
          {'una diferencia significativa que sugiere alta heterogeneidad entre segmentos.' if abs(top_val - bottom_val) > abs(top_val) * 0.5 else 'una diferencia moderada que indica cierta homogeneidad entre segmentos.'}
        """)
    st.markdown("<br>", unsafe_allow_html=True)

# --- Gráfica 7: Curva de Pareto (concentración acumulada) ---
if not df_f.empty and df_f[sel_c1].nunique() >= 3:
    st.markdown(f"""
    <div class="section-header">
        <span class="section-title">Concentración Acumulada (Pareto)</span>
        <span class="section-badge">{sel_m1} por {sel_c1}</span>
    </div>""", unsafe_allow_html=True)

    df_pareto = (
        df_f.groupby(sel_c1)[sel_m1].sum()
        .reset_index()
        .sort_values(sel_m1, ascending=False)
    )
    df_pareto['pct_indiv']  = df_pareto[sel_m1] / df_pareto[sel_m1].sum() * 100
    df_pareto['pct_acum']   = df_pareto['pct_indiv'].cumsum()
    df_pareto['rank']        = range(1, len(df_pareto) + 1)

    # Cuántos segmentos acumulan el 80%
    n_80 = int((df_pareto['pct_acum'] <= 80).sum()) + 1
    pct_entidades_80 = round(n_80 / len(df_pareto) * 100, 1)

    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Bar(
        x=df_pareto[sel_c1], y=df_pareto['pct_indiv'],
        name='% Individual',
        marker_color='#818cf8',
        hovertemplate='<b>%{x}</b><br>Participación: %{y:.1f}%<extra></extra>'
    ))
    fig_pareto.add_trace(go.Scatter(
        x=df_pareto[sel_c1], y=df_pareto['pct_acum'],
        name='% Acumulado',
        mode='lines+markers',
        yaxis='y2',
        line=dict(color='#f59e0b', width=2.5),
        marker=dict(size=6, color='#f59e0b'),
        hovertemplate='<b>%{x}</b><br>Acumulado: %{y:.1f}%<extra></extra>'
    ))
    fig_pareto.add_hline(
        y=80, line_dash='dash', line_color='rgba(239,68,68,0.6)',
        line_width=1.5, annotation_text='80%', annotation_position='right',
        yref='y2'
    )
    fig_pareto.update_layout(
        yaxis=dict(title='% Individual', ticksuffix='%'),
        yaxis2=dict(title='% Acumulado', ticksuffix='%',
                    overlaying='y', side='right', range=[0, 105]),
        legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center'),
        xaxis_title=sel_c1
    )
    apply_common_layout(fig_pareto, height=400)
    st.plotly_chart(fig_pareto, use_container_width=True)

    # Análisis dinámico de la gráfica 7
    lider_pareto     = df_pareto.iloc[0][sel_c1]
    lider_pareto_pct = df_pareto.iloc[0]['pct_indiv']
    with st.expander("📖 Análisis e interpretación de esta gráfica", expanded=False):
        st.markdown(f"""
        **¿Qué se analiza?**
        La curva de Pareto muestra qué proporción de los segmentos de **{sel_c1}**
        concentra el 80% del total de **{sel_m1}**. Las barras representan la
        participación individual de cada segmento y la línea naranja el porcentaje
        acumulado. La línea roja punteada marca el umbral del **80%**.

        **¿A qué conclusión se llega?**
        - **{lider_pareto}** es el segmento dominante con el **{lider_pareto_pct:.1f}%**
          del total de {sel_m1}.
        - Solo **{n_80} de {len(df_pareto)} segmentos** ({pct_entidades_80}% del total)
          concentran el **80%** del {sel_m1} — {"confirmando el principio de Pareto (pocos vitales, muchos triviales)." if pct_entidades_80 <= 25 else "indicando una distribución **más equitativa** de lo habitual entre los segmentos."}
        - {"⚠️ Alta concentración: el negocio depende fuertemente de pocos segmentos, lo que representa un riesgo de diversificación." if pct_entidades_80 <= 20 else "📊 La distribución es relativamente equilibrada, lo que reduce la dependencia de un único segmento."}
        """)
    st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================================
# 11. INSIGHTS AUTOMÁTICOS
# ==========================================================================
st.markdown("""
<div class="section-header">
    <span class="section-title">Hallazgos Clave del Análisis</span>
    <span class="section-badge">Auto-generado</span>
</div>""", unsafe_allow_html=True)

if not df_f.empty and len(df_f) >= 2:
    # Calcular métricas de insights
    by_c1 = df_f.groupby(sel_c1)[sel_m1].sum()
    by_c2 = df_f.groupby(sel_c2)[sel_m2].sum()

    leader_c1     = by_c1.idxmax()
    leader_c1_val = by_c1.max()
    leader_c1_pct = (leader_c1_val / total_m1 * 100) if total_m1 > 0 else 0

    leader_c2     = by_c2.idxmax()
    leader_c2_val = by_c2.max()

    laggard_c2     = by_c2.idxmin()
    laggard_c2_val = by_c2.min()

    # Concentración: top-1 > 50%?
    concentration_alert = leader_c1_pct > 50

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.info(
            f"**Líder en {sel_c1}**\n\n"
            f"**{leader_c1}** concentra el **{leader_c1_pct:.1f}%** de {sel_m1} "
            f"({fmt_number(leader_c1_val)})."
            + (f"\n\n⚠️ Alta concentración: más del 50% en un solo segmento." if concentration_alert else "")
        )

    with col_b:
        if ratio_m2_m1 >= 20:
            st.success(
                f"**Margen Destacado**\n\n"
                f"La relación {m2_label} / {sel_m1} es del **{ratio_m2_m1:.1f}%**, "
                f"indicando una excelente eficiencia operativa con {fmt_number(total_m2)} acumulados."
            )
        elif ratio_m2_m1 >= 0:
            st.warning(
                f"**Margen Moderado**\n\n"
                f"Relación {m2_label} / {sel_m1}: **{ratio_m2_m1:.1f}%** "
                f"({fmt_number(total_m2)}). Existe margen de mejora en eficiencia."
            )
        else:
            st.error(
                f"**Alerta de Déficit**\n\n"
                f"La métrica {m2_label} es negativa ({fmt_number(total_m2)}), "
                f"representando un **{abs(ratio_m2_m1):.1f}%** de pérdida respecto a {sel_m1}."
            )

    with col_c:
        if laggard_c2_val < 0:
            st.error(
                f"**Segmento con Mayor Pérdida**\n\n"
                f"**{laggard_c2}** presenta el saldo más negativo en {m2_label}: "
                f"{fmt_number(laggard_c2_val)}. Se recomienda revisar su estructura de costos."
            )
        else:
            st.success(
                f"**Mayor Aportador en {sel_c2}**\n\n"
                f"**{leader_c2}** lidera con {fmt_number(leader_c2_val)} en {m2_label}. "
                f"Todos los segmentos muestran resultados positivos en este período."
            )
else:
    st.info("Carga un dataset con al menos 2 registros para generar insights automáticos.")

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================================
# 11. TABLA DE DATOS DETALLADA
# ==========================================================================
st.markdown("""
<div class="section-header">
    <span class="section-title">Explorador de Datos</span>
    <span class="section-badge">Búsqueda y Exportación</span>
</div>""", unsafe_allow_html=True)
st.caption("Busca, ordena y descarga los datos filtrados del período seleccionado.")

if not df_f.empty:
    col_srch, col_exp = st.columns([3, 1])
    with col_srch:
        query = st.text_input("", placeholder="Buscar en todos los campos...",
                              label_visibility="collapsed")
    with col_exp:
        # Preparar datos para exportar
        cols_mapped = [c for c in [sel_fecha, sel_c1, sel_c2, sel_m1,
                                   (sel_m2 if sel_m2 != '__m2__' else None)]
                       if c and c != "(Ninguna)" and c in df_f.columns]
        other_cols = [c for c in df_f.columns
                      if c not in cols_mapped
                      and not c.startswith('__')
                      and c not in ['dateObj', 'year', 'monthNum', 'monthName', 'dateStr']]
        show_cols = cols_mapped + other_cols[:max(0, 12 - len(cols_mapped))]
        df_show = df_f[show_cols].copy()

        csv_bytes = df_show.to_csv(index=False).encode('utf-8-sig')
        st.download_button("Exportar CSV", data=csv_bytes,
                           file_name="datos_exportados.csv", mime="text/csv",
                           use_container_width=True)

    # Aplicar búsqueda
    df_table = df_show.copy()
    if query:
        q = query.lower()
        mask = pd.Series(False, index=df_table.index)
        for col in df_table.columns:
            mask |= df_table[col].astype(str).str.lower().str.contains(q, na=False)
        df_table = df_table[mask]
        st.caption(f"Mostrando {len(df_table):,} resultado(s) para **'{query}'**")

    # Configuración de formato
    col_cfg = {}
    for col in df_table.columns:
        if col in [sel_m1, sel_m2]:
            col_cfg[col] = st.column_config.NumberColumn(format="$%.2f")
        elif col == sel_m2 and sel_m2 == '__m2__':
            pass

    st.dataframe(df_table, use_container_width=True, hide_index=True,
                 column_config=col_cfg, height=400)
else:
    st.info("No hay registros que coincidan con los filtros aplicados.")
