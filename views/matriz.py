"""Página principal: pensum oficial x notas."""
import os
import subprocess
import sys

import streamlit as st

from simca.matrix import construir_matriz, matriz_a_dataframe
from simca.render import ESTADOS, render_leyenda_html, render_matriz_html
from simca.requisitos import evaluar_requisitos
from simca.settings import PROJECT_ROOT, credentials_configured, get_student_code
from simca.snapshot import build_snapshot, save_snapshot
from simca.state import get_models

ss = st.session_state
st.title("🎓 Matriz académica")


def _actualizar_desde_simca(usuario: str, password: str, codigo: str) -> None:
    # Prioridad: lo digitado en la UI; si está vacío, lo que haya en .env / entorno.
    if not ((usuario.strip() and password) or credentials_configured()):
        st.error("Faltan credenciales: digítalas en la barra lateral o define SIMCA_USER y SIMCA_PASSWORD en `.env`.")
        return
    if not codigo.strip():
        st.error("Digita el código o cédula del estudiante.")
        return
    env = {**os.environ, "SIMCA_STUDENT_CODE": codigo.strip()}  # por entorno, no por argv
    if usuario.strip() and password:
        env["SIMCA_USER"], env["SIMCA_PASSWORD"] = usuario.strip(), password  # solo para el subproceso
    with st.spinner("Consultando SIMCA (login, notas y pénsum)…"):
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "simca.cli_scrape"],
                capture_output=True, text=True, timeout=300, cwd=PROJECT_ROOT, env=env,
            )
        except subprocess.TimeoutExpired:
            st.error("La consulta superó 5 minutos. Inténtalo de nuevo.")
            return
    if proc.returncode != 0:
        st.error((proc.stderr or "Error desconocido").strip()[-600:])
        return
    from simca.snapshot import load_snapshot
    ss["datos"] = load_snapshot()
    st.success(proc.stdout.strip().splitlines()[0])


