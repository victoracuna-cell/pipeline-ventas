import streamlit as st
import streamlit.components.v1 as components
import json
import requests
from pathlib import Path

st.set_page_config(page_title="Pipeline TUU", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #f9fafb; }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #f0f0f0; }
    [data-testid="stSidebar"] * { color: #0f172a !important; }
    .stMetric { background: #ffffff; border: 1px solid #f0f0f0; border-radius: 12px; padding: 16px 20px; }
    .stMetric label { color: #94a3b8 !important; font-size: 12px !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.05em; }
    .stMetric [data-testid="stMetricValue"] { color: #0f172a !important; font-size: 28px !important; font-weight: 700 !important; }
    div[data-testid="column"] { padding: 0 6px !important; }
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    #MainMenu, footer, header { visibility: hidden; }
    .stRadio label { font-size: 13px !important; }
    .stButton button {
        background: #ffffff !important; border: 1px solid #e2e8f0 !important;
        color: #0f172a !important; font-size: 13px !important; font-weight: 500 !important;
        border-radius: 8px !important; padding: 6px 12px !important;
    }
    .stButton button:hover { background: #f8fafc !important; border-color: #cbd5e1 !important; }
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
            [data-testid="stAppViewContainer"] { background: #ffffff; }
            [data-testid="stSidebar"] { display: none; }
        </style>
        """, unsafe_allow_html=True)

        _, col, _ = st.columns([1, 1, 1])
        with col:
            st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
            st.markdown("""
                <div style='text-align:center; margin-bottom:40px;'>
                    <div style='font-size:40px; font-weight:800; color:#1A4ED8; letter-spacing:-2px; line-height:1;'>TUU</div>
                    <div style='font-size:13px; color:#94a3b8; margin-top:6px; letter-spacing:0.05em; text-transform:uppercase;'>Pipeline de Ventas</div>
                </div>
            """, unsafe_allow_html=True)

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
                st.markdown("<div style='text-align:center; color:#ef4444; font-size:13px; margin-top:8px;'>Correo o contrasena incorrectos</div>", unsafe_allow_html=True)
        st.stop()

check_login()

STAGES = ["Asignado","Visitado","Interesado","Esperando Aprobacion","Cierre ganado","Cierre perdido"]

@st.cache_data(ttl=3600)
def load_deals(source="mock", webhook_url=""):
    if source == "webhook" and webhook_url:
        try:
            r = requests.get(webhook_url, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            st.warning(f"Error conectando webhook: {e}")
    return json.loads((Path(__file__).parent / "deals.json").read_text(encoding="utf-8"))

if "deals" not in st.session_state:
    st.session_state.deals = None

vendedor_activo = st.session_state.get("vendedor", "")

# ── Sidebar ───────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
        <div style='padding:8px 0 24px;'>
            <span style='font-size:24px;font-weight:800;color:#1A4ED8;letter-spacing:-1px;'>TUU</span>
        </div>
        <div style='margin-bottom:24px;'>
            <div style='font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;'>Vendedor</div>
            <div style='font-size:15px;font-weight:700;color:#0f172a;'>{vendedor_activo}</div>
            <div style='font-size:12px;color:#94a3b8;margin-top:2px;'>{st.session_state.get("usuario","")}</div>
        </div>
        <div style='height:1px;background:#f0f0f0;margin-bottom:20px;'></div>
    """, unsafe_allow_html=True)

    source = st.radio("Datos", ["Prueba", "Webhook n8n"], label_visibility="collapsed")
    webhook_url = ""
    if source == "Webhook n8n":
        webhook_url = st.text_input("URL", placeholder="https://n8n.../webhook/pipeline")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    source_key = "mock" if source == "Prueba" else "webhook"

    if st.session_state.deals is None:
        st.session_state.deals = load_deals(source_key, webhook_url)

    if st.button("Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.session_state.deals = load_deals(source_key, webhook_url)
        st.rerun()

    st.markdown("""
        <div style='height:1px;background:#f0f0f0;margin:20px 0;'></div>
        <div style='font-size:11px;color:#cbd5e1;'>Sync automatico cada hora</div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    if st.button("Cerrar sesion", use_container_width=True):
        for k in ["logged_in","usuario","vendedor","deals","login_error"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Data ──────────────────────────────────────────────────────────────
deals = [d for d in (st.session_state.deals or []) if d.get("vendedor") == vendedor_activo]
ganados = [d for d in deals if d["etapa"] == "Cierre ganado"]
perdidos = [d for d in deals if d["etapa"] == "Cierre perdido"]
activos  = [d for d in deals if d["etapa"] not in ("Cierre ganado","Cierre perdido")]
valor    = sum(d["monto"] for d in deals if d["etapa"] != "Cierre perdido")

# ── Header ────────────────────────────────────────────────────────────
st.markdown(f"""
    <div style='margin-bottom:24px;'>
        <div style='font-size:22px;font-weight:700;color:#0f172a;letter-spacing:-0.5px;'>Mis negocios</div>
        <div style='font-size:13px;color:#94a3b8;margin-top:2px;'>{vendedor_activo}</div>
    </div>
""", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns(4)
c1.metric("Negocios", len(deals))
c2.metric("Valor activo", f"${valor:,.0f}")
c3.metric("En curso", len(activos))
c4.metric("Ganados", len(ganados))

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Kanban ────────────────────────────────────────────────────────────
deals_json  = json.dumps(deals, ensure_ascii=False)
stages_json = json.dumps(STAGES, ensure_ascii=False)

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}

.board{{display:flex;gap:12px;overflow-x:auto;padding-bottom:16px;align-items:flex-start;}}

.col{{
  flex:0 0 190px;min-width:170px;
  background:#ffffff;
  border:1px solid #f0f0f0;
  border-radius:12px;
  display:flex;flex-direction:column;
  min-height:280px;
  transition:border-color 0.15s;
}}
.col.over{{border-color:#1A4ED8;background:#f8fbff;}}

.col-head{{
  display:flex;align-items:center;gap:8px;
  padding:12px 14px 10px;
  border-bottom:1px solid #f8f8f8;
}}
.dot{{width:6px;height:6px;border-radius:50%;flex-shrink:0;}}
.col-name{{font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;flex:1;}}
.col-n{{font-size:11px;font-weight:600;color:#cbd5e1;}}

.cards{{padding:8px;flex:1;}}

.card{{
  background:#ffffff;
  border:1px solid #f0f0f0;
  border-radius:10px;
  padding:12px;
  margin-bottom:8px;
  cursor:grab;
  transition:box-shadow 0.15s,border-color 0.15s;
  user-select:none;
}}
.card:hover{{box-shadow:0 4px 16px rgba(0,0,0,0.06);border-color:#e2e8f0;}}
.card.dragging{{opacity:0.35;box-shadow:0 8px 24px rgba(26,78,216,0.15);}}

.c-contact{{font-size:13px;font-weight:600;color:#0f172a;margin-bottom:1px;line-height:1.3;}}
.c-biz{{font-size:11px;color:#1A4ED8;font-weight:500;margin-bottom:8px;}}
.c-info{{font-size:10px;color:#cbd5e1;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.c-loc{{font-size:10px;color:#e2e8f0;margin-top:4px;}}
.c-bottom{{display:flex;justify-content:space-between;align-items:center;margin-top:10px;padding-top:8px;border-top:1px solid #f8f8f8;}}
.c-amt{{font-size:12px;font-weight:700;color:#0f172a;}}
.c-prob{{font-size:10px;font-weight:600;padding:2px 7px;border-radius:6px;}}

.col-foot{{font-size:10px;color:#e2e8f0;text-align:center;padding:8px;border-top:1px solid #f8f8f8;}}
.empty{{text-align:center;padding:20px 8px;color:#e2e8f0;font-size:11px;}}

/* Modal */
.ov{{display:none;position:fixed;inset:0;background:rgba(15,23,42,0.4);z-index:999;align-items:center;justify-content:center;backdrop-filter:blur(2px);}}
.ov.open{{display:flex;}}
.modal{{
  background:#fff;border-radius:16px;width:460px;max-width:94vw;
  max-height:86vh;overflow-y:auto;
  box-shadow:0 32px 80px rgba(15,23,42,0.18);
  animation:up 0.18s ease;
}}
@keyframes up{{from{{transform:translateY(12px);opacity:0}}to{{transform:none;opacity:1}}}}

.mh{{padding:20px 20px 0;display:flex;justify-content:space-between;align-items:flex-start;}}
.m-name{{font-size:18px;font-weight:700;color:#0f172a;line-height:1.3;flex:1;padding-right:12px;}}
.m-close{{width:28px;height:28px;border-radius:8px;border:1px solid #f0f0f0;background:#f8fafc;cursor:pointer;font-size:14px;color:#94a3b8;display:flex;align-items:center;justify-content:center;flex-shrink:0;}}
.m-close:hover{{background:#f0f0f0;color:#0f172a;}}
.m-biz{{padding:4px 20px 0;font-size:13px;color:#1A4ED8;font-weight:600;}}
.m-stage{{display:inline-flex;align-items:center;margin:10px 20px 0;font-size:11px;font-weight:700;padding:4px 10px;border-radius:6px;}}

.mb{{padding:0 20px;}}
.sec{{font-size:10px;font-weight:700;color:#cbd5e1;text-transform:uppercase;letter-spacing:0.07em;margin:20px 0 10px;padding-bottom:8px;border-bottom:1px solid #f8f8f8;}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;}}
.f label{{font-size:10px;color:#94a3b8;display:block;margin-bottom:3px;text-transform:uppercase;letter-spacing:0.04em;}}
.f span,.f a{{font-size:13px;color:#0f172a;font-weight:500;display:block;}}
.f a{{color:#1A4ED8;text-decoration:none;}}
.f.full{{grid-column:1/-1;}}

.nivel{{display:inline-block;font-size:11px;font-weight:600;padding:3px 9px;border-radius:6px;}}
.n-Alto{{background:#f0fdf4;color:#16a34a;}}
.n-Medio{{background:#fffbeb;color:#d97706;}}
.n-Bajo{{background:#fef2f2;color:#dc2626;}}

.mf{{padding:20px;padding-top:16px;}}
.stage-sel{{
  width:100%;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;
  font-size:13px;color:#0f172a;background:#f8fafc;outline:none;margin-bottom:12px;
  appearance:none;
}}
.stage-sel:focus{{border-color:#1A4ED8;}}
.btn{{
  width:100%;padding:11px;background:#1A4ED8;color:#fff;
  border:none;border-radius:10px;font-size:13px;font-weight:700;
  cursor:pointer;letter-spacing:0.01em;transition:background 0.15s;
}}
.btn:hover{{background:#1e40af;}}
</style></head><body>
<div class="board" id="board"></div>
<div class="ov" id="ov">
  <div class="modal">
    <div class="mh">
      <div class="m-name" id="m-name"></div>
      <button class="m-close" onclick="closeM()">&#x2715;</button>
    </div>
    <div class="m-biz" id="m-biz"></div>
    <div id="m-stage" class="m-stage"></div>
    <div class="mb">
      <div class="sec">Contacto</div>
      <div class="grid">
        <div class="f"><label>Nombre</label><span id="m-nombre"></span></div>
        <div class="f"><label>Apellido</label><span id="m-apellido"></span></div>
        <div class="f"><label>Correo</label><a id="m-correo" href="#"></a></div>
        <div class="f"><label>Telefono</label><a id="m-tel" href="#"></a></div>
      </div>
      <div class="sec">Negocio</div>
      <div class="grid">
        <div class="f full"><label>Nombre del negocio</label><span id="m-negnombre"></span></div>
        <div class="f full"><label>Descripcion</label><span id="m-desc"></span></div>
        <div class="f"><label>Nivel de venta</label><span id="m-nivel"></span></div>
        <div class="f"><label>Resultado visita</label><span id="m-resultado"></span></div>
      </div>
      <div class="sec">Ubicacion</div>
      <div class="grid">
        <div class="f full"><label>Direccion</label><span id="m-dir"></span></div>
        <div class="f"><label>Comuna</label><span id="m-comuna"></span></div>
        <div class="f"><label>Ciudad</label><span id="m-ciudad"></span></div>
        <div class="f full"><label>Region</label><span id="m-region"></span></div>
      </div>
      <div class="sec">Negociacion</div>
      <div class="grid">
        <div class="f"><label>Valor</label><span id="m-monto"></span></div>
        <div class="f"><label>Probabilidad</label><span id="m-prob"></span></div>
        <div class="f"><label>Fecha creacion</label><span id="m-created"></span></div>
        <div class="f"><label>Cierre estimado</label><span id="m-close"></span></div>
      </div>
    </div>
    <div class="mf">
      <div style="font-size:12px;font-weight:600;color:#0f172a;margin-bottom:8px;">Mover a etapa</div>
      <select class="stage-sel" id="m-sel"></select>
      <button class="btn" onclick="saveStage()">Guardar cambio</button>
    </div>
  </div>
</div>
<script>
const STAGES={stages_json};
const C={{"Asignado":"#94a3b8","Visitado":"#1A4ED8","Interesado":"#d97706","Esperando Aprobacion":"#7c3aed","Cierre ganado":"#059669","Cierre perdido":"#dc2626"}};
let deals={deals_json},dragId=null,curId=null;

function fmt(n){{if(n>=1e6)return'$'+(n/1e6).toFixed(1)+'M';if(n>=1e3)return'$'+Math.round(n/1e3)+'K';return'$'+n;}}
function pStyle(p,e){{
  if(e==='Cierre ganado')return'background:#f0fdf4;color:#16a34a';
  if(e==='Cierre perdido')return'background:#fef2f2;color:#dc2626';
  if(p>=70)return'background:#f0fdf4;color:#16a34a';
  if(p>=40)return'background:#fffbeb;color:#d97706';
  return'background:#fef2f2;color:#dc2626';
}}

function build(){{
  const b=document.getElementById('board');b.innerHTML='';
  STAGES.forEach(s=>{{
    const sd=deals.filter(d=>d.etapa===s),col=COLORS(s),total=sd.reduce((a,d)=>a+d.monto,0);
    const el=document.createElement('div');el.className='col';el.dataset.stage=s;
    el.addEventListener('dragover',e=>{{e.preventDefault();el.classList.add('over');}});
    el.addEventListener('dragleave',()=>el.classList.remove('over'));
    el.addEventListener('drop',e=>{{
      e.preventDefault();el.classList.remove('over');
      if(dragId){{const d=deals.find(x=>x.id===dragId);if(d){{d.etapa=s;build();send();}}}}
    }});
    const cards=sd.map(d=>`
      <div class="card" draggable="true" data-id="${{d.id}}"
        ondragstart="ds(event,'${{d.id}}')" ondragend="de(event)" onclick="openM('${{d.id}}')">
        <div class="c-contact">${{d.nombre}} ${{d.apellido}}</div>
        <div class="c-biz">${{d.nombre_negocio}}</div>
        <div class="c-info">${{d.correo}}</div>
        <div class="c-info">${{d.telefono}}</div>
        <div class="c-loc">${{d.comuna}}, ${{d.ciudad}}</div>
        <div class="c-bottom">
          <span class="c-amt">${{fmt(d.monto)}}</span>
          <span class="c-prob" style="${{pStyle(d.probabilidad,d.etapa)}}">${{d.probabilidad}}%</span>
        </div>
      </div>`).join('');
    el.innerHTML=`
      <div class="col-head">
        <span class="dot" style="background:${{col}}"></span>
        <span class="col-name">${{s}}</span>
        <span class="col-n">${{sd.length}}</span>
      </div>
      <div class="cards">${{cards||'<div class="empty">Sin negocios</div>'}}</div>
      ${{sd.length?`<div class="col-foot">${{fmt(total)}}</div>`:''}}`;
    b.appendChild(el);
  }});
}}

function COLORS(s){{return C[s]||'#94a3b8';}}
function ds(e,id){{dragId=id;setTimeout(()=>{{const el=document.querySelector(`[data-id="${{id}}"]`);if(el)el.classList.add('dragging');}},0);}}
function de(e){{e.target.classList.remove('dragging');dragId=null;}}

function openM(id){{
  const d=deals.find(x=>x.id===id);if(!d)return;curId=id;
  const col=COLORS(d.etapa);
  document.getElementById('m-name').textContent=d.nombre+' '+d.apellido;
  document.getElementById('m-biz').textContent=d.nombre_negocio;
  const sb=document.getElementById('m-stage');
  sb.textContent=d.etapa;sb.style.cssText=`background:${{col}}18;color:${{col}};border:1px solid ${{col}}30;`;
  document.getElementById('m-nombre').textContent=d.nombre;
  document.getElementById('m-apellido').textContent=d.apellido;
  const mc=document.getElementById('m-correo');mc.textContent=d.correo;mc.href='mailto:'+d.correo;
  const mt=document.getElementById('m-tel');mt.textContent=d.telefono;mt.href='tel:'+d.telefono;
  document.getElementById('m-negnombre').textContent=d.nombre_negocio;
  document.getElementById('m-desc').textContent=d.descripcion_negocio||'—';
  document.getElementById('m-nivel').innerHTML=`<span class="nivel n-${{d.nivel_venta}}">${{d.nivel_venta}}</span>`;
  document.getElementById('m-resultado').textContent=d.resultado_visita||'—';
  document.getElementById('m-dir').textContent=(d.calle||'')+' '+(d.numero||'');
  document.getElementById('m-comuna').textContent=d.comuna||'—';
  document.getElementById('m-ciudad').textContent=d.ciudad||'—';
  document.getElementById('m-region').textContent=d.region||'—';
  document.getElementById('m-monto').textContent='$'+(d.monto||0).toLocaleString('es-CL')+' USD';
  document.getElementById('m-prob').textContent=d.probabilidad+'%';
  document.getElementById('m-created').textContent=d.fecha_creacion||'—';
  document.getElementById('m-close').textContent=d.fecha_cierre_est||'—';
  document.getElementById('m-sel').innerHTML=STAGES.map(s=>`<option value="${{s}}" ${{s===d.etapa?'selected':''}}>${{s}}</option>`).join('');
  document.getElementById('ov').classList.add('open');
}}
function closeM(){{document.getElementById('ov').classList.remove('open');curId=null;}}
function saveStage(){{
  const ns=document.getElementById('m-sel').value;
  const d=deals.find(x=>x.id===curId);if(d){{d.etapa=ns;build();send();}}closeM();
}}
function send(){{window.parent.postMessage({{type:'streamlit:setComponentValue',value:JSON.stringify(deals)}},'*');}}
document.getElementById('ov').addEventListener('click',e=>{{if(e.target.id==='ov')closeM();}});
build();
</script></body></html>"""

result = components.html(html, height=700, scrolling=True)
if result:
    try:
        updated = json.loads(result)
        ids = {{d["id"]: d for d in updated}}
        st.session_state.deals = [ids.get(d["id"], d) for d in (st.session_state.deals or [])]
    except Exception:
        pass
