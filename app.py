import streamlit as st
import streamlit.components.v1 as components
import json
import requests
from pathlib import Path

st.set_page_config(
    page_title="Pipeline TUU",
    page_icon="https://www.tuu.cl/assets/images/logo/smile-tuu-logo.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)

STAGES = [
    "Asignado",
    "Visitado",
    "Interesado",
    "Esperando Aprobacion",
    "Cierre ganado",
    "Cierre perdido",
]

# ── Carga de datos ────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_deals_from_source(source="mock", webhook_url=""):
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

# ── Estado de sesión ──────────────────────────────────────────────────
if "deals" not in st.session_state:
    st.session_state.deals = None
if "vendedor_sel" not in st.session_state:
    st.session_state.vendedor_sel = "Todos"

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding: 8px 0 16px;">
            <span style="font-size:22px; font-weight:700; color:#1A4ED8; letter-spacing:-0.5px;">TUU</span>
            <span style="font-size:14px; color:#64748b; margin-left:6px;">Pipeline</span>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    source = st.radio("Fuente de datos", ["Datos de prueba", "Webhook n8n"])
    webhook_url = ""
    if source == "Webhook n8n":
        webhook_url = st.text_input("URL del webhook", placeholder="https://tu-n8n.com/webhook/pipeline-data")

    st.markdown("---")
    source_key = "mock" if source == "Datos de prueba" else "webhook"

    if st.session_state.deals is None:
        st.session_state.deals = load_deals_from_source(source=source_key, webhook_url=webhook_url)

    all_deals = st.session_state.deals
    vendedores = ["Todos"] + sorted(set(d["vendedor"] for d in all_deals))

    vendedor_sel = st.selectbox("Vendedor", vendedores)
    st.session_state.vendedor_sel = vendedor_sel

    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state.deals = load_deals_from_source(source=source_key, webhook_url=webhook_url)
        st.rerun()

    st.caption("Sincronizacion automatica cada hora")

# ── Filtrar deals ──────────────────────────────────────────────────────
deals = st.session_state.deals or []
if vendedor_sel != "Todos":
    deals = [d for d in deals if d["vendedor"] == vendedor_sel]

# ── Metricas ───────────────────────────────────────────────────────────
total = len(deals)
ganados = [d for d in deals if d["etapa"] == "Cierre ganado"]
perdidos = [d for d in deals if d["etapa"] == "Cierre perdido"]
activos  = [d for d in deals if d["etapa"] not in ("Cierre ganado", "Cierre perdido")]
valor    = sum(d["monto"] for d in deals if d["etapa"] != "Cierre perdido")

st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
  <div>
    <span style="font-size:20px; font-weight:700; color:#0f172a;">Pipeline de Ventas</span>
    <span style="font-size:13px; color:#64748b; margin-left:10px;">
      {"Todos los vendedores" if vendedor_sel == "Todos" else vendedor_sel}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Negocios", total)
m2.metric("Valor pipeline", f"${valor:,.0f}")
m3.metric("Activos", len(activos))
m4.metric("Ganados / Perdidos", f"{len(ganados)} / {len(perdidos)}")

st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)

# ── Kanban con drag & drop ─────────────────────────────────────────────
deals_json = json.dumps(deals, ensure_ascii=False)
stages_json = json.dumps(STAGES, ensure_ascii=False)