with st.sidebar:
    st.subheader("Fuente de datos")
    usuario = st.text_input("Usuario SIMCA", value=os.getenv("SIMCA_USER", ""), autocomplete="off")
    password = st.text_input(
        "Contraseña SIMCA", type="password", autocomplete="off",
        placeholder="(usa la de .env)" if credentials_configured() else "",
        help="No se guarda en disco ni se escribe en ningún archivo. Se envía solo al navegador automatizado durante la consulta.",
    )
    codigo = st.text_input("Código o cédula del estudiante", value=get_student_code(), help="Se usa solo para esta consulta; no se guarda.")
    if st.button("🔄 Actualizar desde SIMCA", type="primary"):
        _actualizar_desde_simca(usuario, password, codigo)

    with st.expander("📁 Cargar HTML guardados (sin conexión)"):
        up_p = st.file_uploader("Pénsum / Currículo (.html)", type=["html", "htm"], key="up_pensum")
        up_n = st.file_uploader("Historia Académica (.html)", type=["html", "htm"], key="up_notas")
        up_m = st.file_uploader("Materias matriculadas (.html, opcional)", type=["html", "htm"], key="up_matric")
        guardar = st.checkbox("Guardar copia local procesada", value=False)
        if st.button("Procesar archivos", disabled=not (up_p and up_n)):
            try:
                dec = lambda f: f.getvalue().decode("utf-8", "replace")  # noqa: E731
                snap = build_snapshot(dec(up_p), dec(up_n), dec(up_m) if up_m else None)
                ss["datos"] = snap
                if guardar:
                    save_snapshot(snap)
                st.success("Archivos procesados.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"No se pudo procesar: {exc}")
    if ss.get("datos"):
        st.caption(f"Datos generados: {ss['datos'].get('generado', '—')}")

pensum, notas, matriculadas = get_models()
if not pensum:
    st.info("Aún no hay datos. Usa **Actualizar desde SIMCA** o carga los HTML guardados en la barra lateral.")
    st.stop()

for w in ss.get("config_warnings", []):
    st.warning(w)

est = ss["datos"].get("estudiante", {})
if est:
    st.caption(f"**{est.get('nombres', '')}** · {est.get('programa', '')} · semestre {est.get('semestre', '—')} · estado {est.get('estado', '—')}")

if not notas:
    st.info("Este estudiante no tiene notas registradas en SIMCA: se muestra solo el pensum, con las materias sin prerrequisitos como disponibles.")

res = construir_matriz(pensum, notas, ss["config"], matriculadas)
m = res.metricas

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Avance (créditos)", f"{m['pct_avance']:.1f}%", f"{m['creditos_aprobados']}/{m['creditos_pensum']} cr", delta_color="off")
c2.metric("Promedio ponderado", f"{m['promedio_ponderado']:.2f}" if m["promedio_ponderado"] else "—")
c3.metric("Materias aprobadas", f"{m['n_aprobada']}/{m['n_total']}")
c4.metric("En curso", m["n_en_curso"], f"{m['creditos_en_curso']} cr" if m["n_en_curso"] else None, delta_color="off")
c5.metric("Disponibles ahora", m["n_disponible"], f"{m['n_bloqueada']} bloqueadas", delta_color="off")
if m["n_en_curso"]:
    st.caption(f"Avance proyectado si aprueba lo que cursa: **{m['pct_proyectado']:.1f}%** · periodo {ss['datos'].get('periodo_actual') or '—'}")
elif not ss["datos"].get("matriculadas_cargadas"):
    st.caption("Sin datos de matrícula actual (sección «Materias» no cargada).")
if m["n_adicionales"] or res.adicionales:
    st.caption(f"Electivas adicionales (sobre los cupos del pensum): **{m['n_adicionales']}** aprobadas · {m['creditos_adicionales']} cr — no suman al avance del pensum.")
st.progress(min(m["pct_avance"] / 100, 1.0))

f1, f2 = st.columns([3, 1])
estados_sel = f1.multiselect("Estados a mostrar", list(ESTADOS), default=list(ESTADOS), format_func=lambda e: ESTADOS[e][0])
con_electivas = f2.toggle("Incluir electivas", value=True)

st.markdown(render_leyenda_html(), unsafe_allow_html=True)
st.markdown(render_matriz_html(res, set(estados_sel), con_electivas), unsafe_allow_html=True)

if res.sin_correspondencia or res.matriculadas_sin_correspondencia:
    with st.expander(f"⚠️ Registros sin materia asignada ({len(res.sin_correspondencia) + len(res.matriculadas_sin_correspondencia)})", expanded=True):
        for n in res.sin_correspondencia:
            st.text(f"Historia · {n.periodo} · {n.id} · {n.nombre} · {n.definitiva}")
        for mm in res.matriculadas_sin_correspondencia:
            st.text(f"Matriculada · {mm.periodo} · {mm.codigo} · {mm.nombre}")
        st.page_link("views/configuracion.py", label="Resolver con un alias en Configuración →", icon="⚙️")

adv = res.advertencias + ss["datos"].get("advertencias", [])
if adv:
    with st.expander(f"Avisos de extracción y unificación ({len(adv)})"):
        for a in adv:
            st.write("• " + a)

if matriculadas:
    with st.expander(f"📅 Materias matriculadas {ss['datos'].get('periodo_actual') or ''} ({len(matriculadas)})"):
        st.dataframe([{
            "Código": x.codigo, "Materia": x.nombre, "Sec.": x.seccion, "Docente": x.docentes,
            "Horario": " · ".join(f"{h.dia} {h.horario} ({h.salon})" for h in x.horarios), "Repetición": x.repeticion,
        } for x in matriculadas], hide_index=True)

with st.expander("Tabla detallada / exportar"):
    df = matriz_a_dataframe(res)
    st.dataframe(df, hide_index=True)
    st.download_button("⬇️ Descargar CSV", df.to_csv(index=False).encode("utf-8-sig"), "matriz_academica.csv", "text/csv")

datos = ss["datos"]
filas_req, otros_req = evaluar_requisitos(datos.get("requisitos_grado_oficiales", []), datos.get("requisitos_grado", []), res.requisitos_marcados)
if filas_req or otros_req:
    with st.expander("🎓 Requisitos de grado", expanded=True):
        icono = {"cumplido": "✅ Cumplido", "en_curso": "🔵 En curso", "pendiente": "⬜ Pendiente"}
        if filas_req:
            st.dataframe([{"Requisito": f["requisito"], "Estado": icono[f["estado"]], "Evidencia": "; ".join(f["evidencia"]) or "—"}
                          for f in filas_req], hide_index=True)
        if otros_req:
            st.write("**Otros reconocidos como requisito de grado**")
            st.dataframe([{"Registro": o["nombre"], "Estado": o["estado"].replace("_", " ").capitalize(), "Detalle": o["detalle"]}
                          for o in otros_req], hide_index=True)
        st.caption("La asociación de las filas de SIMCA a cada requisito se infiere por el nombre (AFF, inglés/idioma, ECAES). "
                   "Para marcar un registro del historial como requisito, usa **Configuración**.")
