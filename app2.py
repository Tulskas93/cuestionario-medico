import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simulacro Médico UdeA 🌙", page_icon="🩺")

# Estilo visual "Camino de la Luna"
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #4b0082; background-color: #1e1e2e; color: white; }
    .stRadio > label { color: #9370db !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS (EXCEL) ---
@st.cache_data(show_spinner="Abriendo los pergaminos de la Luna...")
def cargar_datos():
    # URL para descargar el Excel desde GitHub
    url = "https://github.com/Tulskas93/cuestionario-medico/blob/main/preguntas_medicina.xlsx?raw=true"
    try:
        # Importante: engine='openpyxl' es lo que lee archivos .xlsx
        df = pd.read_excel(url, engine='openpyxl')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")
        return None

df = cargar_datos()

if df is None or df.empty:
    st.warning("⚠️ Onii-san, verifica que el archivo se llame 'preguntas_medicina.xlsx' en tu GitHub.")
    st.stop()

# --- INICIALIZACIÓN DEL ESTADO ---
if 'preguntas_falladas' not in st.session_state:
    st.session_state.preguntas_falladas = set()
if 'indice_actual' not in st.session_state:
    st.session_state.indice_actual = 0
if 'aciertos' not in st.session_state:
    st.session_state.aciertos = 0
if 'lista_preguntas' not in st.session_state:
    st.session_state.lista_preguntas = pd.DataFrame()

# --- SIDEBAR ---
st.sidebar.title("🌙 Menú de Secuencia")
modo = st.sidebar.radio("Método de estudio:", ["Práctica Libre", "Simulacro UdeA", "Repetición Espaciada"])

if st.sidebar.button("✨ Generar / Reiniciar"):
    if modo == "Repetición Espaciada" and st.session_state.preguntas_falladas:
        indices = list(st.session_state.preguntas_falladas)
        st.session_state.lista_preguntas = df.loc[indices].sample(frac=1)
    elif modo == "Simulacro UdeA":
        st.session_state.lista_preguntas = df.sample(n=min(20, len(df)))
    else:
        st.session_state.lista_preguntas = df.sample(frac=1)
    
    st.session_state.indice_actual = 0
    st.session_state.aciertos = 0
    st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🩺 Academia Médica Nocturna")

if st.session_state.lista_preguntas.empty:
    st.info("Onii-san, selecciona un modo y dale a 'Generar' para empezar.")
elif st.session_state.indice_actual < len(st.session_state.lista_preguntas):
    pregunta = st.session_state.lista_preguntas.iloc[st.session_state.indice_actual]
    
    st.write(f"Pregunta **{st.session_state.indice_actual + 1}** de **{len(st.session_state.lista_preguntas)}**")
    st.subheader(pregunta['Pregunta'])
    
    opciones = [pregunta['Opción A'], pregunta['Opción B'], pregunta['Opción C'], pregunta['Opción D']]
    seleccion = st.radio("Diagnóstico:", opciones, key=f"q_{st.session_state.indice_actual}")

    if st.button("Confirmar Respuesta ➡️"):
        # Comparación limpia de strings
        if str(seleccion).strip() == str(pregunta['Respuesta Correcta']).strip():
            st.session_state.aciertos += 1
            if modo != "Simulacro UdeA": st.success("¡Correcto! ✨")
        else:
            st.session_state.preguntas_falladas.add(pregunta.name)
            if modo != "Simulacro UdeA": st.error(f"Fallo. Era: {pregunta['Respuesta Correcta']}")
        
        time.sleep(1)
        st.session_state.indice_actual += 1
        st.rerun()
else:
    st.balloons()
    st.metric("Puntaje Final", f"{st.session_state.aciertos}/{len(st.session_state.lista_preguntas)}")
    if st.button("Nueva Ronda"):
        st.session_state.lista_preguntas = pd.DataFrame()
        st.rerun()
