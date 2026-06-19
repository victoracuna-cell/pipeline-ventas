import streamlit as st
import streamlit.components.v1 as components
import json
import requests
from pathlib import Path

st.set_page_config(
    page_title="Pipeline TUU",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Autenticación ─────────────────────────────────────────────────────
def check_login():
    usuarios = st.secrets.get("usuarios", {})

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    if not st.session_state.logged_in:
        col_left, col_center, col_right = st.columns([1, 1.2, 1])
        with col_center:
            st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
            st.markdown("""
                <div style="text-align:center; margin-bottom:28px;">
                    <span style="font-size:36px; font-weight:800; color:#1A4ED8; letter-spacing:-1px;">TUU</span>
                    <div style="font-size:14px; color:#64748b; margin-top:4px;">Pipeline de Ventas en Terreno</div>
                </div>
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                correo = st.text_input("Correo", placeholder="tu@tuu.cl")
                clave  = st.text_input("Contrasena", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary")

                if submit:
                    if correo in usuarios and usuarios[correo] == clave:
                        st.session_state.logged_in = True
                        st.session_state.usuario = correo
                        st.session_state.login_error = False
                        st.rerun()
                    else:
                        st.session_state.login_error = True

            if st.session_state.login_error:
                st.error("Correo o contrasena incorrectos.")

        st.stop()

check_login()

# ── App principal (solo si está autenticado) ──────────────────────────

STAGES = [
    "Asignado",
    "Visitado",
    "Interesado",
    "Esperando Aprobacion",
    "Cierre ganado",
    "Cierre perdido",
]

@st.cache_data(ttl=3600)
def load_deals_from_source(source="mock", webhook_url=""):
    if source == "webhook" and webhook_url:
        try:
            res = requests.get(webhook_url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            st.warning(f"No se pudo conectar ({e}). Usando datos de prueba.")
    data_path = Path(__file__).parent / "deals.json"
    with open(data_path, encoding="utf-8") as f:
        return json.load(f)

if "deals" not in st.session_state:
    st.session_state.deals = None

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:8px 0 16px;">
            <span style="font-size:22px;font-weight:700;color:#1A4ED8;">TUU</span>
            <span style="font-size:14px;color:#64748b;margin-left:6px;">Pipeline Terreno</span>
        </div>
    """, unsafe_allow_html=True)

    st.caption(f"Sesion: {st.session_state.get('usuario','')}")
    if st.button("Cerrar sesion", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.usuario = ""
        st.session_state.deals = None
        st.rerun()

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

    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.session_state.deals = load_deals_from_source(source=source_key, webhook_url=webhook_url)
        st.rerun()
    st.caption("Sincronizacion automatica cada hora")

# ── Filtrar ───────────────────────────────────────────────────────────
deals = st.session_state.deals or []
if vendedor_sel != "Todos":
    deals = [d for d in deals if d["vendedor"] == vendedor_sel]

# ── Metricas ──────────────────────────────────────────────────────────
ganados = [d for d in deals if d["etapa"] == "Cierre ganado"]
perdidos = [d for d in deals if d["etapa"] == "Cierre perdido"]
activos  = [d for d in deals if d["etapa"] not in ("Cierre ganado", "Cierre perdido")]
valor    = sum(d["monto"] for d in deals if d["etapa"] != "Cierre perdido")

st.markdown("""
    <div style="margin-bottom:4px;">
        <span style="font-size:20px;font-weight:700;color:#0f172a;">Pipeline de Ventas en Terreno</span>
    </div>
""", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Negocios", len(deals))
m2.metric("Valor pipeline", f"${valor:,.0f}")
m3.metric("Activos", len(activos))
m4.metric("Ganados / Perdidos", f"{len(ganados)} / {len(perdidos)}")

st.markdown("<div style='margin-bottom:12px'></div>", unsafe_allow_html=True)

# ── Kanban ────────────────────────────────────────────────────────────
deals_json = json.dumps(deals, ensure_ascii=False)
stages_json = json.dumps(STAGES, ensure_ascii=False)

kanban_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }}
  body {{ background:transparent; }}
  .board {{ display:flex; gap:10px; align-items:flex-start; overflow-x:auto; padding-bottom:12px; min-height:400px; }}
  .column {{
    flex:0 0 195px; min-width:175px; background:#f8fafc;
    border-radius:10px; border:1px solid #e2e8f0;
    display:flex; flex-direction:column; min-height:300px;
  }}
  .column.drag-over {{ background:#eff6ff; border-color:#1A4ED8; }}
  .col-header {{
    padding:10px 12px 8px; border-bottom:1px solid #e2e8f0;
    border-radius:10px 10px 0 0; display:flex; align-items:center; gap:6px;
  }}
  .col-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}
  .col-title {{ font-size:11px; font-weight:700; color:#0f172a; flex:1; text-transform:uppercase; letter-spacing:0.03em; }}
  .col-count {{ background:#e2e8f0; color:#475569; border-radius:99px; padding:1px 7px; font-size:11px; font-weight:600; }}
  .cards-area {{ padding:8px; flex:1; min-height:60px; }}
  .card {{
    background:#fff; border:1px solid #e2e8f0; border-radius:8px;
    padding:10px 12px; margin-bottom:7px; cursor:grab;
    transition:box-shadow 0.15s, border-color 0.15s; user-select:none;
  }}
  .card:hover {{ box-shadow:0 2px 8px rgba(26,78,216,0.10); border-color:#bfdbfe; }}
  .card.dragging {{ opacity:0.4; }}
  .card-name {{ font-size:12px; font-weight:700; color:#0f172a; margin-bottom:1px; }}
  .card-negocio {{ font-size:11px; color:#1A4ED8; font-weight:600; margin-bottom:4px; }}
  .card-prop {{ font-size:10px; color:#94a3b8; margin-bottom:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .card-row {{ display:flex; justify-content:space-between; align-items:center; margin-top:6px; }}
  .card-amount {{ font-size:12px; font-weight:700; color:#0f172a; }}
  .card-badge {{ font-size:10px; padding:2px 7px; border-radius:99px; font-weight:600; }}
  .card-location {{ font-size:10px; color:#cbd5e1; margin-top:3px; }}
  .col-total {{ font-size:10px; color:#94a3b8; text-align:center; padding:5px 0 8px; border-top:1px solid #f1f5f9; }}
  .overlay {{
    display:none; position:fixed; top:0; left:0; right:0; bottom:0;
    background:rgba(15,23,42,0.5); z-index:1000; align-items:center; justify-content:center;
  }}
  .overlay.open {{ display:flex; }}
  .modal {{
    background:#fff; border-radius:14px; padding:24px;
    width:480px; max-width:96vw; max-height:88vh; overflow-y:auto;
    box-shadow:0 24px 64px rgba(15,23,42,0.22); animation:popIn 0.16s ease;
  }}
  @keyframes popIn {{ from{{transform:scale(0.96);opacity:0}} to{{transform:scale(1);opacity:1}} }}
  .modal-top {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px; }}
  .modal-title {{ font-size:17px; font-weight:700; color:#0f172a; flex:1; padding-right:12px; line-height:1.3; }}
  .modal-close {{
    width:28px; height:28px; border-radius:6px; border:none;
    background:#f1f5f9; color:#64748b; cursor:pointer; font-size:15px;
    display:flex; align-items:center; justify-content:center; flex-shrink:0;
  }}
  .modal-close:hover {{ background:#e2e8f0; color:#0f172a; }}
  .modal-negocio {{ font-size:13px; color:#1A4ED8; font-weight:600; margin-bottom:8px; }}
  .modal-badge {{ display:inline-block; font-size:11px; font-weight:700; padding:3px 10px; border-radius:99px; margin-bottom:16px; }}
  .section-title {{
    font-size:10px; font-weight:700; color:#94a3b8; text-transform:uppercase;
    letter-spacing:0.06em; margin:16px 0 10px; padding-bottom:6px; border-bottom:1px solid #f1f5f9;
  }}
  .modal-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  .mf label {{ font-size:10px; color:#94a3b8; display:block; margin-bottom:2px; text-transform:uppercase; letter-spacing:0.04em; }}
  .mf span {{ font-size:13px; color:#0f172a; font-weight:500; }}
  .mf a {{ color:#1A4ED8; text-decoration:none; font-size:13px; font-weight:500; }}
  .mf.full {{ grid-column:1/-1; }}
  .nivel-badge {{ display:inline-block; font-size:11px; font-weight:600; padding:2px 9px; border-radius:99px; }}
  .nivel-Alto {{ background:#d1fae5; color:#065f46; }}
  .nivel-Medio {{ background:#fef3c7; color:#92400e; }}
  .nivel-Bajo {{ background:#fee2e2; color:#991b1b; }}
  .stage-label {{ font-size:12px; font-weight:600; color:#0f172a; margin:16px 0 8px; }}
  .stage-select {{
    width:100%; padding:8px 10px; border:1px solid #e2e8f0; border-radius:7px;
    font-size:13px; color:#0f172a; background:#f8fafc; outline:none; margin-bottom:12px;
  }}
  .stage-select:focus {{ border-color:#1A4ED8; }}
  .btn-save {{
    width:100%; padding:10px; background:#1A4ED8; color:#fff;
    border:none; border-radius:8px; font-size:13px; font-weight:700;
    cursor:pointer; transition:background 0.15s;
  }}
  .btn-save:hover {{ background:#1e40af; }}
</style>
</head>
<body>
<div class="board" id="board"></div>
<div class="overlay" id="overlay">
  <div class="modal">
    <div class="modal-top">
      <div class="modal-title" id="m-title"></div>
      <button class="modal-close" onclick="closeModal()">&#x2715;</button>
    </div>
    <div class="modal-negocio" id="m-negocio"></div>
    <div id="m-badge" class="modal-badge"></div>
    <div class="section-title">Contacto</div>
    <div class="modal-grid">
      <div class="mf"><label>Nombre</label><span id="m-nombre"></span></div>
      <div class="mf"><label>Apellido</label><span id="m-apellido"></span></div>
      <div class="mf"><label>Correo</label><a id="m-correo" href="#"></a></div>
      <div class="mf"><label>Telefono</label><a id="m-tel" href="#"></a></div>
    </div>
    <div class="section-title">Negocio</div>
    <div class="modal-grid">
      <div class="mf full"><label>Nombre del negocio</label><span id="m-negnombre"></span></div>
      <div class="mf full"><label>Descripcion</label><span id="m-desc"></span></div>
      <div class="mf"><label>Nivel de venta</label><span id="m-nivel"></span></div>
      <div class="mf"><label>Resultado visita</label><span id="m-resultado"></span></div>
    </div>
    <div class="section-title">Ubicacion</div>
    <div class="modal-grid">
      <div class="mf full"><label>Direccion</label><span id="m-dir"></span></div>
      <div class="mf"><label>Ciudad</label><span id="m-ciudad"></span></div>
      <div class="mf"><label>Comuna</label><span id="m-comuna"></span></div>
      <div class="mf full"><label>Region</label><span id="m-region"></span></div>
    </div>
    <div class="section-title">Negociacion</div>
    <div class="modal-grid">
      <div class="mf"><label>Vendedor</label><span id="m-vendedor"></span></div>
      <div class="mf"><label>Valor</label><span id="m-monto"></span></div>
      <div class="mf"><label>Probabilidad</label><span id="m-prob"></span></div>
      <div class="mf"><label>Cierre estimado</label><span id="m-close"></span></div>
      <div class="mf"><label>Fecha creacion</label><span id="m-created"></span></div>
    </div>
    <div class="stage-label">Mover a etapa</div>
    <select class="stage-select" id="m-stage-sel"></select>
    <button class="btn-save" onclick="saveStage()">Guardar cambio</button>
  </div>
</div>
<script>
const STAGES = {stages_json};
const COLORS = {{
  "Asignado":"#888780","Visitado":"#1A4ED8","Interesado":"#d97706",
  "Esperando Aprobacion":"#7c3aed","Cierre ganado":"#059669","Cierre perdido":"#dc2626"
}};
let deals = {deals_json};
let draggedId = null, currentDealId = null;
function fmtUSD(n) {{
  if (n>=1000000) return '$'+(n/1000000).toFixed(1)+'M';
  if (n>=1000) return '$'+Math.round(n/1000)+'K';
  return '$'+n;
}}
function probStyle(p,etapa) {{
  if (etapa==='Cierre ganado') return 'background:#d1fae5;color:#065f46';
  if (etapa==='Cierre perdido') return 'background:#fee2e2;color:#991b1b';
  if (p>=70) return 'background:#d1fae5;color:#065f46';
  if (p>=40) return 'background:#fef3c7;color:#92400e';
  return 'background:#fee2e2;color:#991b1b';
}}
function buildBoard() {{
  const board = document.getElementById('board');
  board.innerHTML = '';
  STAGES.forEach(stage => {{
    const sd = deals.filter(d => d.etapa===stage);
    const color = COLORS[stage]||'#888';
    const total = sd.reduce((a,d)=>a+d.monto,0);
    const col = document.createElement('div');
    col.className='column'; col.dataset.stage=stage;
    col.addEventListener('dragover',e=>{{e.preventDefault();col.classList.add('drag-over');}});
    col.addEventListener('dragleave',()=>col.classList.remove('drag-over'));
    col.addEventListener('drop',e=>{{
      e.preventDefault();col.classList.remove('drag-over');
      if(draggedId){{const deal=deals.find(d=>d.id===draggedId);if(deal){{deal.etapa=stage;buildBoard();sendUpdate();}}}}
    }});
    const cards=sd.map(d=>`
      <div class="card" draggable="true" data-id="${{d.id}}"
           ondragstart="onDragStart(event,'${{d.id}}')" ondragend="onDragEnd(event)"
           onclick="openModal('${{d.id}}')">
        <div class="card-name">${{d.nombre}} ${{d.apellido}}</div>
        <div class="card-negocio">${{d.nombre_negocio}}</div>
        <div class="card-prop">${{d.correo}}</div>
        <div class="card-prop">${{d.telefono}}</div>
        <div class="card-location">${{d.comuna}}, ${{d.ciudad}}</div>
        <div class="card-row">
          <span class="card-amount">${{fmtUSD(d.monto)}}</span>
          <span class="card-badge" style="${{probStyle(d.probabilidad,d.etapa)}}">${{d.probabilidad}}%</span>
        </div>
      </div>`).join('');
    col.innerHTML=`
      <div class="col-header">
        <span class="col-dot" style="background:${{color}}"></span>
        <span class="col-title">${{stage}}</span>
        <span class="col-count">${{sd.length}}</span>
      </div>
      <div class="cards-area">${{cards}}</div>
      ${{sd.length>0?`<div class="col-total">Total: ${{fmtUSD(total)}}</div>`:''}}`;
    board.appendChild(col);
  }});
}}
function onDragStart(e,id){{draggedId=id;setTimeout(()=>{{const el=document.querySelector(`[data-id="${{id}}"]`);if(el)el.classList.add('dragging');}},0);}}
function onDragEnd(e){{e.target.classList.remove('dragging');draggedId=null;}}
function openModal(id){{
  const d=deals.find(x=>x.id===id); if(!d) return;
  currentDealId=id;
  const color=COLORS[d.etapa]||'#888';
  document.getElementById('m-title').textContent=d.nombre+' '+d.apellido;
  document.getElementById('m-negocio').textContent=d.nombre_negocio;
  document.getElementById('m-badge').textContent=d.etapa;
  document.getElementById('m-badge').style.cssText=`background:${{color}}22;color:${{color}};`;
  document.getElementById('m-nombre').textContent=d.nombre;
  document.getElementById('m-apellido').textContent=d.apellido;
  document.getElementById('m-correo').textContent=d.correo;
  document.getElementById('m-correo').href='mailto:'+d.correo;
  document.getElementById('m-tel').textContent=d.telefono;
  document.getElementById('m-tel').href='tel:'+d.telefono;
  document.getElementById('m-negnombre').textContent=d.nombre_negocio;
  document.getElementById('m-desc').textContent=d.descripcion_negocio||'—';
  document.getElementById('m-nivel').innerHTML=`<span class="nivel-badge nivel-${{d.nivel_venta}}">${{d.nivel_venta}}</span>`;
  document.getElementById('m-resultado').textContent=d.resultado_visita||'—';
  document.getElementById('m-dir').textContent=(d.calle||'')+' '+(d.numero||'');
  document.getElementById('m-ciudad').textContent=d.ciudad||'—';
  document.getElementById('m-comuna').textContent=d.comuna||'—';
  document.getElementById('m-region').textContent=d.region||'—';
  document.getElementById('m-vendedor').textContent=d.vendedor;
  document.getElementById('m-monto').textContent='$'+(d.monto||0).toLocaleString('es-CL')+' USD';
  document.getElementById('m-prob').textContent=d.probabilidad+'%';
  document.getElementById('m-close').textContent=d.fecha_cierre_est||'—';
  document.getElementById('m-created').textContent=d.fecha_creacion||'—';
  const sel=document.getElementById('m-stage-sel');
  sel.innerHTML=STAGES.map(s=>`<option value="${{s}}" ${{s===d.etapa?'selected':''}}>${{s}}</option>`).join('');
  document.getElementById('overlay').classList.add('open');
}}
function closeModal(){{document.getElementById('overlay').classList.remove('open');currentDealId=null;}}
function saveStage(){{
  const ns=document.getElementById('m-stage-sel').value;
  const deal=deals.find(d=>d.id===currentDealId);
  if(deal){{deal.etapa=ns;buildBoard();sendUpdate();}}
  closeModal();
}}
function sendUpdate(){{window.parent.postMessage({{type:'streamlit:setComponentValue',value:JSON.stringify(deals)}},'*');}}
document.getElementById('overlay').addEventListener('click',e=>{{if(e.target.id==='overlay')closeModal();}});
buildBoard();
</script>
</body>
</html>
"""

result = components.html(kanban_html, height=720, scrolling=True)
if result:
    try:
        updated = json.loads(result)
        st.session_state.deals = updated
    except Exception:
        pass
