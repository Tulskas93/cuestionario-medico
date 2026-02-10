import streamlit as st
import pandas as pd
import random

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO "LUNA" ---
st.set_page_config(page_title="Simulacro Médico UdeA", page_icon="🌙")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { width: 100%; border-radius: 20px; border: 1px solid #4b0082; }
    .stProgress > div > div > div > div { background-color: #4b0082; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # Asegúrate de que el CSV esté en la misma carpeta o usa la URL raw de GitHub
    url = "https://raw.githubusercontent.com/Tulskas93/cuestionario-medico/main/preguntas_medicina.csv"
    return pd.read_csv(url)

df = cargar_datos()

# --- INICIALIZACIÓN DE ESTADO ---
if 'preguntas_falladas' not in st.session_state:
    st.session_state.preguntas_falladas = {} # {índice: conteo_fallos}
if 'historial_simulacro' not in st.session_state:
    st.session_state.historial_simulacro = []

# --- SIDEBAR ---
st.sidebar.title("🌙 Menú de Secuencia")
modo = st.sidebar.radio("Selecciona Modo:", ["Práctica Libre", "Simulacro UdeA", "Repetición Espaciada"])
categoria = st.sidebar.selectbox("Categoría:", ["Todas"] + list(df['Categoría'].unique()))

# --- LÓGICA DE FILTRADO ---
def obtener_preguntas():
    temp_df = df if categoria == "Todas" else df[df['Categoría'] == categoria]
    
    if modo == "Repetición Espaciada":
        # Priorizar preguntas con más fallos en el historial
        indices_fallados = list(st.session_state.preguntas_falladas.keys())
        if indices_fallados:
            return temp_df.iloc[indices_fallados].sample(frac=1)
    
    if modo == "Simulacro UdeA":
        return temp_df.sample(n=min(20, len(temp_df))) # Simulacro de 20 preguntas
    
    return temp_df.sample(frac=1)

# --- INTERFAZ DE CUESTIONARIO ---
st.title(f"✨ Modo {modo}")

if 'lista_preguntas' not in st.session_state or st.sidebar.button("Reiniciar Cuestionario"):
    st.session_state.lista_preguntas = obtener_preguntas()
    st.session_state.indice_actual = 0
    st.session_state.aciertos = 0
    st.session_state.respuestas_simulacro = []

if st.session_state.indice_actual < len(st.session_state.lista_preguntas):
    pregunta_actual = st.session_state.lista_preguntas.iloc[st.session_state.indice_actual]
    
    st.write(f"**Pregunta {st.session_state.indice_actual + 1}:**")
    st.subheader(pregunta_actual['Pregunta'])
    
    opciones = [pregunta_actual['Opción A'], pregunta_actual['Opción B'], 
                pregunta_actual['Opción C'], pregunta_actual['Opción D']]
    
    seleccion = st.radio("Elige tu respuesta:", opciones, key=f"p_{st.session_state.indice_actual}")

    if st.button("Siguiente Pregunta ➡️"):
        es_correcta = (seleccion == pregunta_actual['Respuesta Correcta'])
        
        # Guardar si falló para Repetición Espaciada
        idx_original = pregunta_actual.name
        if not es_correcta:
            st.session_state.preguntas_falladas[idx_original] = st.session_state.preguntas_falladas.get(idx_original, 0) + 1
        
        if modo == "Práctica Libre":
            if es_correcta:
                st.success("¡Correcto, Onii-san! ✨")
            else:
                st.error(f"Oh no... La respuesta era: {pregunta_actual['Respuesta Correcta']}")
                st.info(f"Nota: {pregunta_actual['Explicación']}")
        
        if es_correcta: st.session_state.aciertos += 1
        st.session_state.indice_actual += 1
        st.rerun()

else:
    st.balloons()
    st.header("¡Cuestionario Finalizado!")
    st.metric("Puntaje Final", f"{st.session_state.aciertos}/{len(st.session_state.lista_preguntas)}")
    if st.button("Volver a empezar"):
        st.session_state.indice_actual = 0
        st.rerun()
