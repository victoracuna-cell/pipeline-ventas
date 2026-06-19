import streamlit as st
import streamlit.components.v1 as components
import json
import requests
from pathlib import Path

st.set_page_config(page_title="Pipeline TUU", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background:#f4f5f7; }
  [data-testid="stSidebar"] { display:none; }
  .block-container { padding:0 !important; max-width:100% !important; }
  #MainMenu, footer, header { visibility:hidden; }
  iframe { border:none !important; }
</style>
""", unsafe_allow_html=True)

# ── Auth ──────────────────────────────────────────────────────────────
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    if not st.session_state.logged_in:
        st.markdown("""
        <style>
          [data-testid="stAppViewContainer"] { background:#fff; }
        </style>""", unsafe_allow_html=True)
        _, col, _ = st.columns([1,1,1])
        with col:
            st.markdown("<div style='height:100px'></div>", unsafe_allow_html=True)
            st.markdown("""
              <div style='text-align:center;margin-bottom:40px;'>
                <div style='font-size:42px;font-weight:800;color:#1A4ED8;letter-spacing:-2px;'>TUU</div>
                <div style='font-size:12px;color:#94a3b8;margin-top:6px;text-transform:uppercase;letter-spacing:0.08em;'>Pipeline de Ventas</div>
              </div>""", unsafe_allow_html=True)
            with st.form("login"):
                correo = st.text_input("", placeholder="Correo electronico")
                clave  = st.text_input("", placeholder="Contrasena", type="password")
                ok     = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
                if ok:
                    usuarios = st.secrets.get("usuarios", {})
                    if correo in usuarios and usuarios[correo] == clave:
                        vendedores = st.secrets.get("vendedores", {})
                        st.session_state.logged_in   = True
                        st.session_state.usuario     = correo
                        st.session_state.vendedor    = vendedores.get(correo, correo)
                        st.session_state.login_error = False
                        st.session_state.deals       = None
                        st.rerun()
                    else:
                        st.session_state.login_error = True
            if st.session_state.login_error:
                st.markdown("<div style='text-align:center;color:#ef4444;font-size:13px;margin-top:8px;'>Correo o contrasena incorrectos</div>", unsafe_allow_html=True)
        st.stop()

check_login()

# ── Data ──────────────────────────────────────────────────────────────
STAGES = ["Asignado","Visitado","Interesado","Esperando Aprobacion","Cierre ganado","Cierre perdido"]

@st.cache_data(ttl=3600)
def load_deals(source="mock", webhook_url=""):
    if source == "webhook" and webhook_url:
        try:
            r = requests.get(webhook_url, timeout=10)
            r.raise_for_status()
            return r.json()
        except:
            pass
    return json.loads((Path(__file__).parent / "deals.json").read_text(encoding="utf-8"))

if "deals" not in st.session_state or st.session_state.deals is None:
    st.session_state.deals = load_deals()

vendedor_activo = st.session_state.get("vendedor", "")
deals = [d for d in (st.session_state.deals or []) if d.get("vendedor") == vendedor_activo]

deals_json  = json.dumps(deals, ensure_ascii=False)
stages_json = json.dumps(STAGES, ensure_ascii=False)
vendor_json = json.dumps(vendedor_activo, ensure_ascii=False)

# ── Full app HTML ─────────────────────────────────────────────────────
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:#f4f5f7;height:100vh;display:flex;flex-direction:column;overflow:hidden;}}

/* ── Top bar ── */
.topbar{{
  display:flex;align-items:center;gap:12px;
  background:#fff;border-bottom:1px solid #e8e8e8;
  padding:0 20px;height:52px;flex-shrink:0;
}}
.logo{{font-size:20px;font-weight:800;color:#1A4ED8;letter-spacing:-1px;margin-right:8px;}}
.topbar-title{{font-size:15px;font-weight:700;color:#0f172a;}}
.search-wrap{{flex:1;max-width:320px;position:relative;}}
.search-wrap input{{
  width:100%;padding:7px 12px 7px 34px;
  border:1px solid #e8e8e8;border-radius:8px;
  font-size:13px;color:#0f172a;background:#f8f9fa;outline:none;
}}
.search-wrap input:focus{{border-color:#1A4ED8;background:#fff;}}
.search-icon{{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#94a3b8;font-size:14px;}}
.topbar-right{{display:flex;align-items:center;gap:8px;margin-left:auto;}}
.btn-new{{
  display:flex;align-items:center;gap:6px;
  background:#1A4ED8;color:#fff;border:none;
  padding:7px 14px;border-radius:8px;font-size:13px;font-weight:600;
  cursor:pointer;transition:background 0.15s;
}}
.btn-new:hover{{background:#1e40af;}}
.view-toggle{{display:flex;border:1px solid #e8e8e8;border-radius:8px;overflow:hidden;}}
.view-btn{{
  padding:6px 12px;background:#fff;border:none;cursor:pointer;
  font-size:12px;color:#64748b;transition:all 0.15s;
}}
.view-btn.active{{background:#f0f5ff;color:#1A4ED8;font-weight:600;}}
.user-pill{{
  display:flex;align-items:center;gap:8px;
  padding:4px 10px;background:#f8f9fa;border-radius:8px;
  font-size:12px;color:#64748b;cursor:pointer;
}}
.user-pill:hover{{background:#f0f5ff;}}
.avatar{{width:26px;height:26px;border-radius:50%;background:#1A4ED8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;}}

/* ── Sub nav (stats) ── */
.subnav{{
  display:flex;align-items:center;gap:0;
  background:#fff;border-bottom:1px solid #e8e8e8;
  padding:0 20px;height:40px;flex-shrink:0;
}}
.subnav-tab{{
  padding:0 14px;height:100%;display:flex;align-items:center;
  font-size:12px;font-weight:500;color:#64748b;cursor:pointer;
  border-bottom:2px solid transparent;margin-bottom:-1px;
  transition:all 0.15s;
}}
.subnav-tab.active{{color:#1A4ED8;border-bottom-color:#1A4ED8;font-weight:600;}}
.subnav-tab:hover{{color:#1A4ED8;}}
.stats-bar{{display:flex;align-items:center;gap:20px;margin-left:auto;}}
.stat-item{{display:flex;align-items:center;gap:6px;font-size:12px;color:#64748b;}}
.stat-val{{font-weight:700;color:#0f172a;}}
.stat-dot{{width:8px;height:8px;border-radius:50%;}}

/* ── Main ── */
.main{{flex:1;overflow:hidden;display:flex;flex-direction:column;}}

/* ── Board ── */
.board-wrap{{flex:1;overflow-x:auto;overflow-y:hidden;padding:16px 20px;display:flex;gap:12px;}}
.col{{
  flex:0 0 220px;min-width:200px;
  display:flex;flex-direction:column;max-height:100%;
}}
.col-head{{
  display:flex;align-items:center;gap:8px;
  padding:10px 12px;background:#fff;
  border-radius:10px 10px 0 0;border:1px solid #e8e8e8;border-bottom:none;
}}
.col-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;}}
.col-name{{font-size:11px;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:0.05em;flex:1;}}
.col-count{{font-size:11px;color:#94a3b8;font-weight:600;}}
.col-total-badge{{font-size:10px;color:#1A4ED8;background:#eff6ff;padding:1px 6px;border-radius:4px;font-weight:600;}}
.cards-wrap{{
  flex:1;overflow-y:auto;padding:8px;
  background:#f4f5f7;border:1px solid #e8e8e8;border-top:none;
  border-radius:0 0 10px 10px;
  scrollbar-width:thin;scrollbar-color:#e2e8f0 transparent;
}}
.cards-wrap.over{{background:#eff6ff;border-color:#1A4ED8;}}
.card{{
  background:#fff;border:1px solid #e8e8e8;border-radius:8px;
  padding:12px;margin-bottom:8px;cursor:grab;
  transition:box-shadow 0.15s,border-color 0.15s;
  position:relative;
}}
.card:hover{{box-shadow:0 2px 12px rgba(0,0,0,0.08);border-color:#d0d5dd;}}
.card.dragging{{opacity:0.4;box-shadow:0 8px 24px rgba(26,78,216,0.2);}}
.card-top{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:4px;}}
.card-name{{font-size:13px;font-weight:600;color:#0f172a;line-height:1.3;flex:1;}}
.card-menu{{opacity:0;cursor:pointer;color:#94a3b8;font-size:16px;padding:0 2px;transition:opacity 0.15s;}}
.card:hover .card-menu{{opacity:1;}}
.card-biz{{font-size:11px;color:#1A4ED8;font-weight:500;margin-bottom:8px;}}
.card-bar{{height:3px;border-radius:2px;background:#e8e8e8;margin-bottom:8px;}}
.card-bar-fill{{height:100%;border-radius:2px;background:#1A4ED8;}}
.card-props{{display:flex;flex-direction:column;gap:2px;margin-bottom:8px;}}
.card-prop{{font-size:10px;color:#94a3b8;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.card-bottom{{display:flex;justify-content:space-between;align-items:center;padding-top:8px;border-top:1px solid #f4f5f7;}}
.card-amt{{font-size:12px;font-weight:700;color:#0f172a;}}
.card-badge{{font-size:10px;font-weight:600;padding:2px 7px;border-radius:5px;}}
.empty-col{{text-align:center;padding:20px 8px;color:#d0d5dd;font-size:11px;}}

/* ── List view ── */
.list-wrap{{flex:1;overflow-y:auto;padding:16px 20px;}}
.list-table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e8e8e8;}}
.list-table th{{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;padding:10px 14px;text-align:left;border-bottom:1px solid #e8e8e8;background:#f8f9fa;}}
.list-table td{{font-size:13px;color:#0f172a;padding:11px 14px;border-bottom:1px solid #f4f5f7;vertical-align:middle;}}
.list-table tr:last-child td{{border-bottom:none;}}
.list-table tr:hover td{{background:#f8f9fa;cursor:pointer;}}
.stage-pill{{display:inline-block;font-size:11px;font-weight:600;padding:3px 9px;border-radius:5px;}}
.list-amt{{font-weight:700;}}
.list-biz{{color:#1A4ED8;font-size:12px;}}

/* ── Stats view ── */
.stats-wrap{{flex:1;overflow-y:auto;padding:20px;}}
.stats-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;}}
.stat-card{{background:#fff;border:1px solid #e8e8e8;border-radius:10px;padding:16px 18px;}}
.stat-card-label{{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;}}
.stat-card-val{{font-size:26px;font-weight:800;color:#0f172a;letter-spacing:-0.5px;}}
.stat-card-sub{{font-size:11px;color:#94a3b8;margin-top:4px;}}
.chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
.chart-card{{background:#fff;border:1px solid #e8e8e8;border-radius:10px;padding:18px;}}
.chart-title{{font-size:13px;font-weight:600;color:#0f172a;margin-bottom:14px;}}
.bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}
.bar-label{{font-size:11px;color:#64748b;width:130px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.bar-track{{flex:1;height:8px;background:#f4f5f7;border-radius:4px;overflow:hidden;}}
.bar-fill{{height:100%;border-radius:4px;background:#1A4ED8;}}
.bar-val{{font-size:11px;font-weight:600;color:#0f172a;width:40px;text-align:right;}}
.funnel-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;}}
.funnel-label{{font-size:11px;color:#64748b;width:160px;flex-shrink:0;}}
.funnel-track{{flex:1;height:22px;background:#f4f5f7;border-radius:5px;overflow:hidden;position:relative;}}
.funnel-fill{{height:100%;border-radius:5px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;}}
.funnel-n{{font-size:10px;font-weight:700;color:#fff;}}

/* ── Modal ── */
.ov{{display:none;position:fixed;inset:0;background:rgba(15,23,42,0.45);z-index:900;align-items:flex-start;justify-content:flex-end;}}
.ov.open{{display:flex;}}
.drawer{{
  width:480px;height:100vh;background:#fff;
  box-shadow:-8px 0 40px rgba(0,0,0,0.12);
  display:flex;flex-direction:column;
  animation:slideIn 0.2s ease;overflow:hidden;
}}
@keyframes slideIn{{from{{transform:translateX(40px);opacity:0}}to{{transform:none;opacity:1}}}}
.drawer-head{{
  display:flex;align-items:center;gap:12px;
  padding:16px 20px;border-bottom:1px solid #f0f0f0;flex-shrink:0;
}}
.drawer-title{{flex:1;font-size:16px;font-weight:700;color:#0f172a;}}
.drawer-actions{{display:flex;gap:6px;}}
.dact-btn{{
  padding:6px 12px;border-radius:7px;border:1px solid #e8e8e8;
  background:#fff;font-size:12px;font-weight:600;cursor:pointer;color:#64748b;
}}
.dact-btn:hover{{background:#f8f9fa;}}
.dact-btn.primary{{background:#1A4ED8;color:#fff;border-color:#1A4ED8;}}
.dact-btn.primary:hover{{background:#1e40af;}}
.dact-btn.danger{{color:#ef4444;border-color:#fecaca;}}
.dact-btn.danger:hover{{background:#fef2f2;}}
.stage-nav{{
  display:flex;align-items:center;gap:0;
  padding:12px 20px;border-bottom:1px solid #f0f0f0;flex-shrink:0;overflow-x:auto;
}}
.stage-step{{
  display:flex;align-items:center;gap:4px;
  padding:4px 10px;border-radius:6px;cursor:pointer;
  font-size:11px;font-weight:500;color:#94a3b8;white-space:nowrap;
  transition:all 0.15s;
}}
.stage-step.active{{font-weight:700;}}
.stage-step-dot{{width:6px;height:6px;border-radius:50%;flex-shrink:0;}}
.stage-arrow{{color:#d0d5dd;font-size:10px;margin:0 2px;}}
.drawer-body{{flex:1;overflow-y:auto;padding:20px;}}
.sec-title{{font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin:0 0 12px;padding-bottom:8px;border-bottom:1px solid #f4f5f7;}}
.field-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}}
.field{{display:flex;flex-direction:column;gap:4px;}}
.field.full{{grid-column:1/-1;}}
.field label{{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.04em;font-weight:600;}}
.field input,.field select,.field textarea{{
  padding:8px 10px;border:1px solid #e8e8e8;border-radius:7px;
  font-size:13px;color:#0f172a;background:#f8f9fa;outline:none;
  transition:border-color 0.15s,background 0.15s;
  font-family:inherit;
}}
.field input:focus,.field select:focus,.field textarea:focus{{border-color:#1A4ED8;background:#fff;}}
.field textarea{{resize:vertical;min-height:72px;}}
.nivel-sel{{appearance:none;}}
.comentarios{{margin-top:4px;}}
.comment-box{{
  background:#f8f9fa;border:1px solid #e8e8e8;border-radius:8px;
  padding:10px 12px;margin-bottom:8px;
}}
.comment-text{{font-size:13px;color:#0f172a;line-height:1.5;white-space:pre-wrap;}}
.comment-meta{{font-size:10px;color:#94a3b8;margin-top:4px;}}
.comment-input-wrap{{display:flex;flex-direction:column;gap:8px;}}
.comment-input{{
  width:100%;padding:10px 12px;border:1px solid #e8e8e8;border-radius:8px;
  font-size:13px;color:#0f172a;background:#f8f9fa;outline:none;
  resize:vertical;min-height:72px;font-family:inherit;
}}
.comment-input:focus{{border-color:#1A4ED8;background:#fff;}}
.btn-comment{{
  align-self:flex-end;padding:7px 14px;background:#1A4ED8;color:#fff;
  border:none;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;
}}
.btn-comment:hover{{background:#1e40af;}}

/* ── New deal modal ── */
.ndov{{display:none;position:fixed;inset:0;background:rgba(15,23,42,0.45);z-index:950;align-items:center;justify-content:center;}}
.ndov.open{{display:flex;}}
.nd-modal{{background:#fff;border-radius:14px;width:460px;max-width:94vw;max-height:90vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,0.18);animation:pop 0.18s ease;}}
@keyframes pop{{from{{transform:scale(0.96);opacity:0}}to{{transform:none;opacity:1}}}}
.nd-head{{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #f0f0f0;}}
.nd-title{{font-size:15px;font-weight:700;color:#0f172a;}}
.nd-close{{width:28px;height:28px;border-radius:7px;border:1px solid #e8e8e8;background:#f8f9fa;cursor:pointer;font-size:14px;color:#94a3b8;display:flex;align-items:center;justify-content:center;}}
.nd-close:hover{{background:#f0f0f0;color:#0f172a;}}
.nd-body{{padding:20px;}}
.nd-foot{{padding:14px 20px;border-top:1px solid #f0f0f0;display:flex;gap:8px;justify-content:flex-end;}}
.btn-cancel{{padding:8px 16px;border:1px solid #e8e8e8;border-radius:8px;background:#fff;font-size:13px;cursor:pointer;color:#64748b;}}
.btn-create{{padding:8px 18px;background:#1A4ED8;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;}}
.btn-create:hover{{background:#1e40af;}}

/* scrollbar */
::-webkit-scrollbar{{width:5px;height:5px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:#e2e8f0;border-radius:3px;}}
</style></head><body>

<!-- TOP BAR -->
<div class="topbar">
  <span class="logo">TUU</span>
  <span class="topbar-title">Pipeline</span>
  <div class="search-wrap">
    <span class="search-icon">&#9906;</span>
    <input type="text" id="search" placeholder="Buscar negocio, empresa, contacto..." oninput="filterDeals()">
  </div>
  <div class="topbar-right">
    <button class="btn-new" onclick="openNew()">+ Crear negocio</button>
    <div class="view-toggle">
      <button class="view-btn active" id="vb-pipeline" onclick="setView('pipeline')">&#9776; Pipeline</button>
      <button class="view-btn" id="vb-list" onclick="setView('list')">&#9776; Lista</button>
      <button class="view-btn" id="vb-stats" onclick="setView('stats')">&#9636; Stats</button>
    </div>
    <div class="user-pill" onclick="logout()">
      <div class="avatar" id="avatar-initials">--</div>
      <span id="user-name">...</span>
    </div>
  </div>
</div>

<!-- SUB NAV -->
<div class="subnav">
  <div class="subnav-tab active" onclick="setView('pipeline')">Mis negocios</div>
  <div class="stats-bar">
    <div class="stat-item"><span class="stat-dot" style="background:#1A4ED8"></span>Activos: <span class="stat-val" id="sbar-activos">0</span></div>
    <div class="stat-item"><span class="stat-dot" style="background:#059669"></span>Ganados: <span class="stat-val" id="sbar-ganados">0</span></div>
    <div class="stat-item"><span class="stat-dot" style="background:#dc2626"></span>Perdidos: <span class="stat-val" id="sbar-perdidos">0</span></div>
    <div class="stat-item">Valor: <span class="stat-val" id="sbar-valor">$0</span></div>
  </div>
</div>

<!-- MAIN -->
<div class="main" id="main-content">
  <!-- PIPELINE VIEW -->
  <div id="view-pipeline" class="board-wrap"></div>
  <!-- LIST VIEW -->
  <div id="view-list" class="list-wrap" style="display:none">
    <table class="list-table">
      <thead><tr>
        <th>Contacto</th><th>Negocio</th><th>Etapa</th>
        <th>Valor</th><th>Prob.</th><th>Ciudad</th><th>Nivel</th>
      </tr></thead>
      <tbody id="list-body"></tbody>
    </table>
  </div>
  <!-- STATS VIEW -->
  <div id="view-stats" class="stats-wrap" style="display:none"></div>
</div>

<!-- DEAL DRAWER -->
<div class="ov" id="ov" onclick="if(event.target===this)closeDrawer()">
  <div class="drawer">
    <div class="drawer-head">
      <div class="drawer-title" id="d-title">Negocio</div>
      <div class="drawer-actions">
        <button class="dact-btn danger" onclick="deleteDeal()">Eliminar</button>
        <button class="dact-btn" onclick="closeDrawer()">Cancelar</button>
        <button class="dact-btn primary" onclick="saveDeal()">Guardar</button>
      </div>
    </div>
    <div class="stage-nav" id="d-stage-nav"></div>
    <div class="drawer-body">
      <div class="sec-title">Contacto</div>
      <div class="field-grid">
        <div class="field"><label>Nombre</label><input id="f-nombre" type="text"></div>
        <div class="field"><label>Apellido</label><input id="f-apellido" type="text"></div>
        <div class="field"><label>Correo</label><input id="f-correo" type="email"></div>
        <div class="field"><label>Telefono</label><input id="f-telefono" type="tel"></div>
      </div>
      <div class="sec-title">Negocio</div>
      <div class="field-grid">
        <div class="field full"><label>Nombre del negocio</label><input id="f-negnombre" type="text"></div>
        <div class="field full"><label>Descripcion</label><textarea id="f-desc"></textarea></div>
        <div class="field"><label>Nivel de venta</label>
          <select id="f-nivel" class="nivel-sel">
            <option>Alto</option><option>Medio</option><option>Bajo</option>
          </select>
        </div>
        <div class="field"><label>Resultado visita</label><input id="f-resultado" type="text"></div>
        <div class="field"><label>Valor (USD)</label><input id="f-monto" type="number"></div>
        <div class="field"><label>Probabilidad %</label><input id="f-prob" type="number" min="0" max="100"></div>
        <div class="field"><label>Fecha creacion</label><input id="f-created" type="date"></div>
        <div class="field"><label>Cierre estimado</label><input id="f-close" type="date"></div>
      </div>
      <div class="sec-title">Ubicacion</div>
      <div class="field-grid">
        <div class="field"><label>Calle</label><input id="f-calle" type="text"></div>
        <div class="field"><label>Numero</label><input id="f-numero" type="text"></div>
        <div class="field"><label>Comuna</label><input id="f-comuna" type="text"></div>
        <div class="field"><label>Ciudad</label><input id="f-ciudad" type="text"></div>
        <div class="field full"><label>Region</label><input id="f-region" type="text"></div>
      </div>
      <div class="sec-title">Comentarios</div>
      <div class="comentarios" id="comments-list"></div>
      <div class="comment-input-wrap">
        <textarea class="comment-input" id="new-comment" placeholder="Escribe un comentario..."></textarea>
        <button class="btn-comment" onclick="addComment()">Agregar comentario</button>
      </div>
    </div>
  </div>
</div>

<!-- NEW DEAL MODAL -->
<div class="ndov" id="ndov" onclick="if(event.target===this)closeNew()">
  <div class="nd-modal">
    <div class="nd-head">
      <div class="nd-title">Nuevo negocio</div>
      <button class="nd-close" onclick="closeNew()">&#x2715;</button>
    </div>
    <div class="nd-body">
      <div class="field-grid">
        <div class="field"><label>Nombre</label><input id="n-nombre" type="text" placeholder="Juan"></div>
        <div class="field"><label>Apellido</label><input id="n-apellido" type="text" placeholder="Perez"></div>
        <div class="field"><label>Correo</label><input id="n-correo" type="email" placeholder="juan@mail.com"></div>
        <div class="field"><label>Telefono</label><input id="n-tel" type="tel" placeholder="+56 9 ..."></div>
        <div class="field full"><label>Nombre del negocio</label><input id="n-negnombre" type="text" placeholder="Almacen El Sol"></div>
        <div class="field"><label>Valor (USD)</label><input id="n-monto" type="number" placeholder="0"></div>
        <div class="field"><label>Probabilidad %</label><input id="n-prob" type="number" placeholder="50" min="0" max="100"></div>
        <div class="field"><label>Nivel de venta</label>
          <select id="n-nivel"><option>Alto</option><option selected>Medio</option><option>Bajo</option></select>
        </div>
        <div class="field"><label>Ciudad</label><input id="n-ciudad" type="text"></div>
        <div class="field"><label>Comuna</label><input id="n-comuna" type="text"></div>
        <div class="field full"><label>Region</label><input id="n-region" type="text"></div>
      </div>
    </div>
    <div class="nd-foot">
      <button class="btn-cancel" onclick="closeNew()">Cancelar</button>
      <button class="btn-create" onclick="createDeal()">Crear negocio</button>
    </div>
  </div>
</div>

<script>
const STAGES={stages_json};
const VENDOR={vendor_json};
const COLORS={{"Asignado":"#94a3b8","Visitado":"#1A4ED8","Interesado":"#d97706","Esperando Aprobacion":"#7c3aed","Cierre ganado":"#059669","Cierre perdido":"#dc2626"}};
const PROB_COLORS={{
  ganado:'background:#f0fdf4;color:#16a34a',
  perdido:'background:#fef2f2;color:#dc2626',
  high:'background:#f0fdf4;color:#16a34a',
  mid:'background:#fffbeb;color:#d97706',
  low:'background:#fef2f2;color:#dc2626'
}};

let deals={deals_json};
let filteredDeals=[...deals];
let currentView='pipeline';
let curId=null;
let dragId=null;

// Init
document.getElementById('user-name').textContent=VENDOR;
const initials=VENDOR.split(' ').map(w=>w[0]||'').join('').slice(0,2).toUpperCase();
document.getElementById('avatar-initials').textContent=initials;

function fmt(n){{if(n>=1e6)return'$'+(n/1e6).toFixed(1)+'M';if(n>=1e3)return'$'+Math.round(n/1e3)+'K';return'$'+n;}}
function pStyle(p,e){{
  if(e==='Cierre ganado')return PROB_COLORS.ganado;
  if(e==='Cierre perdido')return PROB_COLORS.perdido;
  if(p>=70)return PROB_COLORS.high;
  if(p>=40)return PROB_COLORS.mid;
  return PROB_COLORS.low;
}}
function uid(){{return Date.now().toString(36)+Math.random().toString(36).slice(2);}}

function updateStatsBar(){{
  const ganados=deals.filter(d=>d.etapa==='Cierre ganado').length;
  const perdidos=deals.filter(d=>d.etapa==='Cierre perdido').length;
  const activos=deals.filter(d=>!['Cierre ganado','Cierre perdido'].includes(d.etapa)).length;
  const valor=deals.filter(d=>d.etapa!=='Cierre perdido').reduce((a,d)=>a+d.monto,0);
  document.getElementById('sbar-activos').textContent=activos;
  document.getElementById('sbar-ganados').textContent=ganados;
  document.getElementById('sbar-perdidos').textContent=perdidos;
  document.getElementById('sbar-valor').textContent=fmt(valor);
}}

function filterDeals(){{
  const q=document.getElementById('search').value.toLowerCase().trim();
  filteredDeals=q?deals.filter(d=>
    (d.nombre+' '+d.apellido).toLowerCase().includes(q)||
    (d.nombre_negocio||'').toLowerCase().includes(q)||
    (d.correo||'').toLowerCase().includes(q)||
    (d.empresa||'').toLowerCase().includes(q)
  ):[...deals];
  render();
}}

function setView(v){{
  currentView=v;
  ['pipeline','list','stats'].forEach(x=>{{
    document.getElementById('view-'+x).style.display=x===v?(x==='pipeline'?'flex':'block'):'none';
    const btn=document.getElementById('vb-'+x);
    if(btn) btn.classList.toggle('active',x===v);
  }});
  render();
}}

function render(){{
  updateStatsBar();
  if(currentView==='pipeline') buildBoard();
  else if(currentView==='list') buildList();
  else buildStats();
}}

// ── Board ──────────────────────────────────────────────────────────
function buildBoard(){{
  const board=document.getElementById('view-pipeline');
  board.innerHTML='';
  STAGES.forEach(stage=>{{
    const sd=filteredDeals.filter(d=>d.etapa===stage);
    const col=document.createElement('div');col.className='col';
    const total=sd.reduce((a,d)=>a+d.monto,0);
    const cw=document.createElement('div');cw.className='cards-wrap';cw.dataset.stage=stage;
    cw.addEventListener('dragover',e=>{{e.preventDefault();cw.classList.add('over');}});
    cw.addEventListener('dragleave',()=>cw.classList.remove('over'));
    cw.addEventListener('drop',e=>{{
      e.preventDefault();cw.classList.remove('over');
      if(dragId){{const d=deals.find(x=>x.id===dragId);if(d){{d.etapa=stage;filterDeals();send();}}}}
    }});
    sd.forEach(d=>{{
      const card=document.createElement('div');card.className='card';card.draggable=true;card.dataset.id=d.id;
      card.addEventListener('dragstart',e=>{{dragId=d.id;setTimeout(()=>card.classList.add('dragging'),0);}});
      card.addEventListener('dragend',()=>{{card.classList.remove('dragging');dragId=null;}});
      card.addEventListener('click',()=>openDrawer(d.id));
      card.innerHTML=`
        <div class="card-top">
          <div class="card-name">${{d.nombre}} ${{d.apellido}}</div>
        </div>
        <div class="card-biz">${{d.nombre_negocio||d.empresa||''}}</div>
        <div class="card-bar"><div class="card-bar-fill" style="width:${{d.probabilidad||0}}%"></div></div>
        <div class="card-props">
          <div class="card-prop">${{d.correo||''}}</div>
          <div class="card-prop">${{d.telefono||''}}</div>
          <div class="card-prop" style="color:#cbd5e1">${{[d.comuna,d.ciudad].filter(Boolean).join(', ')}}</div>
        </div>
        <div class="card-bottom">
          <span class="card-amt">${{fmt(d.monto||0)}}</span>
          <span class="card-badge" style="${{pStyle(d.probabilidad||0,d.etapa)}}">${{d.probabilidad||0}}%</span>
        </div>`;
      cw.appendChild(card);
    }});
    if(!sd.length) cw.innerHTML='<div class="empty-col">Sin negocios</div>';
    col.innerHTML=`<div class="col-head">
      <span class="col-dot" style="background:${{COLORS[stage]||'#94a3b8'}}"></span>
      <span class="col-name">${{stage}}</span>
      <span class="col-count">${{sd.length}}</span>
      ${{sd.length?`<span class="col-total-badge">${{fmt(total)}}</span>`:''}}
    </div>`;
    col.appendChild(cw);
    board.appendChild(col);
  }});
}}

// ── List ──────────────────────────────────────────────────────────
function buildList(){{
  const tbody=document.getElementById('list-body');tbody.innerHTML='';
  filteredDeals.forEach(d=>{{
    const tr=document.createElement('tr');
    tr.onclick=()=>openDrawer(d.id);
    const col=COLORS[d.etapa]||'#94a3b8';
    tr.innerHTML=`
      <td><div style="font-weight:600">${{d.nombre}} ${{d.apellido}}</div></td>
      <td><div class="list-biz">${{d.nombre_negocio||''}}</div></td>
      <td><span class="stage-pill" style="background:${{col}}18;color:${{col}}">${{d.etapa}}</span></td>
      <td><span class="list-amt">${{fmt(d.monto||0)}}</span></td>
      <td><span class="card-badge" style="${{pStyle(d.probabilidad||0,d.etapa)}}">${{d.probabilidad||0}}%</span></td>
      <td style="color:#64748b;font-size:12px">${{d.ciudad||'—'}}</td>
      <td><span class="card-badge nivel-${{d.nivel_venta}}" style="font-size:11px;padding:2px 7px;border-radius:5px;font-weight:600;${{d.nivel_venta==='Alto'?'background:#f0fdf4;color:#16a34a':d.nivel_venta==='Medio'?'background:#fffbeb;color:#d97706':'background:#fef2f2;color:#dc2626'}}">${{d.nivel_venta||''}}</span></td>`;
    tbody.appendChild(tr);
  }});
}}

// ── Stats ─────────────────────────────────────────────────────────
function buildStats(){{
  const w=document.getElementById('view-stats');
  const ganados=deals.filter(d=>d.etapa==='Cierre ganado');
  const perdidos=deals.filter(d=>d.etapa==='Cierre perdido');
  const activos=deals.filter(d=>!['Cierre ganado','Cierre perdido'].includes(d.etapa));
  const valor=deals.filter(d=>d.etapa!=='Cierre perdido').reduce((a,d)=>a+(d.monto||0),0);
  const tasa=deals.length?Math.round(ganados.length/deals.length*100):0;

  let funnelRows=STAGES.map(s=>{{
    const n=deals.filter(d=>d.etapa===s).length;
    const pct=deals.length?Math.round(n/deals.length*100):0;
    return `<div class="funnel-row">
      <div class="funnel-label">${{s}}</div>
      <div class="funnel-track">
        <div class="funnel-fill" style="width:${{pct}}%;background:${{COLORS[s]||'#94a3b8'}}">
          ${{n?`<span class="funnel-n">${{n}}</span>`:''}}
        </div>
      </div>
    </div>`;
  }}).join('');

  const maxMonto=Math.max(...deals.map(d=>d.monto||0),1);
  let topDeals=[...deals].sort((a,b)=>(b.monto||0)-(a.monto||0)).slice(0,6);
  let barRows=topDeals.map(d=>`<div class="bar-row">
    <div class="bar-label">${{d.nombre}} ${{d.apellido}}</div>
    <div class="bar-track"><div class="bar-fill" style="width:${{Math.round((d.monto||0)/maxMonto*100)}}%"></div></div>
    <div class="bar-val">${{fmt(d.monto||0)}}</div>
  </div>`).join('');

  w.innerHTML=`
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-card-label">Total negocios</div><div class="stat-card-val">${{deals.length}}</div><div class="stat-card-sub">En el pipeline</div></div>
      <div class="stat-card"><div class="stat-card-label">Valor activo</div><div class="stat-card-val">${{fmt(valor)}}</div><div class="stat-card-sub">Excluyendo perdidos</div></div>
      <div class="stat-card"><div class="stat-card-label">Tasa de cierre</div><div class="stat-card-val">${{tasa}}%</div><div class="stat-card-sub">${{ganados.length}} ganados / ${{deals.length}} totales</div></div>
      <div class="stat-card"><div class="stat-card-label">En curso</div><div class="stat-card-val">${{activos.length}}</div><div class="stat-card-sub">${{perdidos.length}} perdidos</div></div>
    </div>
    <div class="chart-row">
      <div class="chart-card"><div class="chart-title">Embudo por etapa</div>${{funnelRows}}</div>
      <div class="chart-card"><div class="chart-title">Top negocios por valor</div>${{barRows}}</div>
    </div>`;
}}

// ── Drawer ────────────────────────────────────────────────────────
function openDrawer(id){{
  const d=deals.find(x=>x.id===id);if(!d)return;curId=id;
  document.getElementById('d-title').textContent=(d.nombre||'')+' '+(d.apellido||'');
  document.getElementById('f-nombre').value=d.nombre||'';
  document.getElementById('f-apellido').value=d.apellido||'';
  document.getElementById('f-correo').value=d.correo||'';
  document.getElementById('f-telefono').value=d.telefono||'';
  document.getElementById('f-negnombre').value=d.nombre_negocio||'';
  document.getElementById('f-desc').value=d.descripcion_negocio||'';
  document.getElementById('f-nivel').value=d.nivel_venta||'Medio';
  document.getElementById('f-resultado').value=d.resultado_visita||'';
  document.getElementById('f-monto').value=d.monto||0;
  document.getElementById('f-prob').value=d.probabilidad||0;
  document.getElementById('f-created').value=d.fecha_creacion||'';
  document.getElementById('f-close').value=d.fecha_cierre_est||'';
  document.getElementById('f-calle').value=d.calle||'';
  document.getElementById('f-numero').value=d.numero||'';
  document.getElementById('f-comuna').value=d.comuna||'';
  document.getElementById('f-ciudad').value=d.ciudad||'';
  document.getElementById('f-region').value=d.region||'';

  // Stage nav
  const nav=document.getElementById('d-stage-nav');nav.innerHTML='';
  STAGES.forEach((s,i)=>{{
    if(i>0) nav.insertAdjacentHTML('beforeend','<span class="stage-arrow">&#8250;</span>');
    const step=document.createElement('div');
    step.className='stage-step'+(d.etapa===s?' active':'');
    step.style.cssText=d.etapa===s?`color:${{COLORS[s]}};background:${{COLORS[s]}}15;`:'';
    step.innerHTML=`<span class="stage-step-dot" style="background:${{COLORS[s]}}"></span>${{s}}`;
    step.onclick=()=>{{
      const deal=deals.find(x=>x.id===curId);if(deal){{deal.etapa=s;render();send();openDrawer(curId);}}
    }};
    nav.appendChild(step);
  }});

  // Comments
  renderComments(d);
  document.getElementById('new-comment').value='';
  document.getElementById('ov').classList.add('open');
}}

function renderComments(d){{
  const list=document.getElementById('comments-list');
  const comments=d.comentarios||[];
  list.innerHTML=comments.length?comments.map(c=>`
    <div class="comment-box">
      <div class="comment-text">${{c.texto}}</div>
      <div class="comment-meta">${{c.fecha}}</div>
    </div>`).join(''):'';
}}

function addComment(){{
  const txt=document.getElementById('new-comment').value.trim();if(!txt)return;
  const d=deals.find(x=>x.id===curId);if(!d)return;
  if(!d.comentarios)d.comentarios=[];
  const now=new Date();
  const fecha=now.toLocaleDateString('es-CL',{{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}});
  d.comentarios.push({{texto:txt,fecha}});
  renderComments(d);
  document.getElementById('new-comment').value='';
  send();
}}

function saveDeal(){{
  const d=deals.find(x=>x.id===curId);if(!d)return;
  d.nombre=document.getElementById('f-nombre').value;
  d.apellido=document.getElementById('f-apellido').value;
  d.correo=document.getElementById('f-correo').value;
  d.telefono=document.getElementById('f-telefono').value;
  d.nombre_negocio=document.getElementById('f-negnombre').value;
  d.descripcion_negocio=document.getElementById('f-desc').value;
  d.nivel_venta=document.getElementById('f-nivel').value;
  d.resultado_visita=document.getElementById('f-resultado').value;
  d.monto=parseFloat(document.getElementById('f-monto').value)||0;
  d.probabilidad=parseInt(document.getElementById('f-prob').value)||0;
  d.fecha_creacion=document.getElementById('f-created').value;
  d.fecha_cierre_est=document.getElementById('f-close').value;
  d.calle=document.getElementById('f-calle').value;
  d.numero=document.getElementById('f-numero').value;
  d.comuna=document.getElementById('f-comuna').value;
  d.ciudad=document.getElementById('f-ciudad').value;
  d.region=document.getElementById('f-region').value;
  filterDeals();send();closeDrawer();
}}

function deleteDeal(){{
  if(!confirm('Eliminar este negocio?'))return;
  deals=deals.filter(d=>d.id!==curId);
  filterDeals();send();closeDrawer();
}}

function closeDrawer(){{document.getElementById('ov').classList.remove('open');curId=null;}}

// ── New deal ───────────────────────────────────────────────────────
function openNew(){{document.getElementById('ndov').classList.add('open');}}
function closeNew(){{document.getElementById('ndov').classList.remove('open');}}
function createDeal(){{
  const nombre=document.getElementById('n-nombre').value.trim();
  if(!nombre){{alert('Ingresa el nombre del contacto');return;}}
  const nd={{
    id:uid(),
    nombre,
    apellido:document.getElementById('n-apellido').value,
    correo:document.getElementById('n-correo').value,
    telefono:document.getElementById('n-tel').value,
    nombre_negocio:document.getElementById('n-negnombre').value,
    monto:parseFloat(document.getElementById('n-monto').value)||0,
    probabilidad:parseInt(document.getElementById('n-prob').value)||50,
    nivel_venta:document.getElementById('n-nivel').value,
    ciudad:document.getElementById('n-ciudad').value,
    comuna:document.getElementById('n-comuna').value,
    region:document.getElementById('n-region').value,
    etapa:'Asignado',
    vendedor:VENDOR,
    fecha_creacion:new Date().toISOString().split('T')[0],
    comentarios:[]
  }};
  deals.push(nd);filterDeals();send();closeNew();
  ['n-nombre','n-apellido','n-correo','n-tel','n-negnombre','n-ciudad','n-comuna','n-region'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('n-monto').value='';
  document.getElementById('n-prob').value='50';
}}

function logout(){{
  if(confirm('Cerrar sesion?'))
    window.parent.postMessage({{type:'streamlit:setComponentValue',value:'__logout__'}},'*');
}}

function send(){{
  window.parent.postMessage({{type:'streamlit:setComponentValue',value:JSON.stringify(deals)}},'*');
}}

// Init
filterDeals();
</script></body></html>"""

result = components.html(html, height=800, scrolling=False)

if result:
    if result == "__logout__":
        for k in ["logged_in","usuario","vendedor","deals","login_error"]:
            st.session_state.pop(k, None)
        st.rerun()
    else:
        try:
            updated = json.loads(result)
            ids = {d["id"]: d for d in updated}
            all_deals = st.session_state.deals or []
            # Merge: actualizar existentes + agregar nuevos del vendedor
            existing_ids = {d["id"] for d in all_deals}
            merged = [ids.get(d["id"], d) for d in all_deals]
            for d in updated:
                if d["id"] not in existing_ids:
                    merged.append(d)
            # Eliminar los que ya no existen en updated (borrados)
            updated_ids = {d["id"] for d in updated}
            vendor_ids_in_all = {d["id"] for d in all_deals if d.get("vendedor") == vendedor_activo}
            deleted = vendor_ids_in_all - updated_ids
            merged = [d for d in merged if d["id"] not in deleted]
            st.session_state.deals = merged
        except Exception:
            pass
