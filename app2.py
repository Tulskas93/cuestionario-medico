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

# --- CARGA DE DATOS (EXCEL .XLSX) ---
@st.cache_data(show_spinner="Abriendo los pergaminos de la Luna...")
def cargar_datos():
    # URL de tu archivo EXCEL en modo RAW/Download
    # GitHub no da "raw" de archivos binarios como Excel igual que los CSV, 
    # por lo que usamos ?raw=true al final de la URL normal
    url = "https://github.com/Tulskas93/cuestionario-medico/blob/main/preguntas_medicina.xlsx?raw=true"
    try:
        # Usamos read_excel en lugar de read_csv
        df = pd.read_excel(url)
        # Limpiar espacios en los nombres de las columnas
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.sidebar.error(f"Error técnico: {e}")
        return None

df = cargar_datos()

# --- VALIDACIÓN INICIAL ---
if df is None or df.empty:
    st.error("⚠️ No pude leer el archivo Excel.")
    st.write("Verifica que el nombre en tu GitHub sea exactamente: **preguntas_medicina.xlsx**")
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
    if modo == "Repetición Espaciada":
        if not st.session_state.preguntas_falladas:
            st.sidebar.warning("¡Aún no hay fallos registrados!")
            st.session_state.lista_preguntas = df.sample(frac=1)
        else:
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
    st.info("Onii-san, selecciona un modo y presiona 'Generar' para comenzar.")
elif st.session_state.indice_actual < len(st.session_state.lista_preguntas):
    
    pregunta = st.session_state.lista_preguntas.iloc[st.session_state.indice_actual]
    
    total = len(st.session_state.lista_preguntas)
    actual = st.session_state.indice_actual + 1
    st.progress(actual / total)
    st.write(f"Pregunta **{actual}** de **{total}**")

    st.subheader(pregunta['Pregunta'])
    
    # Creamos la lista de opciones (ajusta los nombres si en tu Excel son distintos)
    opciones = [pregunta['Opción A'], pregunta['Opción B'], 
                pregunta['Opción C'], pregunta['Opción D']]
    
    seleccion = st.radio("Diagnóstico:", opciones, key=f"q_{st.session_state.indice_actual}")

    if st.button("Confirmar Respuesta ➡️"):
        es_correcta = (str(seleccion).strip() == str(pregunta['Respuesta Correcta']).strip())
        
        if es_correcta:
            st.session_state.aciertos += 1
            if modo != "Simulacro UdeA": st.success("¡Excelente diagnóstico! ✨")
        else:
            st.session_state.preguntas_falladas.add(pregunta.name)
            if modo != "Simulacro UdeA": 
                st.error(f"Incorrecto. La respuesta era: {pregunta['Respuesta Correcta']}")
        
        if modo != "Simulacro UdeA":
            time.sleep(1.5)
            
        st.session_state.indice_actual += 1
        st.rerun()
else:
    st.balloons()
    st.header("¡Misión Cumplida! 🦇")
    st.metric("Puntaje Final", f"{st.session_state.aciertos}/{len(st.session_state.lista_preguntas)}")
    if st.button("🔄 Volver al Inicio"):
        st.session_state.lista_preguntas = pd.DataFrame()
        st.rerun()
