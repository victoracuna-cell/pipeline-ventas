import streamlit as st
import pandas as pd
from utils.data_loader import load_deals, STAGES, STAGE_COLORS, STAGE_BG

# ── Configuración de página ──────────────────────────────────────────
st.set_page_config(
    page_title="Pipeline de Ventas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personalizado ────────────────────────────────────────────────
st.markdown("""
<style>
    /* Tarjeta de negocio */
    .deal-card {
        background: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: box-shadow 0.2s;
    }
    .deal-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
    .deal-name { font-weight: 600; font-size: 13px; color: #1a1a1a; margin-bottom: 2px; }
    .deal-company { font-size: 12px; color: #666; margin-bottom: 6px; }
    .deal-prop { font-size: 11px; color: #555; margin-bottom: 2px; }
    .deal-prop a { color: #378ADD; text-decoration: none; }
    .deal-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
    .deal-amount { font-weight: 600; font-size: 13px; color: #1a1a1a; }
    .deal-prob { font-size: 11px; padding: 2px 8px; border-radius: 99px; }

    /* Columna kanban */
    .stage-header {
        padding: 8px 0 10px 0;
        border-radius: 0;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 13px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .stage-dot {
        width: 8px; height: 8px; border-radius: 50%; display: inline-block;
    }
    .stage-count {
        background: #f0f0f0; border-radius: 99px;
        padding: 1px 7px; font-size: 11px; font-weight: 400; color: #555;
    }

    /* Ocultar header por defecto de streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Reducir padding lateral en columnas */
    [data-testid="column"] { padding: 0 4px !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar: configuración ───────────────────────────────────────────
with st.sidebar:
    st.image("https://via.placeholder.com/180x40/7F77DD/ffffff?text=Pipeline+CRM", use_column_width=True)
    st.markdown("---")

    st.subheader("Fuente de datos")
    source = st.radio(
        "Origen",
        ["Datos de prueba", "Webhook n8n"],
        help="Datos de prueba usa el archivo local. Webhook conecta a n8n/HubSpot."
    )

    webhook_url = ""
    if source == "Webhook n8n":
        webhook_url = st.text_input(
            "URL del webhook",
            placeholder="https://tu-n8n.com/webhook/pipeline-data"
        )

    st.markdown("---")
    st.subheader("Filtros")

    source_key = "mock" if source == "Datos de prueba" else "webhook"
    all_deals = load_deals(source=source_key, webhook_url=webhook_url)
    df_all = pd.DataFrame(all_deals)

    vendedores = ["Todos"] + sorted(df_all["vendedor"].unique().tolist())
    vendedor_sel = st.selectbox("Vendedor", vendedores)

    etapas_sel = st.multiselect(
        "Etapas visibles",
        STAGES,
        default=STAGES,
    )

    monto_min, monto_max = int(df_all["monto"].min()), int(df_all["monto"].max())
    rango_monto = st.slider(
        "Rango de monto (USD)",
        monto_min, monto_max,
        (monto_min, monto_max),
        step=1000,
        format="$%d"
    )

    st.markdown("---")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Datos sincronizados cada 1 hora (ttl=3600)")


# ── Filtrar datos ────────────────────────────────────────────────────
df = df_all.copy()
if vendedor_sel != "Todos":
    df = df[df["vendedor"] == vendedor_sel]
df = df[df["etapa"].isin(etapas_sel)]
df = df[(df["monto"] >= rango_monto[0]) & (df["monto"] <= rango_monto[1])]


# ── Header ───────────────────────────────────────────────────────────
st.markdown("## 📊 Pipeline de Ventas")
if vendedor_sel != "Todos":
    st.caption(f"Mostrando negocios de **{vendedor_sel}**")
else:
    st.caption("Todos los vendedores")

# ── Métricas resumen ─────────────────────────────────────────────────
m1, m2, m3, m4, m5 = st.columns(5)

total_val = df[df["etapa"] != "Cierre perdido"]["monto"].sum()
ganados   = df[df["etapa"] == "Cierre ganado"]
perdidos  = df[df["etapa"] == "Cierre perdido"]
activos   = df[~df["etapa"].isin(["Cierre ganado", "Cierre perdido"])]

m1.metric("Negocios totales", len(df))
m2.metric("Valor pipeline", f"${total_val:,.0f}")
m3.metric("Activos", len(activos))
m4.metric("Ganados", len(ganados), delta=f"${ganados['monto'].sum():,.0f}")
m5.metric("Perdidos", len(perdidos))

st.divider()


# ── Helpers ──────────────────────────────────────────────────────────
def prob_style(p: int, etapa: str) -> str:
    if etapa == "Cierre ganado":
        return "background:#E1F5EE; color:#085041;"
    if etapa == "Cierre perdido":
        return "background:#FCEBEB; color:#791F1F;"
    if p >= 70:
        return "background:#EAF3DE; color:#3B6D11;"
    if p >= 40:
        return "background:#FAEEDA; color:#854F0B;"
    return "background:#FAECE7; color:#993C1D;"


def fmt_usd(n: int) -> str:
    if n >= 1_000_000:
        return f"${n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"${n/1_000:.0f}K"
    return f"${n}"


def render_card(deal: dict) -> str:
    prob_css = prob_style(deal["probabilidad"], deal["etapa"])
    dias_txt = f"{deal['dias_en_etapa']} día{'s' if deal['dias_en_etapa'] != 1 else ''} en etapa"
    return f"""
    <div class="deal-card">
        <div class="deal-name">{deal['nombre']}</div>
        <div class="deal-company">🏢 {deal['empresa']}</div>
        <div class="deal-prop">✉️ <a href="mailto:{deal['correo']}">{deal['correo']}</a></div>
        <div class="deal-prop">📞 <a href="tel:{deal['telefono']}">{deal['telefono']}</a></div>
        <div class="deal-prop">🗓️ Cierre est.: {deal.get('fecha_cierre_est', '—')}</div>
        <div class="deal-footer">
            <span class="deal-amount">{fmt_usd(deal['monto'])}</span>
            <span class="deal-prob" style="{prob_css}">{deal['probabilidad']}%</span>
        </div>
        <div style="font-size:11px; color:#999; margin-top:6px;">⏱ {dias_txt}</div>
    </div>
    """


# ── Kanban board ─────────────────────────────────────────────────────
visible_stages = [s for s in STAGES if s in etapas_sel]
cols = st.columns(len(visible_stages))

for i, stage in enumerate(visible_stages):
    stage_df = df[df["etapa"] == stage]
    color = STAGE_COLORS[stage]

    with cols[i]:
        # Header de columna
        st.markdown(
            f"""<div class="stage-header" style="border-top: 3px solid {color}; padding-top: 10px;">
                <span class="stage-dot" style="background:{color}"></span>
                {stage}
                <span class="stage-count">{len(stage_df)}</span>
            </div>""",
            unsafe_allow_html=True
        )

        if stage_df.empty:
            st.markdown(
                "<div style='text-align:center; color:#aaa; font-size:12px; padding:20px 0;'>Sin negocios</div>",
                unsafe_allow_html=True
            )
        else:
            for _, deal in stage_df.iterrows():
                st.markdown(render_card(deal.to_dict()), unsafe_allow_html=True)

        # Total de columna
        if not stage_df.empty:
            total_col = stage_df["monto"].sum()
            st.markdown(
                f"<div style='text-align:center; font-size:11px; color:#888; "
                f"border-top:1px solid #eee; padding-top:6px; margin-top:4px;'>"
                f"Total: <b>{fmt_usd(int(total_col))}</b></div>",
                unsafe_allow_html=True
            )
