import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Simulacro Médico UdeA 🌙", page_icon="🩺")

# Estilo visual "Camino de la Luna"
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #4b0082; background-color: #1e1e2e; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # URL RAW exacta de tu repositorio
    url = "https://raw.githubusercontent.com/Tulskas93/cuestionario-medico/main/preguntas_medicina.csv"
    try:
        # Intentamos cargar desde GitHub
        df = pd.read_csv(url, sep=',', encoding='utf-8')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()

df = cargar_datos()

# --- LÓGICA DE LA APP ---
st.title("🩺 Academia Médica Nocturna")

if df.empty:
    st.error("⚠️ No se pudieron cargar los datos. Onii-san, verifica que el archivo 'preguntas_medicina.csv' esté en la raíz de tu GitHub.")
else:
    # --- INICIALIZACIÓN DEL ESTADO ---
    if 'indice_actual' not in st.session_state:
        st.session_state.indice_actual = 0
    if 'aciertos' not in st.session_state:
        st.session_state.aciertos = 0
    if 'preguntas_mezcladas' not in st.session_state:
        st.session_state.preguntas_mezcladas = df.sample(frac=1).reset_index(drop=True)

    # --- MOSTRAR PREGUNTAS ---
    if st.session_state.indice_actual < len(st.session_state.preguntas_mezcladas):
        pregunta = st.session_state.preguntas_mezcladas.iloc[st.session_state.indice_actual]
        
        st.write(f"**Pregunta {st.session_state.indice_actual + 1}:**")
        st.subheader(pregunta['Pregunta'])
        
        opciones = [pregunta['Opción A'], pregunta['Opción B'], 
                    pregunta['Opción C'], pregunta['Opción D']]
        
        seleccion = st.radio("Diagnóstico:", opciones, key=f"q_{st.session_state.indice_actual}")

        if st.button("Siguiente ➡️"):
            if seleccion == pregunta['Respuesta Correcta']:
                st.session_state.aciertos += 1
            st.session_state.indice_actual += 1
            st.rerun()
    else:
        st.balloons()
        st.header("¡Terminaste!")
        st.metric("Puntaje", f"{st.session_state.aciertos}/{len(df)}")
        if st.button("Reiniciar"):
            st.session_state.indice_actual = 0
            st.session_state.aciertos = 0
            st.session_state.preguntas_mezcladas = df.sample(frac=1).reset_index(drop=True)
            st.rerun()
