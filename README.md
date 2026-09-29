# Dashboard Financiero — Superintendencia de Sociedades

**Proyecto de Grado** · Especialización en Analítica de Datos  
Análisis Comparativo del Estado de Resultado Integral · Metodología CRISP-DM

---

## Descripción

Dashboard interactivo que facilita el análisis comparativo del **Estado de Resultado Integral** de las empresas reportantes a la Superintendencia de Sociedades de Colombia durante el período 2023–2025.

Resuelve la necesidad de los analistas financieros, de riesgo y de supervisión de contar con una herramienta ágil para comparar el desempeño financiero entre empresas de un mismo sector y periodo, sin cruces manuales.

> **Aviso:** Este tablero es de uso académico. No constituye un aval de la Superintendencia de Sociedades ni una calificación de riesgo crediticio.

---

## Ejecución local

### Requisitos
- Python 3.9 o superior
- Las dependencias listadas en `requirements.txt`

### Instalación y arranque

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd <carpeta-del-proyecto>

# 2. Crear y activar entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/macOS

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar el dashboard
streamlit run dashboard_app.py
```

O simplemente ejecutar `run.bat` en Windows.

### Datos

El archivo de datos debe ubicarse en:
```
data/310030_Estado de resultado integral, resultado del periodo, por funcion de gasto.xlsx
```

Obtenible del portal **SIIS** de la Superintendencia de Sociedades de Colombia.  
Para apuntar a un archivo diferente, modifica únicamente la constante `DATA_FILE` al inicio de `dashboard_app.py`.

---

## Estructura del proyecto

```
├── dashboard_app.py       ← Archivo principal (streamlit run dashboard_app.py)
├── requirements.txt       ← Dependencias Python
├── run.bat                ← Acceso directo para Windows
├── .streamlit/
│   └── config.toml        ← Configuración de tema Streamlit
├── data/
│   └── 310030_Estado de resultado integral...xlsx   ← Datos fuente
└── README.md
```

---

## Funcionalidades

- **Filtros**: Sector CIIU, departamento, ciudad, tipo societario, rango de ingresos y periodo
- **KPIs**: Ingresos totales, ganancia neta, margen ponderado, margen mediana
- **Análisis por sector**: Top sectores por ingresos, ganancia y margen
- **Análisis por empresa**: Top empresas con ranking y tabla detallada
- **Comparación temporal**: Periodo Actual vs Anterior con variaciones porcentuales
- **Análisis geográfico**: Ingresos y ganancia por departamento y ciudad
- **Calidad de datos**: Cobertura temporal, NITs duplicados, outliers de margen, nulos y validaciones contables

---

## Despliegue en Streamlit Community Cloud

1. Sube el repositorio a GitHub (incluye la carpeta `data/` con el archivo Excel)
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu cuenta de GitHub y selecciona el repositorio
4. Configura:
   - **Main file path**: `dashboard_app.py`
   - **Python version**: 3.11 (recomendado)
5. Haz clic en **Deploy**

---

## Fuente de datos

**Sistema Integrado de Información Societaria (SIIS)**  
Superintendencia de Sociedades · Colombia  
Formulario 310030 — Estado de Resultado Integral por Función de Gasto  
Taxonomía XBRL — NIIF plenas

---

## Limitaciones conocidas del dataset

- El archivo de trabajo es una copia de prueba, no la descarga directa del portal oficial
- La cobertura actual es de un único año (cortes: 2025-03-31, 2025-04-30, 2025-06-30, 2025-10-31, 2025-12-31)
- Existen valores nulos en Ingresos y Costo de Ventas
- Puede haber más de una Fecha de Corte por NIT; se conserva la más reciente por NIT+Periodo