kanban_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}
  body {{ background: transparent; padding: 0; }}

  .board {{ display: flex; gap: 10px; align-items: flex-start; overflow-x: auto; padding-bottom: 12px; }}

  .column {{
    flex: 0 0 200px;
    min-width: 180px;
    background: #f8fafc;
    border-radius: 10px;
    padding: 0;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    border: 1px solid #e2e8f0;
  }}
  .column.drag-over {{ background: #eff6ff; border-color: #1A4ED8; }}

  .col-header {{
    padding: 10px 12px 8px;
    border-bottom: 1px solid #e2e8f0;
    display: flex;
    align-items: center;
    gap: 6px;
    border-radius: 10px 10px 0 0;
  }}
  .col-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}
  .col-title {{ font-size: 12px; font-weight: 600; color: #0f172a; flex:1; }}
  .col-count {{
    background: #e2e8f0; color: #475569;
    border-radius: 99px; padding: 1px 7px;
    font-size: 11px; font-weight: 600;
  }}

  .cards-area {{ padding: 8px; flex: 1; min-height: 60px; }}

  .card {{
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 7px;
    cursor: grab;
    transition: box-shadow 0.15s, border-color 0.15s;
    user-select: none;
  }}
  .card:hover {{ box-shadow: 0 2px 8px rgba(26,78,216,0.10); border-color: #bfdbfe; }}
  .card.dragging {{ opacity: 0.45; box-shadow: 0 4px 16px rgba(26,78,216,0.18); }}
  .card-name {{ font-size: 12px; font-weight: 600; color: #0f172a; margin-bottom: 2px; line-height:1.3; }}
  .card-company {{ font-size: 11px; color: #64748b; margin-bottom: 6px; }}
  .card-row {{ display:flex; justify-content:space-between; align-items:center; margin-top:4px; }}
  .card-amount {{ font-size: 12px; font-weight: 600; color: #1A4ED8; }}
  .card-prob {{ font-size: 10px; padding: 1px 7px; border-radius: 99px; font-weight:500; }}
  .card-prop {{ font-size: 10px; color: #94a3b8; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}

  .col-total {{ font-size:10px; color:#94a3b8; text-align:center; padding:6px 0 8px; border-top:1px solid #f1f5f9; }}

  /* Modal */
  .overlay {{
    display:none; position:fixed; top:0; left:0; right:0; bottom:0;
    background:rgba(15,23,42,0.45); z-index:1000; align-items:center; justify-content:center;
  }}
  .overlay.open {{ display:flex; }}
  .modal {{
    background:#fff; border-radius:14px; padding:24px;
    width:420px; max-width:95vw; max-height:90vh; overflow-y:auto;
    box-shadow: 0 20px 60px rgba(15,23,42,0.2);
    animation: popIn 0.18s ease;
  }}
  @keyframes popIn {{ from{{transform:scale(0.95);opacity:0}} to{{transform:scale(1);opacity:1}} }}
  .modal-header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:16px; }}
  .modal-title {{ font-size:16px; font-weight:700; color:#0f172a; line-height:1.3; flex:1; padding-right:12px; }}
  .modal-close {{
    width:28px; height:28px; border-radius:6px; border:none;
    background:#f1f5f9; color:#64748b; cursor:pointer; font-size:16px;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
  }}
  .modal-close:hover {{ background:#e2e8f0; }}
  .modal-stage-badge {{
    display:inline-block; font-size:11px; font-weight:600;
    padding:3px 10px; border-radius:99px; margin-bottom:16px;
  }}
  .modal-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px; }}
  .modal-field label {{ font-size:11px; color:#94a3b8; display:block; margin-bottom:3px; text-transform:uppercase; letter-spacing:0.04em; }}
  .modal-field span {{ font-size:13px; color:#0f172a; font-weight:500; }}
  .modal-field a {{ color:#1A4ED8; text-decoration:none; font-size:13px; font-weight:500; }}
  .modal-sep {{ border:none; border-top:1px solid #f1f5f9; margin:16px 0; }}
  .modal-label {{ font-size:12px; font-weight:600; color:#0f172a; margin-bottom:8px; }}
  .stage-select {{
    width:100%; padding:8px 10px; border:1px solid #e2e8f0; border-radius:7px;
    font-size:13px; color:#0f172a; background:#f8fafc; outline:none; margin-bottom:12px;
  }}
  .stage-select:focus {{ border-color:#1A4ED8; }}
  .btn-save {{
    width:100%; padding:9px; background:#1A4ED8; color:#fff;
    border:none; border-radius:8px; font-size:13px; font-weight:600;
    cursor:pointer; transition:background 0.15s;
  }}
  .btn-save:hover {{ background:#1e40af; }}
</style>
</head>
<body>

<div class="board" id="board"></div>

<div class="overlay" id="overlay">
  <div class="modal" id="modal">
    <div class="modal-header">
      <div class="modal-title" id="m-title"></div>
      <button class="modal-close" onclick="closeModal()">x</button>
    </div>
    <div id="m-badge" class="modal-stage-badge"></div>
    <div class="modal-grid">
      <div class="modal-field"><label>Empresa</label><span id="m-empresa"></span></div>
      <div class="modal-field"><label>Vendedor</label><span id="m-vendedor"></span></div>
      <div class="modal-field"><label>Correo</label><a id="m-correo" href="#"></a></div>
      <div class="modal-field"><label>Telefono</label><a id="m-tel" href="#"></a></div>
      <div class="modal-field"><label>Valor</label><span id="m-monto"></span></div>
      <div class="modal-field"><label>Probabilidad</label><span id="m-prob"></span></div>
      <div class="modal-field"><label>Fecha creacion</label><span id="m-created"></span></div>
      <div class="modal-field"><label>Cierre estimado</label><span id="m-close"></span></div>
    </div>
    <hr class="modal-sep">
    <div class="modal-label">Mover a etapa</div>
    <select class="stage-select" id="m-stage-sel"></select>
    <button class="btn-save" onclick="saveStage()">Guardar cambio</button>
  </div>
</div>

<script>
const STAGES = {stages_json};
const COLORS = {{
  "Asignado":              "#888780",
  "Visitado":              "#1A4ED8",
  "Interesado":            "#d97706",
  "Esperando Aprobacion":  "#7c3aed",
  "Cierre ganado":         "#059669",
  "Cierre perdido":        "#dc2626",
}};

let deals = {deals_json};
let draggedId = null;
let currentDealId = null;

function fmtUSD(n) {{
  if (n >= 1000000) return '$' + (n/1000000).toFixed(1) + 'M';
  if (n >= 1000) return '$' + Math.round(n/1000) + 'K';
  return '$' + n;
}}

function probStyle(p, etapa) {{
  if (etapa === 'Cierre ganado') return 'background:#d1fae5;color:#065f46';
  if (etapa === 'Cierre perdido') return 'background:#fee2e2;color:#991b1b';
  if (p >= 70) return 'background:#d1fae5;color:#065f46';
  if (p >= 40) return 'background:#fef3c7;color:#92400e';
  return 'background:#fee2e2;color:#991b1b';
}}

function buildBoard() {{
  const board = document.getElementById('board');
  board.innerHTML = '';

  STAGES.forEach(stage => {{
    const stageDeals = deals.filter(d => d.etapa === stage);
    const color = COLORS[stage] || '#888';
    const total = stageDeals.reduce((a,d) => a + d.monto, 0);

    const col = document.createElement('div');
    col.className = 'column';
    col.dataset.stage = stage;

    col.addEventListener('dragover', e => {{ e.preventDefault(); col.classList.add('drag-over'); }});
    col.addEventListener('dragleave', () => col.classList.remove('drag-over'));
    col.addEventListener('drop', e => {{
      e.preventDefault();
      col.classList.remove('drag-over');
      if (draggedId) {{
        const deal = deals.find(d => d.id === draggedId);
        if (deal) {{ deal.etapa = stage; buildBoard(); sendUpdate(); }}
      }}
    }});

    let cardsHTML = stageDeals.map(d => `
      <div class="card" draggable="true" data-id="${{d.id}}"
           ondragstart="onDragStart(event,'${{d.id}}')"
           ondragend="onDragEnd(event)"
           onclick="openModal('${{d.id}}')">
        <div class="card-name">${{d.nombre}}</div>
        <div class="card-company">${{d.empresa}}</div>
        <div class="card-prop">${{d.correo}}</div>
        <div class="card-prop">${{d.telefono}}</div>
        <div class="card-row">
          <span class="card-amount">${{fmtUSD(d.monto)}}</span>
          <span class="card-prob" style="${{probStyle(d.probabilidad, d.etapa)}}">${{d.probabilidad}}%</span>
        </div>
      </div>
    `).join('');

    col.innerHTML = `
      <div class="col-header">
        <span class="col-dot" style="background:${{color}}"></span>
        <span class="col-title">${{stage}}</span>
        <span class="col-count">${{stageDeals.length}}</span>
      </div>
      <div class="cards-area" data-stage="${{stage}}">${{cardsHTML}}</div>
      ${{stageDeals.length > 0 ? `<div class="col-total">Total: ${{fmtUSD(total)}}</div>` : ''}}
    `;

    board.appendChild(col);
  }});
}}

function onDragStart(e, id) {{
  draggedId = id;
  setTimeout(() => e.target.classList.add('dragging'), 0);
}}
function onDragEnd(e) {{
  e.target.classList.remove('dragging');
  draggedId = null;
}}

function openModal(id) {{
  const d = deals.find(x => x.id === id);
  if (!d) return;
  currentDealId = id;
  const color = COLORS[d.etapa] || '#888';

  document.getElementById('m-title').textContent = d.nombre;
  document.getElementById('m-badge').textContent = d.etapa;
  document.getElementById('m-badge').style = `background:${{color}}22; color:${{color}};`;
  document.getElementById('m-empresa').textContent = d.empresa;
  document.getElementById('m-vendedor').textContent = d.vendedor;
  document.getElementById('m-correo').textContent = d.correo;
  document.getElementById('m-correo').href = 'mailto:' + d.correo;
  document.getElementById('m-tel').textContent = d.telefono;
  document.getElementById('m-tel').href = 'tel:' + d.telefono;
  document.getElementById('m-monto').textContent = '$' + d.monto.toLocaleString('es-CL') + ' USD';
  document.getElementById('m-prob').textContent = d.probabilidad + '%';
  document.getElementById('m-created').textContent = d.fecha_creacion || '—';
  document.getElementById('m-close').textContent = d.fecha_cierre_est || '—';

  const sel = document.getElementById('m-stage-sel');
  sel.innerHTML = STAGES.map(s => `<option value="${{s}}" ${{s===d.etapa?'selected':''}}>${{s}}</option>`).join('');

  document.getElementById('overlay').classList.add('open');
}}

function closeModal() {{
  document.getElementById('overlay').classList.remove('open');
  currentDealId = null;
}}

function saveStage() {{
  const newStage = document.getElementById('m-stage-sel').value;
  const deal = deals.find(d => d.id === currentDealId);
  if (deal) {{ deal.etapa = newStage; buildBoard(); sendUpdate(); }}
  closeModal();
}}

function sendUpdate() {{
  window.parent.postMessage({{type:'streamlit:setComponentValue', value: JSON.stringify(deals)}}, '*');
}}

document.getElementById('overlay').addEventListener('click', e => {{
  if (e.target === document.getElementById('overlay')) closeModal();
}});

buildBoard();
</script>
</body>
</html>
"""

result = components.html(kanban_html, height=700, scrolling=True)

if result:
    try:
        updated = json.loads(result)
        st.session_state.deals = updated
    except Exception:
        pass
