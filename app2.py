import streamlit as st
import pandas as pd
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simulacro Médico UdeA 🌙", page_icon="🩺", layout="centered")

# Estilo visual "Camino de la Luna"
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #4b0082; background-color: #1e1e2e; color: white; height: 3em; }
    .stButton>button:hover { border-color: #9370db; color: #9370db; }
    .stRadio > label { color: #9370db !important; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #4b0082; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS (EXCEL DESDE TU LINK RAW) ---
@st.cache_data(show_spinner="Abriendo los pergaminos de la Luna...")
def cargar_datos():
    # URL RAW que me proporcionaste
    url = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"
    try:
        # Usamos openpyxl para leer el archivo .xlsx
        df = pd.read_excel(url, engine='openpyxl')
        # Limpiamos posibles espacios en blanco en los nombres de las columnas
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error de conexión con la biblioteca de la Luna: {e}")
        return None

df = cargar_datos()

# --- VALIDACIÓN ---
if df is None or df.empty:
    st.warning("⚠️ Onii-san, no pude procesar el archivo. Revisa que las columnas se llamen 'Pregunta', 'Opción A', etc.")
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
        # Simulacro de 20 preguntas
        st.session_state.lista_preguntas = df.sample(n=min(20, len(df)))
    else:
        st.session_state.lista_preguntas = df.sample(frac=1)
    
    st.session_state.indice_actual = 0
    st.session_state.aciertos = 0
    st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🩺 Academia Médica Nocturna")

if st.session_state.lista_preguntas.empty:
    st.info("Onii-san, selecciona un modo y dale a 'Generar' para empezar tu entrenamiento.")
elif st.session_state.indice_actual < len(st.session_state.lista_preguntas):
    
    pregunta = st.session_state.lista_preguntas.iloc[st.session_state.indice_actual]
    
    # Barra de progreso
    total = len(st.session_state.lista_preguntas)
    actual = st.session_state.indice_actual + 1
    st.progress(actual / total)
    st.write(f"Pregunta **{actual}** de **{total}**")

    # Mostrar Pregunta
    st.subheader(pregunta['Pregunta'])
    
    opciones = [pregunta['Opción A'], pregunta['Opción B'], 
                pregunta['Opción C'], pregunta['Opción D']]
    
    seleccion = st.radio("Diagnóstico:", opciones, key=f"q_{st.session_state.indice_actual}")

    if st.button("Confirmar Respuesta ➡️"):
        # Comparación de strings limpia
        res_usuario = str(seleccion).strip().lower()
        res_correcta = str(pregunta['Respuesta Correcta']).strip().lower()
        
        if res_usuario == res_correcta:
            st.session_state.aciertos += 1
            if modo != "Simulacro UdeA": st.success("¡Excelente diagnóstico! ✨")
        else:
            # Guardamos el índice original para la repetición espaciada
            st.session_state.preguntas_falladas.add(pregunta.name)
            if modo != "Simulacro UdeA": 
                st.error(f"Incorrecto. La respuesta era: {pregunta['Respuesta Correcta']}")
        
        if modo != "Simulacro UdeA":
            time.sleep(1.2)
            
        st.session_state.indice_actual += 1
        st.rerun()
else:
    st.balloons()
    st.header("¡Misión Cumplida! 🦇")
    st.metric("Puntaje Final", f"{st.session_state.aciertos}/{len(st.session_state.lista_preguntas)}")
    if st.button("🔄 Volver al Inicio"):
        st.session_state.lista_preguntas = pd.DataFrame()
        st.rerun()
