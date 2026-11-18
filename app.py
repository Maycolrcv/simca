"""Punto de entrada:  streamlit run app.py"""
import streamlit as st

from simca.state import init_state

st.set_page_config(page_title="SIMCA Analytics", page_icon="🎓", layout="wide")
init_state()

pagina = st.navigation([
    st.Page("views/matriz.py", title="Matriz académica", icon="🎓", default=True),
    st.Page("views/configuracion.py", title="Configuración de materias", icon="⚙️"),
])
pagina.run()
