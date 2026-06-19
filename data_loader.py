import json
import os
import requests
import streamlit as st
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "deals.json"

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

STAGE_BG = {
    "Asignado":             "#F1EFE8",
    "Visitado":             "#E6F1FB",
    "Interesado":           "#FAEEDA",
    "Esperando Aprobación": "#EEEDFE",
    "Cierre ganado":        "#E1F5EE",
    "Cierre perdido":       "#FCEBEB",
}


@st.cache_data(ttl=3600)
def load_deals(source: str = "mock", webhook_url: str = "") -> list[dict]:
    """
    Carga negocios desde la fuente configurada.
    source: 'mock' usa data/deals.json | 'webhook' llama al endpoint de n8n
    """
    if source == "webhook" and webhook_url:
        try:
            res = requests.get(webhook_url, timeout=10)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            st.warning(f"No se pudo conectar al webhook ({e}). Usando datos de prueba.")

    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)
