import streamlit as st
import streamlit.components.v1 as components
import json
from supabase import create_client

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

# ── Supabase client ───────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

# ── Auth ──────────────────────────────────────────────────────────────
def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    if not st.session_state.logged_in:
        st.markdown("<style>[data-testid='stAppViewContainer']{background:#fff;}</style>", unsafe_allow_html=True)
        _, col, _ = st.columns([1, 1, 1])
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
                    try:
                        res = supabase.table("usuarios").select("*").eq("correo", correo).eq("clave", clave).eq("activo", True).execute()
                        if res.data:
                            u = res.data[0]
                            st.session_state.logged_in = True
                            st.session_state.usuario   = correo
                            st.session_state.vendedor  = u["nombre"]
                            st.session_state.rol       = u["rol"]
                            st.session_state.login_error = False
                            st.rerun()
                        else:
                            st.session_state.login_error = True
                    except Exception as e:
                        st.error(f"Error de conexion: {e}")
            if st.session_state.login_error:
                st.markdown("<div style='text-align:center;color:#ef4444;font-size:13px;margin-top:8px;'>Correo o contrasena incorrectos</div>", unsafe_allow_html=True)
        st.stop()

check_login()

# ── Load data ─────────────────────────────────────────────────────────
def load_deals():
    rol     = st.session_state.get("rol", "vendedor")
    vendedor = st.session_state.get("vendedor", "")
    try:
        if rol == "vendedor":
            res = supabase.table("negocios").select("*").eq("vendedor", vendedor).execute()
        else:
            res = supabase.table("negocios").select("*").execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error cargando negocios: {e}")
        return []

def load_comments(negocio_id):
    try:
        res = supabase.table("comentarios").select("*").eq("negocio_id", negocio_id).order("created_at").execute()
        return res.data or []
    except:
        return []

def save_deal(deal):
    try:
        supabase.table("negocios").upsert(deal).execute()
    except Exception as e:
        st.error(f"Error guardando: {e}")

def delete_deal(id):
    try:
        supabase.table("negocios").delete().eq("id", id).execute()
    except Exception as e:
        st.error(f"Error eliminando: {e}")

def add_comment(negocio_id, texto, autor):
    try:
        supabase.table("comentarios").insert({
            "negocio_id": negocio_id,
            "texto": texto,
            "autor": autor
        }).execute()
    except Exception as e:
        st.error(f"Error agregando comentario: {e}")

def get_vendedores():
    try:
        res = supabase.table("usuarios").select("nombre").eq("rol", "vendedor").execute()
        return [r["nombre"] for r in (res.data or [])]
    except:
        return []

# ── Session state ─────────────────────────────────────────────────────
if "deals" not in st.session_state:
    st.session_state.deals = load_deals()
if "comments" not in st.session_state:
    st.session_state.comments = []
if "cur_id" not in st.session_state:
    st.session_state.cur_id = None

STAGES    = ["Asignado","Visitado","Interesado","Esperando Aprobacion","Cierre ganado","Cierre perdido"]
rol       = st.session_state.get("rol", "vendedor")
vendedor  = st.session_state.get("vendedor", "")
usuario   = st.session_state.get("usuario", "")

can_edit   = rol in ("team_leader", "vendedor")
can_delete = rol == "team_leader"
can_create = rol in ("team_leader", "vendedor")
can_move   = rol in ("team_leader", "vendedor")
see_all    = rol in ("team_leader", "soporte")

deals       = st.session_state.deals
deals_json  = json.dumps(deals, ensure_ascii=False)
stages_json = json.dumps(STAGES, ensure_ascii=False)
vendor_json = json.dumps(vendedor, ensure_ascii=False)
rol_json    = json.dumps(rol, ensure_ascii=False)
vendedores_json = json.dumps(get_vendedores() if see_all else [vendedor], ensure_ascii=False)

can_edit_js   = "true" if can_edit else "false"
can_delete_js = "true" if can_delete else "false"
can_create_js = "true" if can_create else "false"
can_move_js   = "true" if can_move else "false"
see_all_js    = "true" if see_all else "false"

# ── Handle messages from component ────────────────────────────────────
if "pending_action" in st.session_state:
    action = st.session_state.pending_action
    st.session_state.pop("pending_action")

    if action["type"] == "logout":
        for k in ["logged_in","usuario","vendedor","rol","deals","comments","cur_id","login_error"]:
            st.session_state.pop(k, None)
        st.rerun()

    elif action["type"] == "save_deal":
        save_deal(action["deal"])
        st.session_state.deals = load_deals()
        st.rerun()

    elif action["type"] == "delete_deal":
        delete_deal(action["id"])
        st.session_state.deals = load_deals()
        st.rerun()

    elif action["type"] == "move_deal":
        d = next((x for x in st.session_state.deals if x["id"] == action["id"]), None)
        if d:
            d["etapa"] = action["etapa"]
            save_deal(d)
            st.session_state.deals = load_deals()
            st.rerun()

    elif action["type"] == "add_comment":
        add_comment(action["negocio_id"], action["texto"], vendedor)
        st.session_state.comments = load_comments(action["negocio_id"])
        st.rerun()

    elif action["type"] == "load_comments":
        st.session_state.comments = load_comments(action["negocio_id"])
        st.session_state.cur_id = action["negocio_id"]
        st.rerun()

    elif action["type"] == "create_deal":
        save_deal(action["deal"])
        st.session_state.deals = load_deals()
        st.rerun()

    elif action["type"] == "refresh":
        st.session_state.deals = load_deals()
        st.rerun()

    elif action["type"] == "filter_vendor":
        try:
            res = supabase.table("negocios").select("*").eq("vendedor", action["vendedor"]).execute()
            st.session_state.deals = res.data or []
        except:
            pass
        st.rerun()

