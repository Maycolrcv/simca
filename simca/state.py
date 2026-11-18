"""Inicialización de st.session_state (config + datos) compartida por todas las páginas."""
from __future__ import annotations

import streamlit as st

from .config_store import ConfigError, empty_config, load_config
from .snapshot import load_snapshot, snapshot_to_models


def init_state() -> None:
    ss = st.session_state
    if "config" not in ss:  # una sola lectura del JSON por sesión; luego solo se escribe al guardar
        try:
            res = load_config()
            ss["config"], ss["config_warnings"] = res.config, res.warnings
        except ConfigError as exc:
            ss["config"], ss["config_warnings"] = empty_config(), [str(exc)]
    if "datos" not in ss:
        ss["datos"] = load_snapshot()


def get_models():
    """(pensum, notas, matriculadas) o (None, None, None) si todavía no hay datos cargados."""
    datos = st.session_state.get("datos")
    if not datos:
        return None, None, None
    try:
        return snapshot_to_models(datos)
    except (TypeError, KeyError) as exc:
        st.error(f"El snapshot local está incompleto o es de otra versión ({exc}). Vuelve a cargar los datos.")
        return None, None, None
