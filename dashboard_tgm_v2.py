"""
Dashboard TGM (Transvisa E.I.R.L.) - Baja eficacia del cumplimiento de mantenimiento preventivo
Versión 2: panel lateral de navegación + filtros dinámicos (meses y As-Is / To-Be) interconectados.
Ejecutar con:  streamlit run dashboard_tgm_v2.py
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="TGM | Mantenimiento preventivo", page_icon="🚛", layout="wide")

# ======================= DATOS (del Excel del equipo) =======================
SEMANAL = [['S01-02', 15, 10, 14747.8, 19894.03], ['S03-04', 8, 5, 3347.84, 8468.14], ['S04-05', 11, 6, 10635.51, 4471.74], ['S06-07', 11, 7, 18621.93, 1407.28], ['S08-09', 12, 8, 5261.22, 18017.83], ['S10-11', 14, 9, 11229.77, 29989.02], ['S12-13', 14, 10, 13467.64, 17211.7], ['S14-15', 8, 8, 18270.01, 3658.39], ['S16-17', 2, 2, 5066.83, 192.66], ['S18-19', 5, 4, 3133.43, 5416.55], ['S20-21', 7, 4, 8958.43, 2817.64], ['S22-23', 7, 4, 695.32, 134.08], ['S24-25', 4, 1, 1888.82, 560.2], ['S26-27', 18, 12, 12858.83, 7151.18], ['S28-29', 17, 12, 14418.1, 9635.9], ['S30-31', 15, 11, 7220.69, 8395.15], ['S32-33', 10, 8, 4846.09, 56401.09], ['S34-35', 7, 7, 4219.55, 2183.42], ['S36-37', 5, 3, 18895.25, 6572.13], ['S38-39', 14, 10, 21726.35, 4019.43], ['S40-41', 11, 11, 19618.58, 10931.71], ['S42-43', 7, 4, 20759.2, 1042.59], ['S44-45', 10, 8, 5648.05, 7963.19], ['S46-47', 10, 8, 11969.78, 2604.7], ['S48-49', 9, 9, 15490.3, 5380.88], ['S50-51', 11, 9, 0.0, 0.0]]
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
ABREV = [m[:3].upper() for m in MESES]
ASIS_MENSUAL = {
    'capacitacion': [66.7, 58.3, 75.0, 50.0, 41.7, 66.7, 75.0, 58.3, 58.3, 50.0, 75.0, 66.7],
    'tiempo_muerto': [11.67, 15.0, 10.83, 3.33, 5.83, 7.0, 2.0, 8.33, 3.67, 8.67, 2.08, 1.33],
    'disponibilidad': [88.9, 83.7, 92.3, 78.3, 87.0, 82.4, 78.4, 74.2, 89.4, 86.3, 85.1, 93.3],
    'reprocesos': [22.2, 33.3, 10.0, 14.3, 12.5, 22.2, 28.6, 40.0, 10.0, 25.0, 11.1, 9.1],
    'setup': [520.0, 580.0, 470.0, 180.0, 310.0, 390.0, 100.0, 450.0, 200.0, 470.0, 110.0, 80.0],
}
# Capacitación: To-Be mensual tomado de tu Power BI (simulación ADDIE) y asistentes por mes
CAP_TOBE = [92.8, 91.1, 94.6, 89.3, 87.5, 92.8, 94.6, 91.1, 91.1, 89.3, 94.6, 92.8]
CAP_ASIST_ASIS = [8, 7, 9, 6, 5, 8, 9, 7, 7, 6, 9, 8]
CAP_ASIST_TOBE = [11.1, 10.9, 11.4, 10.7, 10.5, 11.1, 11.4, 10.9, 10.9, 10.7, 11.4, 11.1]
TOTAL_COLAB = 12

META_OT = 90.0
FACTURACION_ANUAL = 2_585_000

ROJO, VERDE, AZUL, ROSA, MORADO, NARANJA, CIAN, AMBAR, NAVY = (
    "#FF3D5A", "#00D68F", "#2F80FF", "#FF2D87", "#7C3AED", "#FF7A00", "#00B8D9", "#FFC400", "#16163A")

MOTIVOS = [
    dict(id="C1", icono="🎓", color=MORADO, nombre="Capacitación", col="capacitacion",
         ind="% de asistencia a capacitaciones", unidad="%", as_is=61.8, to_be=91.8, estandar=90.0, mejor="mayor",
         metodo="ADDIE", metodo_det="ADDIE (Análisis, Diseño, Desarrollo, Implementación, Evaluación) · Luo et al. (2024)",
         formula="C(asist) = (N° de colaboradores que asistieron / Total de colaboradores del área) × 100",
         causa="Ausencia de un programa de capacitación continua en mantenimiento preventivo y autónomo."),
    dict(id="C2", icono="⏱️", color=NARANJA, nombre="Tiempos muertos", col="tiempo_muerto",
         ind="Tiempo muerto mensual", unidad="horas", as_is=6.65, to_be=3.18, estandar=3.42, mejor="menor",
         metodo="Intelligent Scheduling Optimization System",
         metodo_det="Intelligent Scheduling Optimization System (programación inteligente de recursos)",
         formula="Horas muertas por mes = Σ horas sin actividad productiva durante el servicio",
         causa="Ausencia de un procedimiento para asegurar oportunamente los recursos requeridos para el mantenimiento."),
    dict(id="C3", icono="🛠️", color=CIAN, nombre="Disponibilidad", col="disponibilidad",
         ind="Disponibilidad de equipos", unidad="%", as_is=84.9, to_be=95.3, estandar=95.0, mejor="mayor",
         metodo="TPM", metodo_det="TPM (Mantenimiento Productivo Total)",
         formula="Disponibilidad = MTBF / (MTBF + MTTR) × 100",
         causa="Averías recurrentes por mantenimiento correctivo no programado que reducen las ventanas de tiempo para el preventivo."),
    dict(id="C4", icono="🔁", color=ROSA, nombre="Reprocesos", col="reprocesos",
         ind="% de equipos con segundo mantenimiento", unidad="%", as_is=19.9, to_be=3.4, estandar=5.0, mejor="menor",
         metodo="DMAIC", metodo_det="DMAIC (Definir, Medir, Analizar, Mejorar, Controlar) · Six Sigma",
         formula="Reprocesos = (N° equipos con segundo mantenimiento / Total de equipos atendidos) × 100",
         causa="Ausencia de un protocolo de verificación de conformidad al finalizar el mantenimiento preventivo."),
    dict(id="C5", icono="⚙️", color=AMBAR, nombre="Setup", col="setup",
         ind="Tiempo de setup mensual", unidad="minutos", as_is=321.7, to_be=166.1, estandar=140.4, mejor="menor",
         metodo="SMED", metodo_det="SMED (Cambio rápido de herramientas / preparación)",
         formula="Setup mensual = Σ minutos de preparación previa al servicio de mantenimiento",
         causa="Ausencia de un procedimiento estandarizado para la preparación previa del servicio de mantenimiento."),
]

# ---------- DataFrames ----------
semanal = pd.DataFrame(SEMANAL, columns=["semana", "programados", "ejecutados", "costo_tracto", "costo_tolva"])
semanal["cumplimiento"] = semanal["ejecutados"] / semanal["programados"] * 100
semanal["costo_total"] = semanal["costo_tracto"] + semanal["costo_tolva"]


def serie_tobe(m):
    """To-Be mensual: C1 usa tus valores del Power BI; el resto es una simulación coherente
    (misma forma del As-Is, promedio igual al To-Be del Excel)."""
    if m["col"] == "capacitacion":
        return CAP_TOBE
    base = ASIS_MENSUAL[m["col"]]
    prom = sum(base) / len(base)
    if m["mejor"] == "mayor":
        return [round(min(100, m["to_be"] + (v - prom) * 0.35), 1) for v in base]
    return [round(v * m["to_be"] / prom, 2) for v in base]


mensual = pd.DataFrame({"mes": MESES, "abrev": ABREV})
for m in MOTIVOS:
    mensual[m["col"] + "_asis"] = ASIS_MENSUAL[m["col"]]
    mensual[m["col"] + "_tobe"] = serie_tobe(m)

resumen = pd.DataFrame(MOTIVOS)


def mejora(as_is, to_be, mejor):
    return (to_be - as_is) / as_is * 100 if mejor == "mayor" else (as_is - to_be) / as_is * 100


def cumple(valor, est, mejor):
    return valor >= est if mejor == "mayor" else valor <= est


# ======================= ESTILOS =======================
st.markdown(f"""
<style>
.stApp {{ background: linear-gradient(135deg,#F4F7FF 0%,#FFF4FA 50%,#F0FFF9 100%); }}
section[data-testid="stSidebar"] > div {{ background: linear-gradient(180deg,#0A2A7A 0%,#1456D6 55%,#2F9BFF 100%); }}
section[data-testid="stSidebar"] * {{ color: #FFFFFF; }}
section[data-testid="stSidebar"] .stButton > button {{
    width:100%; text-align:left; border-radius:12px; border:1px solid rgba(255,255,255,.25);
    background: rgba(255,255,255,.08); font-weight:700; padding:.55rem .8rem; transition:all .2s; }}
section[data-testid="stSidebar"] .stButton > button:hover {{ background: rgba(255,255,255,.25); transform: translateX(4px); }}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
    background: linear-gradient(90deg,#E5173F,#FF3D5A); color:#FFFFFF !important; border:none; }}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] p {{ color:#FFFFFF !important; }}
.banner {{ border-radius:18px; padding:18px 26px; color:#fff; box-shadow:0 8px 22px rgba(0,0,0,.18); margin-bottom:14px; }}
.banner h1 {{ margin:0; font-size:1.9rem; color:#fff; }}
.banner p {{ margin:4px 0 0 0; opacity:.95; font-size:.95rem; }}
.chip {{ display:inline-block; padding:5px 12px; border-radius:999px; background:rgba(255,255,255,.22);
        font-size:.82rem; font-weight:700; margin:8px 8px 0 0; border:1px solid rgba(255,255,255,.4); }}
.kpi {{ border-radius:16px; padding:14px 16px; color:#fff; box-shadow:0 6px 16px rgba(0,0,0,.15); min-height:120px; }}
.kpi .t {{ font-size:.72rem; font-weight:800; letter-spacing:.6px; text-transform:uppercase; opacity:.92; }}
.kpi .s {{ font-size:.78rem; opacity:.9; }}
.kpi .v {{ font-size:2.1rem; font-weight:900; line-height:1.15; margin:4px 0; }}
.panel {{ background:#fff; border-radius:16px; padding:6px 10px; box-shadow:0 4px 14px rgba(0,0,0,.08); }}
.empresa {{ text-align:center; padding:6px 0 2px 0; }}
.empresa h2 {{ margin:0; font-size:1.55rem; letter-spacing:1px; color:#fff; }}
.servicio {{ background:rgba(255,255,255,.12); border-left:5px solid {AMBAR}; border-radius:10px;
             padding:7px 10px; margin:6px 0; font-size:.88rem; font-weight:600; }}
.seccion {{ font-size:.78rem; font-weight:800; letter-spacing:1.5px; margin:14px 0 4px 0; color:{AMBAR}; }}
</style>
""", unsafe_allow_html=True)


def kpi(titulo, valor, sub, color, color2=None):
    color2 = color2 or color
    st.markdown(f"""<div class="kpi" style="background:linear-gradient(135deg,{color},{color2});">
        <div class="t">{titulo}</div><div class="v">{valor}</div><div class="s">{sub}</div></div>""",
                unsafe_allow_html=True)


def banner(titulo, sub, color, color2, chips=()):
    ch = "".join(f'<span class="chip">{c}</span>' for c in chips)
    st.markdown(f"""<div class="banner" style="background:linear-gradient(110deg,{color},{color2});">
        <h1>{titulo}</h1><p>{sub}</p>{ch}</div>""", unsafe_allow_html=True)


LOGO_B64 = "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"

# ======================= ESTADO (interconexión) =======================
if "pagina" not in st.session_state:
    st.session_state.pagina = "resumen"
if "meses_sel" not in st.session_state:
    st.session_state.meses_sel = []     # vacío = todos los meses
if "escenario" not in st.session_state:
    st.session_state.escenario = "Ambos"


def ir(p):
    st.session_state.pagina = p


# ======================= PANEL IZQUIERDO =======================
with st.sidebar:
    st.markdown(f"""<div class="empresa"><div style="background:#FFFFFF;border-radius:16px;padding:10px 14px;margin:4px 0 10px 0;box-shadow:0 4px 12px rgba(0,0,0,.25)"><img src="data:image/png;base64,{LOGO_B64}" style="width:100%;max-width:190px"></div>
        <h2>TRANSVISA E.I.R.L.</h2><div style="font-size:.8rem;opacity:.85">TGM · Año 2025</div></div>""",
                unsafe_allow_html=True)
    st.markdown('<div class="seccion">SERVICIOS</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="servicio">🚚 Transporte de carga pesada</div>
    <div class="servicio" style="border-left-color:#00D68F">🛢️ Fabricación de cisternas</div>
    <div class="servicio" style="border-left-color:#FF2D87">🔧 Mantenimiento</div>""", unsafe_allow_html=True)

    st.markdown('<div class="seccion">PANEL</div>', unsafe_allow_html=True)
    st.button("📋  Resumen ejecutivo", on_click=ir, args=("resumen",), key="b_res",
              type="primary" if st.session_state.pagina == "resumen" else "secondary")
    st.button("🚨  Problema general", on_click=ir, args=("general",), key="b_gen",
              type="primary" if st.session_state.pagina == "general" else "secondary")

    st.markdown('<div class="seccion">LAS 5 CAUSAS</div>', unsafe_allow_html=True)
    puntos = {"C1": "🟣", "C2": "🟠", "C3": "🔵", "C4": "🌸", "C5": "🟡"}
    for m in MOTIVOS:
        st.button(f"{puntos[m['id']]} {m['icono']}  {m['id']} · {m['nombre']}", on_click=ir, args=(m["id"],),
                  key="b_" + m["id"], type="primary" if st.session_state.pagina == m["id"] else "secondary")
    st.caption("Fuente: Excel del equipo (hojas Ficha Técnica y Planteamiento)")

pagina = st.session_state.pagina

# ======================= PÁGINA: RESUMEN EJECUTIVO =======================
if pagina == "resumen":
    banner("📋 RESUMEN EJECUTIVO", "Baja eficacia del cumplimiento de mantenimiento preventivo · TGM / Transvisa E.I.R.L.",
           AZUL, MORADO, ["🎯 5 causas raíz", "📈 As-Is vs To-Be", "🧰 5 metodologías"])
    cumpl = semanal["cumplimiento"].mean()
    costo = semanal["costo_total"].sum()
    ok = sum(cumple(m["to_be"], m["estandar"], m["mejor"]) for m in MOTIVOS)

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("✅ Cumplimiento OT (As-Is)", f"{cumpl:.1f}%", f"Meta {META_OT:.0f}% · {cumpl - META_OT:.1f} pp", ROJO, "#FF7A00")
    with c2: kpi("💰 Impacto económico", f"S/ {costo:,.0f}", "Costo tracto + tolva/cisterna", AZUL, CIAN)
    with c3: kpi("📉 % facturación anual", f"{costo / FACTURACION_ANUAL * 100:.1f}%", f"Facturación S/ {FACTURACION_ANUAL:,.0f}", MORADO, ROSA)
    with c4: kpi("🏆 To-Be cumple estándar", f"{ok} de {len(MOTIVOS)}", "Causas que alcanzan su estándar", "#00A878", VERDE)

    st.markdown("### 🎯 Las 5 causas de un vistazo")
    cols = st.columns(5)
    for col, m in zip(cols, MOTIVOS):
        u = "%" if m["unidad"] == "%" else f" {m['unidad'][:3]}."
        mj = mejora(m["as_is"], m["to_be"], m["mejor"])
        c = cumple(m["to_be"], m["estandar"], m["mejor"])
        with col:
            kpi(f"{m['icono']} {m['id']} · {m['nombre']}", f"{m['to_be']:,.1f}{u}",
                f"As-Is {m['as_is']:,.1f}{u} · ▲ {mj:.0f}% · {'✔ cumple' if c else '✖ no cumple'}", m["color"], NAVY)

    resumen["mejora_pct"] = resumen.apply(lambda r: mejora(r.as_is, r.to_be, r.mejor), axis=1)
    resumen["etiqueta"] = resumen["id"] + " · " + resumen["nombre"]
    fig = px.bar(resumen, x="etiqueta", y="mejora_pct", color="etiqueta",
                 color_discrete_sequence=[m["color"] for m in MOTIVOS],
                 text=resumen["mejora_pct"].round(1).astype(str) + "%",
                 title="📈 Mejora esperada por causa (To-Be vs As-Is)", labels={"mejora_pct": "% de mejora", "etiqueta": ""})
    fig.update_traces(textposition="outside")
    fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig)

    tabla = resumen[["id", "nombre", "unidad", "as_is", "to_be", "estandar", "metodo"]].copy()
    tabla["Cumple"] = [("✅ Sí" if cumple(r.to_be, r.estandar, r.mejor) else "❌ No") for r in resumen.itertuples()]
    tabla.columns = ["ID", "Causa", "Unidad", "As-Is", "To-Be", "Estándar", "Metodología", "To-Be cumple estándar"]
    st.dataframe(tabla, hide_index=True)

# ======================= PÁGINA: PROBLEMA GENERAL =======================
elif pagina == "general":
    banner("🚨 PROBLEMA GENERAL", "Baja eficacia del cumplimiento de mantenimiento preventivo", ROJO, NARANJA,
           ["📅 Periodos quincenales 2025", f"🎯 Meta {META_OT:.0f}% de cumplimiento de OT"])
    prog, ejec = semanal["programados"].sum(), semanal["ejecutados"].sum()
    cumpl = semanal["cumplimiento"].mean()
    costo = semanal["costo_total"].sum()
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("✅ Cumplimiento OT", f"{cumpl:.1f}%", f"{cumpl - META_OT:.1f} pp vs meta {META_OT:.0f}%", ROJO, NARANJA)
    with c2: kpi("📝 OT ejecutadas / programadas", f"{ejec} / {prog}", "Total del año", AZUL, CIAN)
    with c3: kpi("💰 Impacto económico", f"S/ {costo:,.0f}", "Tracto + tolva/cisterna", MORADO, ROSA)
    with c4: kpi("📉 % facturación anual", f"{costo / FACTURACION_ANUAL * 100:.1f}%", "Sobre ingresos anuales", "#00A878", VERDE)

    fig = px.line(semanal, x="semana", y="cumplimiento", markers=True,
                  title="📈 % de cumplimiento de órdenes de trabajo por quincena")
    fig.update_traces(line_color=ROSA, line_width=3, marker=dict(size=9, color=AZUL))
    fig.add_hline(y=META_OT, line_dash="dash", line_color=ROJO, annotation_text=f"Meta {META_OT:.0f}%",
                  annotation_position="top left")
    fig.update_layout(yaxis_title="% cumplimiento", xaxis_title="", yaxis_range=[0, 110],
                      plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig)

    costos = semanal.melt(id_vars="semana", value_vars=["costo_tracto", "costo_tolva"], var_name="tipo", value_name="costo")
    costos["tipo"] = costos["tipo"].map({"costo_tracto": "🚛 Tracto", "costo_tolva": "🛢️ Tolva / cisterna"})
    fig2 = px.bar(costos, x="semana", y="costo", color="tipo", title="💸 Costo por periodo (S/)",
                  color_discrete_map={"🚛 Tracto": AZUL, "🛢️ Tolva / cisterna": NARANJA},
                  labels={"costo": "S/", "semana": "", "tipo": ""})
    fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig2)

    with st.expander("📑 Ver datos del cumplimiento semanal"):
        st.dataframe(semanal, hide_index=True)

# ======================= PÁGINAS: CAUSAS C1..C5 =======================
else:
    m = next(x for x in MOTIVOS if x["id"] == pagina)
    color = m["color"]
    u = "%" if m["unidad"] == "%" else f" {m['unidad']}"

    banner(f"{m['icono']} CAUSA {m['id'][1]} · {m['nombre'].upper()}",
           f"Causa raíz: {m['causa']}", color, NAVY,
           [f"📐 Indicador: {m['ind']}", f"🧰 Metodología: {m['metodo']}",
            f"📏 Parámetro (estándar): {m['estandar']:,.1f}{u}"])
    with st.expander("🔎 Fórmula y herramienta / metodología aplicada", expanded=False):
        st.markdown(f"**📐 Indicador:** {m['formula']}")
        st.markdown(f"**🧰 Herramienta / metodología:** {m['metodo_det']}")
        st.markdown(f"**📏 Parámetro (estándar):** {m['estandar']:,.1f}{u} "
                    f"({'mayor es mejor' if m['mejor'] == 'mayor' else 'menor es mejor'})")

    # ---------- Filtros interconectados (botones de mes + As-Is / To-Be) ----------
    f1, f2 = st.columns([4, 1.4])
    with f1:
        st.markdown("**📅 Meses** (sin selección = todo el año)")
        if hasattr(st, "pills"):
            sel = st.pills("Meses", ABREV, selection_mode="multi", key="meses_sel", label_visibility="collapsed")
        else:
            sel = st.multiselect("Meses", ABREV, key="meses_sel", label_visibility="collapsed")
    with f2:
        st.markdown("**🔀 Escenario**")
        st.radio("Escenario", ["Ambos", "As-Is", "To-Be"], key="escenario", horizontal=True,
                 label_visibility="collapsed")
    sel = sel or ABREV
    esc = st.session_state.escenario
    df = mensual[mensual["abrev"].isin(sel)].reset_index(drop=True)
    a_col, t_col = m["col"] + "_asis", m["col"] + "_tobe"

    val_asis, val_tobe = df[a_col].mean(), df[t_col].mean()
    mj = mejora(val_asis, val_tobe, m["mejor"])
    cumple_tobe = cumple(val_tobe, m["estandar"], m["mejor"])
    meses_txt = "Todo el año" if len(sel) == 12 else ", ".join(sel)

    k = st.columns(5)
    with k[0]: kpi("🔴 As-Is · Situación actual", f"{val_asis:,.1f}{u}", f"Promedio · {meses_txt}", ROJO, "#C21F3A")
    with k[1]: kpi("🟢 To-Be · Simulación", f"{val_tobe:,.1f}{u}", f"Aplicando {m['metodo']}", "#00A878", VERDE)
    with k[2]: kpi("🎯 Estándar / Meta", f"{m['estandar']:,.1f}{u}", "Valor de referencia (parámetro)", NAVY, "#3B3B7A")
    with k[3]: kpi("🚀 Mejora esperada", f"{'▲' if mj >= 0 else '▼'} {abs(mj):.1f}%", "Frente al As-Is", AZUL, CIAN)
    with k[4]:
        kpi("🏁 Estado del To-Be", "CUMPLE ✔" if cumple_tobe else "NO CUMPLE ✖", "Comparado con el estándar",
            "#00A878" if cumple_tobe else ROJO, VERDE if cumple_tobe else NARANJA)

    g1, g2 = st.columns([1.6, 1])
    # ---------- Evolución mensual ----------
    with g1:
        fig = go.Figure()
        if esc in ("Ambos", "As-Is"):
            fig.add_trace(go.Scatter(x=df["abrev"], y=df[a_col], mode="lines+markers+text", name="As-Is",
                                     text=[f"{v:,.1f}" for v in df[a_col]], textposition="bottom center",
                                     line=dict(color=ROJO, width=3), marker=dict(size=10)))
        if esc in ("Ambos", "To-Be"):
            fig.add_trace(go.Scatter(x=df["abrev"], y=df[t_col], mode="lines+markers+text", name="To-Be",
                                     text=[f"{v:,.1f}" for v in df[t_col]], textposition="top center",
                                     line=dict(color=VERDE, width=3), marker=dict(size=10)))
        fig.add_hline(y=m["estandar"], line_dash="dot", line_color=NAVY, line_width=2,
                      annotation_text=f"Estándar: {m['estandar']:,.1f}{u}", annotation_position="top right")
        fig.update_layout(title=f"📈 Evolución mensual: {esc} · {m['ind']}", yaxis_title=m["unidad"], xaxis_title="",
                          plot_bgcolor="white", paper_bgcolor="white", height=380,
                          legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig)

    # ---------- Termómetro (gauge) ----------
    with g2:
        val_g = val_asis if esc == "As-Is" else val_tobe
        etiqueta = "As-Is" if esc == "As-Is" else "To-Be"
        max_g = 100 if m["unidad"] == "%" else max(m["as_is"], m["estandar"], max(df[a_col])) * 1.25
        if m["mejor"] == "mayor":
            pasos = [dict(range=[0, m["estandar"]], color="#FFD1D8"), dict(range=[m["estandar"], max_g], color="#C9F7E4")]
        else:
            pasos = [dict(range=[0, m["estandar"]], color="#C9F7E4"), dict(range=[m["estandar"], max_g], color="#FFD1D8")]
        ok_g = cumple(val_g, m["estandar"], m["mejor"])
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=round(val_g, 1), number=dict(suffix="" if m["unidad"] != "%" else "%"),
            title=dict(text=f"🌡️ Termómetro vs estándar · {etiqueta}"),
            gauge=dict(axis=dict(range=[0, max_g]), bar=dict(color=VERDE if ok_g else ROJO), steps=pasos,
                       threshold=dict(line=dict(color=NAVY, width=5), thickness=0.85, value=m["estandar"]))))
        gauge.update_layout(height=380, paper_bgcolor="white", margin=dict(t=70, b=10))
        st.plotly_chart(gauge)

    h1, h2 = st.columns([1.6, 1])
    # ---------- Gráfico inferior ----------
    with h1:
        fig3 = go.Figure()
        if m["col"] == "capacitacion":
            idx = [ABREV.index(a) for a in df["abrev"]]
            if esc in ("Ambos", "As-Is"):
                fig3.add_trace(go.Bar(x=df["abrev"], y=[CAP_ASIST_ASIS[i] for i in idx], name="Asistieron As-Is",
                                      marker_color=ROJO, text=[CAP_ASIST_ASIS[i] for i in idx], textposition="outside"))
            if esc in ("Ambos", "To-Be"):
                fig3.add_trace(go.Bar(x=df["abrev"], y=[CAP_ASIST_TOBE[i] for i in idx], name="Asistieron To-Be",
                                      marker_color=VERDE, text=[CAP_ASIST_TOBE[i] for i in idx], textposition="outside"))
            fig3.add_hline(y=TOTAL_COLAB, line_dash="dot", line_color=NAVY,
                           annotation_text=f"Total colaboradores: {TOTAL_COLAB}", annotation_position="top right")
            fig3.update_layout(title="👥 Colaboradores que asistieron a la capacitación por mes", barmode="group")
        else:
            sig = 1 if m["mejor"] == "mayor" else -1
            if esc in ("Ambos", "As-Is"):
                brecha = [(v - m["estandar"]) * sig for v in df[a_col]]
                fig3.add_trace(go.Bar(x=df["abrev"], y=brecha, name="Brecha As-Is", marker_color=ROJO,
                                      text=[f"{b:+,.1f}" for b in brecha], textposition="outside"))
            if esc in ("Ambos", "To-Be"):
                brecha = [(v - m["estandar"]) * sig for v in df[t_col]]
                fig3.add_trace(go.Bar(x=df["abrev"], y=brecha, name="Brecha To-Be", marker_color=VERDE,
                                      text=[f"{b:+,.1f}" for b in brecha], textposition="outside"))
            fig3.add_hline(y=0, line_color=NAVY)
            fig3.update_layout(title="📊 Brecha vs estándar por mes (positivo = cumple)", barmode="group")
        fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=340, xaxis_title="",
                           legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig3)

    # ---------- Detalle mensual ----------
    with h2:
        st.markdown(f"**📋 Detalle mensual ({m['unidad']})**")
        det = pd.DataFrame({"Mes": df["abrev"], "As-Is": df[a_col].round(1), "To-Be": df[t_col].round(1),
                            "Estándar": m["estandar"]})
        if esc == "As-Is":
            det = det.drop(columns=["To-Be"])
        elif esc == "To-Be":
            det = det.drop(columns=["As-Is"])
        st.dataframe(det, hide_index=True, height=300)
