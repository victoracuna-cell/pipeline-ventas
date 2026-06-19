import streamlit as st
import pandas as pd
import json
import requests
from pathlib import Path

st.set_page_config(
    page_title="Pipeline de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

STAGES = [
    "Asignado",
    "Visitado",
    "Interesado",
    "Esperando Aprobación",
    "Cierre ganado",
    "Cierre perdido",
]

STAGE_COLORS = {
    "Asignado":             "#888780",
    "Visitado":             "#378ADD",
    "Interesado":           "#BA7517",
    "Esperando Aprobación": "#7F77DD",
    "Cierre ganado":        "#0F6E56",
    "Cierre perdido":       "#A32D2D",
}

st.markdown("""
<style>
    .deal-card {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: box-shadow 0.2s;
    }
    .deal-card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.12); border-color: #ccc; }
    .deal-name { font-weight: 600; font-size: 13px; color: #1a1a1a; margin-bottom: 2px; }
    .deal-company { font-size: 12px; color: #666; margin-bottom: 6px; }
    .deal-prop { font-size: 11px; color: #555; margin-bottom: 2px; }
    .deal-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
    .deal-amount { font-weight: 600; font-size: 13px; color: #1a1a1a; }
    .deal-prob { font-size: 11px; padding: 2px 8px; border-radius: 99px; }
    .prop-label { font-size: 12px; color: #888; margin-bottom: 2px; }
    .prop-value { font-size: 14px; color: #1a1a1a; margin-bottom: 12px; font-weight: 500; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    [data-testid="column"] { padding: 0 4px !important; }
    div[data-testid="stDialog"] > div { max-width: 520px !important; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_deals(source="mock", webhook_url=""):
    if source == "webhook" and webhook_url:
        try:
            res = requests.get(webhook_url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            st.warning(f"No se pudo conectar al webhook ({e}). Usando datos de prueba.")
    data_path = Path(__file__).parent / "deals.json"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)


def prob_style(p, etapa):
    if etapa == "Cierre ganado":  return "background:#E1F5EE; color:#085041;"
    if etapa == "Cierre perdido": return "background:#FCEBEB; color:#791F1F;"
    if p >= 70: return "background:#EAF3DE; color:#3B6D11;"
    if p >= 40: return "background:#FAEEDA; color:#854F0B;"
    return "background:#FAECE7; color:#993C1D;"

def fmt_usd(n):
    if n >= 1_000_000: return f"${n/1_000_000:.1f}M"
    if n >= 1_000:     return f"${n/1_000:.0f}K"
    return f"${n}"


# ── Estado de sesión ─────────────────────────────────────────────────
if "deals" not in st.session_state:
    st.session_state.deals = None
if "selected_deal" not in st.session_state:
    st.session_state.selected_deal = None
if "show_modal" not in st.session_state:
    st.session_state.show_modal = False


# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Pipeline CRM")
    st.markdown("---")

    st.subheader("Fuente de datos")
    source = st.radio("Origen", ["Datos de prueba", "Webhook n8n"])

    webhook_url = ""
    if source == "Webhook n8n":
        webhook_url = st.text_input(
            "URL del webhook",
            placeholder="https://tu-n8n.com/webhook/pipeline-data"
        )

    st.markdown("---")
    st.subheader("Filtros")

    source_key = "mock" if source == "Datos de prueba" else "webhook"
    raw_deals = load_deals(source=source_key, webhook_url=webhook_url)

    if st.session_state.deals is None:
        st.session_state.deals = raw_deals

    df_all = pd.DataFrame(st.session_state.deals)

    vendedores = ["Todos"] + sorted(df_all["vendedor"].unique().tolist())
    vendedor_sel = st.selectbox("Vendedor", vendedores)

    etapas_sel = st.multiselect("Etapas visibles", STAGES, default=STAGES)

    st.markdown("---")
    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state.deals = load_deals(source=source_key, webhook_url=webhook_url)
        st.rerun()

    st.caption("Datos sincronizados cada 1 hora")


# ── Filtrar ───────────────────────────────────────────────────────────
df = pd.DataFrame(st.session_state.deals)
if vendedor_sel != "Todos":
    df = df[df["vendedor"] == vendedor_sel]
df = df[df["etapa"].isin(etapas_sel)]


# ── Header y métricas ─────────────────────────────────────────────────
st.markdown("## Pipeline de Ventas")
st.caption(f"Vendedor: **{vendedor_sel}**" if vendedor_sel != "Todos" else "Todos los vendedores")

m1, m2, m3, m4, m5 = st.columns(5)
total_val = df[df["etapa"] != "Cierre perdido"]["monto"].sum()
ganados   = df[df["etapa"] == "Cierre ganado"]
perdidos  = df[df["etapa"] == "Cierre perdido"]
activos   = df[~df["etapa"].isin(["Cierre ganado", "Cierre perdido"])]

m1.metric("Total negocios", len(df))
m2.metric("Valor pipeline", f"${total_val:,.0f}")
m3.metric("Activos", len(activos))
m4.metric("Ganados", len(ganados), delta=f"${ganados['monto'].sum():,.0f}")
m5.metric("Perdidos", len(perdidos))

st.divider()


# ── Modal de detalle ──────────────────────────────────────────────────
@st.dialog("Detalle del negocio")
def show_deal_modal(deal):
    color = STAGE_COLORS.get(deal["etapa"], "#888")

    st.markdown(f"### {deal['nombre']}")
    st.markdown(
        f"<span style='background:{color}22; color:{color}; padding:3px 10px; "
        f"border-radius:99px; font-size:12px; font-weight:600;'>{deal['etapa']}</span>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='prop-label'>Empresa</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal['empresa']}</div>", unsafe_allow_html=True)

        st.markdown("<div class='prop-label'>Correo</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal['correo']}</div>", unsafe_allow_html=True)

        st.markdown("<div class='prop-label'>Telefono</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal['telefono']}</div>", unsafe_allow_html=True)

        st.markdown("<div class='prop-label'>Vendedor</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal['vendedor']}</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='prop-label'>Valor</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>${deal['monto']:,.0f} USD</div>", unsafe_allow_html=True)

        st.markdown("<div class='prop-label'>Probabilidad</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal['probabilidad']}%</div>", unsafe_allow_html=True)

        st.markdown("<div class='prop-label'>Fecha creacion</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal.get('fecha_creacion','—')}</div>", unsafe_allow_html=True)

        st.markdown("<div class='prop-label'>Cierre estimado</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prop-value'>{deal.get('fecha_cierre_est','—')}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Mover a otra etapa**")

    current_idx = STAGES.index(deal["etapa"]) if deal["etapa"] in STAGES else 0
    nueva_etapa = st.selectbox(
        "Selecciona etapa",
        STAGES,
        index=current_idx,
        key=f"etapa_sel_{deal['id']}"
    )

    col_cancel, col_save = st.columns([1, 1])
    with col_cancel:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()
    with col_save:
        if st.button("Guardar cambio", type="primary", use_container_width=True):
            for d in st.session_state.deals:
                if d["id"] == deal["id"]:
                    d["etapa"] = nueva_etapa
                    break
            st.rerun()


# ── Kanban ────────────────────────────────────────────────────────────
visible_stages = [s for s in STAGES if s in etapas_sel]
cols = st.columns(len(visible_stages))

for i, stage in enumerate(visible_stages):
    stage_df = df[df["etapa"] == stage]
    color = STAGE_COLORS[stage]

    with cols[i]:
        st.markdown(
            f"""<div style="border-top: 3px solid {color}; padding-top: 10px; margin-bottom: 10px;">
                <span style="font-weight:600; font-size:13px;">{stage}</span>
                <span style="background:#f0f0f0; border-radius:99px; padding:1px 8px;
                             font-size:11px; color:#555; margin-left:6px;">{len(stage_df)}</span>
            </div>""",
            unsafe_allow_html=True
        )

        if stage_df.empty:
            st.markdown(
                "<div style='text-align:center; color:#aaa; font-size:12px; padding:20px 0;'>Sin negocios</div>",
                unsafe_allow_html=True
            )
        else:
            for _, row in stage_df.iterrows():
                deal = row.to_dict()
                prob_css = prob_style(deal["probabilidad"], deal["etapa"])
                dias_txt = f"{deal['dias_en_etapa']} dias en etapa"

                st.markdown(
                    f"""<div class="deal-card">
                        <div class="deal-name">{deal['nombre']}</div>
                        <div class="deal-company">{deal['empresa']}</div>
                        <div class="deal-prop">{deal['correo']}</div>
                        <div class="deal-prop">{deal['telefono']}</div>
                        <div class="deal-footer">
                            <span class="deal-amount">{fmt_usd(deal['monto'])}</span>
                            <span class="deal-prob" style="{prob_css}">{deal['probabilidad']}%</span>
                        </div>
                        <div style="font-size:11px; color:#999; margin-top:6px;">{dias_txt}</div>
                    </div>""",
                    unsafe_allow_html=True
                )

                if st.button(
                    "Ver detalle",
                    key=f"btn_{deal['id']}",
                    use_container_width=True
                ):
                    show_deal_modal(deal)

        if not stage_df.empty:
            st.markdown(
                f"<div style='text-align:center; font-size:11px; color:#888; "
                f"border-top:1px solid #eee; padding-top:6px; margin-top:4px;'>"
                f"Total: <b>{fmt_usd(int(stage_df['monto'].sum()))}</b></div>",
                unsafe_allow_html=True
            )