comments_json = json.dumps(st.session_state.comments, ensure_ascii=False, default=str)
cur_id_json   = json.dumps(st.session_state.cur_id, ensure_ascii=False)

# ── HTML ──────────────────────────────────────────────────────────────
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:#f4f5f7;height:100vh;display:flex;flex-direction:column;overflow:hidden;}}

.topbar{{display:flex;align-items:center;gap:12px;background:#fff;border-bottom:1px solid #e8e8e8;padding:0 20px;height:52px;flex-shrink:0;}}
.logo{{font-size:20px;font-weight:800;color:#1A4ED8;letter-spacing:-1px;margin-right:4px;}}
.topbar-sep{{color:#e2e8f0;margin:0 4px;}}
.topbar-title{{font-size:14px;font-weight:600;color:#64748b;}}
.search-wrap{{flex:1;max-width:300px;position:relative;margin-left:8px;}}
.search-wrap input{{width:100%;padding:7px 12px 7px 32px;border:1px solid #e8e8e8;border-radius:8px;font-size:13px;color:#0f172a;background:#f8f9fa;outline:none;}}
.search-wrap input:focus{{border-color:#1A4ED8;background:#fff;}}
.s-icon{{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#94a3b8;font-size:13px;}}
.topbar-right{{display:flex;align-items:center;gap:8px;margin-left:auto;}}
.btn-new{{display:flex;align-items:center;gap:5px;background:#1A4ED8;color:#fff;border:none;padding:7px 14px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;}}
.btn-new:hover{{background:#1e40af;}}
.btn-new:disabled{{background:#93c5fd;cursor:not-allowed;}}
.view-toggle{{display:flex;border:1px solid #e8e8e8;border-radius:8px;overflow:hidden;}}
.vb{{padding:6px 12px;background:#fff;border:none;cursor:pointer;font-size:12px;color:#64748b;}}
.vb.active{{background:#eff6ff;color:#1A4ED8;font-weight:600;}}
.user-pill{{display:flex;align-items:center;gap:7px;padding:4px 10px;background:#f8f9fa;border-radius:8px;font-size:12px;color:#64748b;cursor:pointer;}}
.user-pill:hover{{background:#eff6ff;}}
.avatar{{width:26px;height:26px;border-radius:50%;background:#1A4ED8;color:#fff;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;}}
.role-badge{{font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;text-transform:uppercase;letter-spacing:0.04em;}}
.role-team_leader{{background:#fef3c7;color:#d97706;}}
.role-vendedor{{background:#eff6ff;color:#1A4ED8;}}
.role-soporte{{background:#f0fdf4;color:#16a34a;}}

.subnav{{display:flex;align-items:center;background:#fff;border-bottom:1px solid #e8e8e8;padding:0 20px;height:40px;flex-shrink:0;gap:16px;}}
.stats-bar{{display:flex;align-items:center;gap:16px;}}
.si{{display:flex;align-items:center;gap:5px;font-size:12px;color:#64748b;}}
.si-dot{{width:7px;height:7px;border-radius:50%;}}
.si-val{{font-weight:700;color:#0f172a;}}
.vendor-filter{{margin-left:auto;display:flex;align-items:center;gap:8px;}}
.vendor-sel{{padding:4px 8px;border:1px solid #e8e8e8;border-radius:6px;font-size:12px;color:#0f172a;background:#f8f9fa;outline:none;}}
.btn-refresh{{padding:5px 10px;border:1px solid #e8e8e8;border-radius:6px;font-size:12px;background:#fff;cursor:pointer;color:#64748b;}}
.btn-refresh:hover{{background:#f8f9fa;}}

.main{{flex:1;overflow:hidden;display:flex;flex-direction:column;}}
.board-wrap{{flex:1;overflow-x:auto;overflow-y:hidden;padding:16px 20px;display:flex;gap:12px;}}
.col{{flex:0 0 210px;min-width:190px;display:flex;flex-direction:column;max-height:100%;}}
.col-head{{display:flex;align-items:center;gap:7px;padding:10px 12px;background:#fff;border-radius:10px 10px 0 0;border:1px solid #e8e8e8;border-bottom:none;}}
.col-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0;}}
.col-name{{font-size:10px;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:0.05em;flex:1;}}
.col-n{{font-size:11px;color:#94a3b8;font-weight:600;}}
.col-tot{{font-size:10px;color:#1A4ED8;background:#eff6ff;padding:1px 6px;border-radius:4px;font-weight:600;}}
.cards-area{{flex:1;overflow-y:auto;padding:8px;background:#f4f5f7;border:1px solid #e8e8e8;border-top:none;border-radius:0 0 10px 10px;scrollbar-width:thin;scrollbar-color:#e2e8f0 transparent;}}
.cards-area.over{{background:#eff6ff;border-color:#1A4ED8;}}
.card{{background:#fff;border:1px solid #e8e8e8;border-radius:8px;padding:11px 12px;margin-bottom:7px;cursor:pointer;transition:box-shadow 0.15s,border-color 0.15s;}}
.card:hover{{box-shadow:0 2px 10px rgba(0,0,0,0.07);border-color:#d0d5dd;}}
.card.dragging{{opacity:0.35;}}
.c-name{{font-size:13px;font-weight:600;color:#0f172a;margin-bottom:2px;}}
.c-biz{{font-size:11px;color:#1A4ED8;font-weight:500;margin-bottom:7px;}}
.c-bar{{height:3px;border-radius:2px;background:#f0f0f0;margin-bottom:7px;}}
.c-fill{{height:100%;border-radius:2px;background:#1A4ED8;}}
.c-info{{font-size:10px;color:#94a3b8;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.c-loc{{font-size:10px;color:#d0d5dd;margin-top:3px;}}
.c-bottom{{display:flex;justify-content:space-between;align-items:center;margin-top:8px;padding-top:7px;border-top:1px solid #f4f5f7;}}
.c-amt{{font-size:12px;font-weight:700;color:#0f172a;}}
.c-prob{{font-size:10px;font-weight:600;padding:2px 6px;border-radius:5px;}}
.c-vendor{{font-size:10px;color:#94a3b8;margin-top:4px;}}
.empty{{text-align:center;padding:18px 8px;color:#d0d5dd;font-size:11px;}}

.list-wrap{{flex:1;overflow-y:auto;padding:16px 20px;}}
.ltable{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;border:1px solid #e8e8e8;}}
.ltable th{{font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;padding:10px 14px;text-align:left;border-bottom:1px solid #e8e8e8;background:#f8f9fa;}}
.ltable td{{font-size:13px;color:#0f172a;padding:10px 14px;border-bottom:1px solid #f4f5f7;vertical-align:middle;}}
.ltable tr:last-child td{{border-bottom:none;}}
.ltable tr:hover td{{background:#f8f9fa;cursor:pointer;}}
.spill{{display:inline-block;font-size:11px;font-weight:600;padding:3px 8px;border-radius:5px;}}

.stats-wrap{{flex:1;overflow-y:auto;padding:20px;}}
.sg{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px;}}
.sc{{background:#fff;border:1px solid #e8e8e8;border-radius:10px;padding:16px 18px;}}
.sc-label{{font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;}}
.sc-val{{font-size:26px;font-weight:800;color:#0f172a;letter-spacing:-0.5px;}}
.sc-sub{{font-size:11px;color:#94a3b8;margin-top:3px;}}
.chart-row{{display:grid;grid-template-columns:1fr 1fr;gap:14px;}}
.cc{{background:#fff;border:1px solid #e8e8e8;border-radius:10px;padding:18px;}}
.cc-title{{font-size:13px;font-weight:600;color:#0f172a;margin-bottom:14px;}}
.br{{display:flex;align-items:center;gap:8px;margin-bottom:9px;}}
.br-label{{font-size:11px;color:#64748b;width:130px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.br-track{{flex:1;height:8px;background:#f4f5f7;border-radius:4px;overflow:hidden;}}
.br-fill{{height:100%;border-radius:4px;background:#1A4ED8;}}
.br-val{{font-size:11px;font-weight:600;color:#0f172a;width:44px;text-align:right;}}
.fr{{display:flex;align-items:center;gap:8px;margin-bottom:8px;}}
.fr-label{{font-size:11px;color:#64748b;width:160px;flex-shrink:0;}}
.fr-track{{flex:1;height:22px;background:#f4f5f7;border-radius:5px;overflow:hidden;}}
.fr-fill{{height:100%;border-radius:5px;display:flex;align-items:center;justify-content:flex-end;padding-right:8px;}}
.fr-n{{font-size:10px;font-weight:700;color:#fff;}}

/* Drawer */
.ov{{display:none;position:fixed;inset:0;background:rgba(15,23,42,0.4);z-index:900;align-items:flex-start;justify-content:flex-end;}}
.ov.open{{display:flex;}}
.drawer{{width:480px;height:100vh;background:#fff;box-shadow:-8px 0 40px rgba(0,0,0,0.1);display:flex;flex-direction:column;animation:sIn 0.2s ease;overflow:hidden;}}
@keyframes sIn{{from{{transform:translateX(40px);opacity:0}}to{{transform:none;opacity:1}}}}
.dh{{display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid #f0f0f0;flex-shrink:0;}}
.dh-title{{flex:1;font-size:15px;font-weight:700;color:#0f172a;}}
.da{{display:flex;gap:6px;}}
.dab{{padding:6px 12px;border-radius:7px;border:1px solid #e8e8e8;background:#fff;font-size:12px;font-weight:600;cursor:pointer;color:#64748b;}}
.dab:hover{{background:#f8f9fa;}}
.dab.p{{background:#1A4ED8;color:#fff;border-color:#1A4ED8;}}
.dab.p:hover{{background:#1e40af;}}
.dab.d{{color:#ef4444;border-color:#fecaca;}}
.dab.d:hover{{background:#fef2f2;}}
.dab:disabled{{opacity:0.4;cursor:not-allowed;}}
.snav{{display:flex;align-items:center;padding:10px 18px;border-bottom:1px solid #f0f0f0;flex-shrink:0;overflow-x:auto;gap:2px;}}
.ss{{display:flex;align-items:center;gap:4px;padding:4px 8px;border-radius:6px;cursor:pointer;font-size:11px;font-weight:500;color:#94a3b8;white-space:nowrap;transition:all 0.15s;}}
.ss.active{{font-weight:700;}}
.ss-dot{{width:6px;height:6px;border-radius:50%;flex-shrink:0;}}
.sarr{{color:#d0d5dd;font-size:10px;}}
.dbody{{flex:1;overflow-y:auto;padding:18px;}}
.sec{{font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin:0 0 10px;padding-bottom:7px;border-bottom:1px solid #f4f5f7;}}
.fg{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:14px;}}
.f{{display:flex;flex-direction:column;gap:3px;}}
.f.full{{grid-column:1/-1;}}
.f label{{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.04em;font-weight:600;}}
.f input,.f select,.f textarea{{padding:7px 10px;border:1px solid #e8e8e8;border-radius:7px;font-size:13px;color:#0f172a;background:#f8f9fa;outline:none;font-family:inherit;transition:border-color 0.15s,background 0.15s;}}
.f input:focus,.f select:focus,.f textarea:focus{{border-color:#1A4ED8;background:#fff;}}
.f input:disabled,.f select:disabled,.f textarea:disabled{{color:#94a3b8;cursor:not-allowed;}}
.f textarea{{resize:vertical;min-height:68px;}}
.cbox{{background:#f8f9fa;border:1px solid #e8e8e8;border-radius:8px;padding:10px 12px;margin-bottom:8px;}}
.ctxt{{font-size:13px;color:#0f172a;line-height:1.5;white-space:pre-wrap;}}
.cmeta{{font-size:10px;color:#94a3b8;margin-top:4px;}}
.ci-wrap{{display:flex;flex-direction:column;gap:7px;}}
.ci{{width:100%;padding:9px 11px;border:1px solid #e8e8e8;border-radius:8px;font-size:13px;color:#0f172a;background:#f8f9fa;outline:none;resize:vertical;min-height:68px;font-family:inherit;}}
.ci:focus{{border-color:#1A4ED8;background:#fff;}}
.ci:disabled{{color:#94a3b8;cursor:not-allowed;}}
.btn-c{{align-self:flex-end;padding:7px 13px;background:#1A4ED8;color:#fff;border:none;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;}}
.btn-c:hover{{background:#1e40af;}}
.btn-c:disabled{{background:#93c5fd;cursor:not-allowed;}}

/* New deal */
.ndov{{display:none;position:fixed;inset:0;background:rgba(15,23,42,0.4);z-index:950;align-items:center;justify-content:center;}}
.ndov.open{{display:flex;}}
.ndm{{background:#fff;border-radius:14px;width:460px;max-width:94vw;max-height:90vh;overflow-y:auto;box-shadow:0 24px 64px rgba(0,0,0,0.16);animation:pop 0.18s ease;}}
@keyframes pop{{from{{transform:scale(0.96);opacity:0}}to{{transform:none;opacity:1}}}}
.ndh{{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid #f0f0f0;}}
.ndh-title{{font-size:15px;font-weight:700;color:#0f172a;}}
.nd-close{{width:27px;height:27px;border-radius:7px;border:1px solid #e8e8e8;background:#f8f9fa;cursor:pointer;font-size:14px;color:#94a3b8;display:flex;align-items:center;justify-content:center;}}
.nd-close:hover{{background:#f0f0f0;}}
.ndb{{padding:18px;}}
.ndf{{display:flex;gap:8px;justify-content:flex-end;padding:12px 18px;border-top:1px solid #f0f0f0;}}
.btn-cancel{{padding:7px 14px;border:1px solid #e8e8e8;border-radius:8px;background:#fff;font-size:13px;cursor:pointer;color:#64748b;}}
.btn-create{{padding:7px 16px;background:#1A4ED8;color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;}}
.btn-create:hover{{background:#1e40af;}}

::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-thumb{{background:#e2e8f0;border-radius:3px;}}
</style></head><body>

<div class="topbar">
  <span class="logo">TUU</span>
  <span class="topbar-sep">|</span>
  <span class="topbar-title">Pipeline</span>
  <div class="search-wrap">
    <span class="s-icon">&#9906;</span>
    <input type="text" id="search" placeholder="Buscar negocio, contacto..." oninput="filterDeals()">
  </div>
  <div class="topbar-right">
    <button class="btn-new" id="btn-new" onclick="openNew()" {'disabled' if not can_create else ''}>+ Crear negocio</button>
    <div class="view-toggle">
      <button class="vb active" id="vb-pipeline" onclick="setView('pipeline')">Pipeline</button>
      <button class="vb" id="vb-list" onclick="setView('list')">Lista</button>
      <button class="vb" id="vb-stats" onclick="setView('stats')">Stats</button>
    </div>
    <div class="user-pill" onclick="logout()">
      <div class="avatar" id="av">--</div>
      <span id="uname">...</span>
      <span class="role-badge role-{rol}" id="rbadge">{rol.replace('_',' ').title()}</span>
    </div>
  </div>
</div>

<div class="subnav">
  <div class="stats-bar">
    <div class="si"><span class="si-dot" style="background:#1A4ED8"></span>Activos: <span class="si-val" id="sb-a">0</span></div>
    <div class="si"><span class="si-dot" style="background:#059669"></span>Ganados: <span class="si-val" id="sb-g">0</span></div>
    <div class="si"><span class="si-dot" style="background:#dc2626"></span>Perdidos: <span class="si-val" id="sb-p">0</span></div>
    <div class="si">Valor: <span class="si-val" id="sb-v">$0</span></div>
  </div>
  {'<div class="vendor-filter"><select class="vendor-sel" id="vendor-sel" onchange="filterByVendor()"><option value="">Todos los vendedores</option></select></div>' if see_all else ''}
  <button class="btn-refresh" onclick="refresh()" style="margin-left:{'8px' if not see_all else 'auto'}">&#8635; Actualizar</button>
</div>

<div class="main">
  <div id="view-pipeline" class="board-wrap"></div>
  <div id="view-list" class="list-wrap" style="display:none">
    <table class="ltable">
      <thead><tr>
        <th>Contacto</th><th>Negocio</th><th>Etapa</th><th>Valor</th><th>Prob.</th>
        {'<th>Vendedor</th>' if see_all else ''}<th>Ciudad</th><th>Nivel</th>
      </tr></thead>
      <tbody id="list-body"></tbody>
    </table>
  </div>
  <div id="view-stats" class="stats-wrap" style="display:none"></div>
</div>

<!-- Drawer -->
<div class="ov" id="ov" onclick="if(event.target===this)closeD()">
  <div class="drawer">
    <div class="dh">
      <div class="dh-title" id="d-title">Negocio</div>
      <div class="da">
        <button class="dab d" id="btn-del" onclick="delDeal()" {'style="display:none"' if not can_delete else ''}>Eliminar</button>
        <button class="dab" onclick="closeD()">Cancelar</button>
        <button class="dab p" id="btn-save" onclick="saveD()" {'disabled' if not can_edit else ''}>Guardar</button>
      </div>
    </div>
    <div class="snav" id="d-snav"></div>
    <div class="dbody">
      <div class="sec">Contacto</div>
      <div class="fg">
        <div class="f"><label>Nombre</label><input id="f-nombre" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Apellido</label><input id="f-apellido" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Correo</label><input id="f-correo" type="email" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Telefono</label><input id="f-tel" {'disabled' if not can_edit else ''}></div>
      </div>
      <div class="sec">Negocio</div>
      <div class="fg">
        <div class="f full"><label>Nombre del negocio</label><input id="f-negnombre" {'disabled' if not can_edit else ''}></div>
        <div class="f full"><label>Descripcion</label><textarea id="f-desc" {'disabled' if not can_edit else ''}></textarea></div>
        <div class="f"><label>Nivel de venta</label><select id="f-nivel" {'disabled' if not can_edit else ''}><option>Alto</option><option>Medio</option><option>Bajo</option></select></div>
        <div class="f"><label>Resultado visita</label><input id="f-resultado" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Valor (USD)</label><input id="f-monto" type="number" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Probabilidad %</label><input id="f-prob" type="number" min="0" max="100" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Fecha creacion</label><input id="f-created" type="date" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Cierre estimado</label><input id="f-close" type="date" {'disabled' if not can_edit else ''}></div>
      </div>
      <div class="sec">Ubicacion</div>
      <div class="fg">
        <div class="f"><label>Calle</label><input id="f-calle" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Numero</label><input id="f-numero" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Comuna</label><input id="f-comuna" {'disabled' if not can_edit else ''}></div>
        <div class="f"><label>Ciudad</label><input id="f-ciudad" {'disabled' if not can_edit else ''}></div>
        <div class="f full"><label>Region</label><input id="f-region" {'disabled' if not can_edit else ''}></div>
      </div>
      <div class="sec">Comentarios</div>
      <div id="c-list"></div>
      <div class="ci-wrap">
        <textarea class="ci" id="new-c" placeholder="Escribe un comentario..." {'disabled' if rol == 'soporte' else ''}></textarea>
        <button class="btn-c" onclick="addC()" {'disabled' if rol == 'soporte' else ''}>Agregar comentario</button>
      </div>
    </div>
  </div>
</div>

<!-- New deal -->
<div class="ndov" id="ndov" onclick="if(event.target===this)closeNew()">
  <div class="ndm">
    <div class="ndh">
      <div class="ndh-title">Nuevo negocio</div>
      <button class="nd-close" onclick="closeNew()">&#x2715;</button>
    </div>
    <div class="ndb">
      <div class="fg">
        <div class="f"><label>Nombre</label><input id="n-nombre" placeholder="Juan"></div>
        <div class="f"><label>Apellido</label><input id="n-apellido" placeholder="Pérez"></div>
        <div class="f"><label>Correo</label><input id="n-correo" type="email" placeholder="juan@mail.com"></div>
        <div class="f"><label>Telefono</label><input id="n-tel" placeholder="+56 9 ..."></div>
        <div class="f full"><label>Nombre del negocio</label><input id="n-negnombre" placeholder="Almacén El Sol"></div>
        <div class="f"><label>Valor (USD)</label><input id="n-monto" type="number" placeholder="0"></div>
        <div class="f"><label>Probabilidad %</label><input id="n-prob" type="number" placeholder="50" min="0" max="100"></div>
        <div class="f"><label>Nivel de venta</label><select id="n-nivel"><option>Alto</option><option selected>Medio</option><option>Bajo</option></select></div>
        <div class="f"><label>Ciudad</label><input id="n-ciudad"></div>
        <div class="f"><label>Comuna</label><input id="n-comuna"></div>
        <div class="f full"><label>Region</label><input id="n-region"></div>
      </div>
    </div>
    <div class="ndf">
      <button class="btn-cancel" onclick="closeNew()">Cancelar</button>
      <button class="btn-create" onclick="createDeal()">Crear negocio</button>
    </div>
  </div>
</div>

<script>
const STAGES={stages_json};
const VENDOR={vendor_json};
const ROL={rol_json};
const VENDEDORES={vendedores_json};
const CAN_EDIT={can_edit_js};
const CAN_DELETE={can_delete_js};
const CAN_MOVE={can_move_js};
const SEE_ALL={see_all_js};
const COLORS={{"Asignado":"#94a3b8","Visitado":"#1A4ED8","Interesado":"#d97706","Esperando Aprobacion":"#7c3aed","Cierre ganado":"#059669","Cierre perdido":"#dc2626"}};

let deals={deals_json};
let filtered=[...deals];
let comments={comments_json};
let curId={cur_id_json};
let dragId=null;
let view='pipeline';

// Init
document.getElementById('uname').textContent=VENDOR;
const ini=VENDOR.split(' ').map(w=>w[0]||'').join('').slice(0,2).toUpperCase();
document.getElementById('av').textContent=ini;

// Populate vendor filter
if(SEE_ALL){{
  const sel=document.getElementById('vendor-sel');
  if(sel) VENDEDORES.forEach(v=>{{const o=document.createElement('option');o.value=v;o.textContent=v;sel.appendChild(o);}});
}}

// If there's a pending cur_id (comments loaded), reopen drawer
if(curId){{
  setTimeout(()=>openDrawer(curId),100);
}}

function fmt(n){{if(n>=1e6)return'$'+(n/1e6).toFixed(1)+'M';if(n>=1e3)return'$'+Math.round(n/1e3)+'K';return'$'+n;}}
function pStyle(p,e){{
  if(e==='Cierre ganado')return'background:#f0fdf4;color:#16a34a';
  if(e==='Cierre perdido')return'background:#fef2f2;color:#dc2626';
  if(p>=70)return'background:#f0fdf4;color:#16a34a';
  if(p>=40)return'background:#fffbeb;color:#d97706';
  return'background:#fef2f2;color:#dc2626';
}}
function uid(){{return Date.now().toString(36)+Math.random().toString(36).slice(2);}}

function send(action){{
  window.parent.postMessage({{type:'streamlit:setComponentValue',value:JSON.stringify(action)}},'*');
}}

function updateStats(){{
  const g=filtered.filter(d=>d.etapa==='Cierre ganado').length;
  const p=filtered.filter(d=>d.etapa==='Cierre perdido').length;
  const a=filtered.filter(d=>!['Cierre ganado','Cierre perdido'].includes(d.etapa)).length;
  const v=filtered.filter(d=>d.etapa!=='Cierre perdido').reduce((s,d)=>s+(d.monto||0),0);
  document.getElementById('sb-a').textContent=a;
  document.getElementById('sb-g').textContent=g;
  document.getElementById('sb-p').textContent=p;
  document.getElementById('sb-v').textContent=fmt(v);
}}

function filterDeals(){{
  const q=document.getElementById('search').value.toLowerCase().trim();
  filtered=q?deals.filter(d=>
    ((d.nombre||'')+' '+(d.apellido||'')).toLowerCase().includes(q)||
    (d.nombre_negocio||'').toLowerCase().includes(q)||
    (d.correo||'').toLowerCase().includes(q)
  ):[...deals];
  render();
}}

function filterByVendor(){{
  const v=document.getElementById('vendor-sel')?.value||'';
  if(v) send({{type:'filter_vendor',vendedor:v}});
  else send({{type:'refresh'}});
}}

function setView(v){{
  view=v;
  ['pipeline','list','stats'].forEach(x=>{{
    document.getElementById('view-'+x).style.display=x===v?(x==='pipeline'?'flex':'block'):'none';
    const b=document.getElementById('vb-'+x);if(b)b.classList.toggle('active',x===v);
  }});
  render();
}}

function render(){{updateStats();if(view==='pipeline')buildBoard();else if(view==='list')buildList();else buildStats();}}

function buildBoard(){{
  const b=document.getElementById('view-pipeline');b.innerHTML='';
  STAGES.forEach(stage=>{{
    const sd=filtered.filter(d=>d.etapa===stage);
    const col=document.createElement('div');col.className='col';
    const total=sd.reduce((a,d)=>a+(d.monto||0),0);
    const ca=document.createElement('div');ca.className='cards-area';ca.dataset.stage=stage;
    if(CAN_MOVE){{
      ca.addEventListener('dragover',e=>{{e.preventDefault();ca.classList.add('over');}});
      ca.addEventListener('dragleave',()=>ca.classList.remove('over'));
      ca.addEventListener('drop',e=>{{
        e.preventDefault();ca.classList.remove('over');
        if(dragId){{send({{type:'move_deal',id:dragId,etapa:stage}});dragId=null;}}
      }});
    }}
    sd.forEach(d=>{{
      const card=document.createElement('div');card.className='card';
      if(CAN_MOVE){{card.draggable=true;card.addEventListener('dragstart',e=>{{dragId=d.id;setTimeout(()=>card.classList.add('dragging'),0);}});card.addEventListener('dragend',()=>{{card.classList.remove('dragging');dragId=null;}});}}
      card.addEventListener('click',()=>openDrawer(d.id));
      card.innerHTML=`
        <div class="c-name">${{d.nombre||''}} ${{d.apellido||''}}</div>
        <div class="c-biz">${{d.nombre_negocio||''}}</div>
        <div class="c-bar"><div class="c-fill" style="width:${{d.probabilidad||0}}%"></div></div>
        <div class="c-info">${{d.correo||''}}</div>
        <div class="c-info">${{d.telefono||''}}</div>
        <div class="c-loc">${{[d.comuna,d.ciudad].filter(Boolean).join(', ')}}</div>
        ${{SEE_ALL?`<div class="c-vendor">${{d.vendedor||''}}</div>`:''}}
        <div class="c-bottom">
          <span class="c-amt">${{fmt(d.monto||0)}}</span>
          <span class="c-prob" style="${{pStyle(d.probabilidad||0,d.etapa)}}">${{d.probabilidad||0}}%</span>
        </div>`;
      ca.appendChild(card);
    }});
    if(!sd.length)ca.innerHTML='<div class="empty">Sin negocios</div>';
    col.innerHTML=`<div class="col-head">
      <span class="col-dot" style="background:${{COLORS[stage]||'#94a3b8'}}"></span>
      <span class="col-name">${{stage}}</span>
      <span class="col-n">${{sd.length}}</span>
      ${{sd.length?`<span class="col-tot">${{fmt(total)}}</span>`:''}}
    </div>`;
    col.appendChild(ca);b.appendChild(col);
  }});
}}

function buildList(){{
  const tb=document.getElementById('list-body');tb.innerHTML='';
  filtered.forEach(d=>{{
    const tr=document.createElement('tr');tr.onclick=()=>openDrawer(d.id);
    const col=COLORS[d.etapa]||'#94a3b8';
    const nv=d.nivel_venta||'';
    const nvStyle=nv==='Alto'?'background:#f0fdf4;color:#16a34a':nv==='Medio'?'background:#fffbeb;color:#d97706':'background:#fef2f2;color:#dc2626';
    tr.innerHTML=`
      <td><b>${{d.nombre||''}} ${{d.apellido||''}}</b></td>
      <td style="color:#1A4ED8;font-size:12px">${{d.nombre_negocio||''}}</td>
      <td><span class="spill" style="background:${{col}}18;color:${{col}}">${{d.etapa}}</span></td>
      <td><b>${{fmt(d.monto||0)}}</b></td>
      <td><span class="c-prob" style="${{pStyle(d.probabilidad||0,d.etapa)}}">${{d.probabilidad||0}}%</span></td>
      ${{SEE_ALL?`<td style="font-size:12px;color:#64748b">${{d.vendedor||''}}</td>`:''}}
      <td style="font-size:12px;color:#64748b">${{d.ciudad||'—'}}</td>
      <td><span class="spill" style="${{nvStyle}}">${{nv}}</span></td>`;
    tb.appendChild(tr);
  }});
}}

function buildStats(){{
  const w=document.getElementById('view-stats');
  const g=deals.filter(d=>d.etapa==='Cierre ganado');
  const p=deals.filter(d=>d.etapa==='Cierre perdido');
  const a=deals.filter(d=>!['Cierre ganado','Cierre perdido'].includes(d.etapa));
  const val=deals.filter(d=>d.etapa!=='Cierre perdido').reduce((s,d)=>s+(d.monto||0),0);
  const tasa=deals.length?Math.round(g.length/deals.length*100):0;
  const funnel=STAGES.map(s=>{{const n=deals.filter(d=>d.etapa===s).length;const pct=deals.length?Math.round(n/deals.length*100):0;return`<div class="fr"><div class="fr-label">${{s}}</div><div class="fr-track"><div class="fr-fill" style="width:${{pct}}%;background:${{COLORS[s]||'#94a3b8'}}">${{n?`<span class="fr-n">${{n}}</span>`:''}}
</div></div></div>`;}}).join('');
  const maxM=Math.max(...deals.map(d=>d.monto||0),1);
  const bars=[...deals].sort((a,b)=>(b.monto||0)-(a.monto||0)).slice(0,6).map(d=>`<div class="br"><div class="br-label">${{d.nombre||''}} ${{d.apellido||''}}</div><div class="br-track"><div class="br-fill" style="width:${{Math.round((d.monto||0)/maxM*100)}}%"></div></div><div class="br-val">${{fmt(d.monto||0)}}</div></div>`).join('');
  w.innerHTML=`
    <div class="sg">
      <div class="sc"><div class="sc-label">Total negocios</div><div class="sc-val">${{deals.length}}</div><div class="sc-sub">En el pipeline</div></div>
      <div class="sc"><div class="sc-label">Valor activo</div><div class="sc-val">${{fmt(val)}}</div><div class="sc-sub">Excluyendo perdidos</div></div>
      <div class="sc"><div class="sc-label">Tasa de cierre</div><div class="sc-val">${{tasa}}%</div><div class="sc-sub">${{g.length}} ganados / ${{deals.length}} totales</div></div>
      <div class="sc"><div class="sc-label">En curso</div><div class="sc-val">${{a.length}}</div><div class="sc-sub">${{p.length}} perdidos</div></div>
    </div>
    <div class="chart-row">
      <div class="cc"><div class="cc-title">Embudo por etapa</div>${{funnel}}</div>
      <div class="cc"><div class="cc-title">Top negocios por valor</div>${{bars}}</div>
    </div>`;
}}

function openDrawer(id){{
  const d=deals.find(x=>x.id===id);if(!d)return;curId=id;
  document.getElementById('d-title').textContent=(d.nombre||'')+' '+(d.apellido||'');
  document.getElementById('f-nombre').value=d.nombre||'';
  document.getElementById('f-apellido').value=d.apellido||'';
  document.getElementById('f-correo').value=d.correo||'';
  document.getElementById('f-tel').value=d.telefono||'';
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

  const nav=document.getElementById('d-snav');nav.innerHTML='';
  STAGES.forEach((s,i)=>{{
    if(i>0)nav.insertAdjacentHTML('beforeend','<span class="sarr">›</span>');
    const el=document.createElement('div');el.className='ss'+(d.etapa===s?' active':'');
    el.style.cssText=d.etapa===s?`color:${{COLORS[s]}};background:${{COLORS[s]}}15;`:'';
    el.innerHTML=`<span class="ss-dot" style="background:${{COLORS[s]||'#94a3b8'}}"></span>${{s}}`;
    if(CAN_MOVE)el.onclick=()=>{{send({{type:'move_deal',id:curId,etapa:s}});}};
    nav.appendChild(el);
  }});

  // Load comments
  send({{type:'load_comments',negocio_id:id}});

  document.getElementById('ov').classList.add('open');
}}

// Re-render comments when updated by Streamlit
function renderComments(){{
  const list=document.getElementById('c-list');if(!list)return;
  list.innerHTML=comments.length?comments.map(c=>`
    <div class="cbox">
      <div class="ctxt">${{c.texto}}</div>
      <div class="cmeta">${{c.autor}} · ${{c.created_at?new Date(c.created_at).toLocaleString('es-CL'):''}}
</div>
    </div>`).join(''):'';
}}

function addC(){{
  const txt=document.getElementById('new-c').value.trim();if(!txt||!curId)return;
  send({{type:'add_comment',negocio_id:curId,texto:txt}});
  document.getElementById('new-c').value='';
}}

function saveD(){{
  const d=deals.find(x=>x.id===curId);if(!d)return;
  d.nombre=document.getElementById('f-nombre').value;
  d.apellido=document.getElementById('f-apellido').value;
  d.correo=document.getElementById('f-correo').value;
  d.telefono=document.getElementById('f-tel').value;
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
  send({{type:'save_deal',deal:d}});closeD();
}}

function delDeal(){{
  if(!confirm('Eliminar este negocio?'))return;
  send({{type:'delete_deal',id:curId}});closeD();
}}

function closeD(){{document.getElementById('ov').classList.remove('open');curId=null;}}

function openNew(){{document.getElementById('ndov').classList.add('open');}}
function closeNew(){{document.getElementById('ndov').classList.remove('open');}}
function createDeal(){{
  const nombre=document.getElementById('n-nombre').value.trim();
  if(!nombre){{alert('Ingresa el nombre del contacto');return;}}
  const nd={{
    id:uid(),nombre,
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
    etapa:'Asignado',vendedor:VENDOR,
    fecha_creacion:new Date().toISOString().split('T')[0]
  }};
  send({{type:'create_deal',deal:nd}});closeNew();
  ['n-nombre','n-apellido','n-correo','n-tel','n-negnombre','n-ciudad','n-comuna','n-region'].forEach(id=>document.getElementById(id).value='');
}}

function refresh(){{send({{type:'refresh'}});}}
function logout(){{if(confirm('Cerrar sesion?'))send({{type:'logout'}});}}

// Expose for Streamlit re-renders
window._updateComments=function(c){{comments=c;renderComments();}};

render();
// Render comments if already loaded
if(comments.length)renderComments();
</script></body></html>"""

result = components.html(html, height=800, scrolling=False)

if result:
    try:
        action = json.loads(result)
        st.session_state.pending_action = action
        st.rerun()
    except Exception:
        pass
