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

# --- CARGA DE DATOS ---
@st.cache_data(show_spinner="Invocando el conocimiento de la Luna...")
def cargar_datos():
    # URL RAW exacta de tu repositorio
    url = "https://raw.githubusercontent.com/Tulskas93/cuestionario-medico/main/preguntas_medicina.csv"
    try:
        # Forzamos la lectura con parámetros de seguridad
        df = pd.read_csv(url, sep=',', encoding='utf-8', on_bad_lines='skip')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return None

df = cargar_datos()

# --- VALIDACIÓN INICIAL ---
if df is None or df.empty:
    st.error("⚠️ Onii-san, no pude leer el CSV. Verifica que el archivo esté en GitHub con el nombre 'preguntas_medicina.csv'")
    st.info("Si acabas de subir el archivo, espera 30 segundos y dale a 'Rerun' en el menú de arriba.")
    st.stop()

# --- INICIALIZACIÓN DEL ESTADO ---
if 'preguntas_falladas' not in st.session_state:
    st.session_state.preguntas_falladas = set() # Usamos set para no repetir índices
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
            st.sidebar.warning("¡Aún no has fallado preguntas, Vampiro!")
            st.session_state.lista_preguntas = df.sample(frac=1)
        else:
            indices = list(st.session_state.preguntas_falladas)
            st.session_state.lista_preguntas = df.loc[indices].sample(frac=1)
    elif modo == "Simulacro UdeA":
        # Simulacro de 20 preguntas aleatorias
        st.session_state.lista_preguntas = df.sample(n=min(20, len(df)))
    else:
        # Mezclar todo
        st.session_state.lista_preguntas = df.sample(frac=1)
    
    st.session_state.indice_actual = 0
    st.session_state.aciertos = 0
    st.rerun()

# --- CUERPO PRINCIPAL ---
st.title("🩺 Academia Médica Nocturna")

if st.session_state.lista_preguntas.empty:
    st.info("Selecciona un modo en el menú lateral y dale a 'Generar' para empezar.")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJid3R6bmJ6bmJ6bmJ6bmJ6bmJ6bmJ6bmJ6bmJ6bmJ6bmJ6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/3o7TKMGpxxcaOXYTTO/giphy.gif", width=300)
elif st.session_state.indice_actual < len(st.session_state.lista_preguntas):
    
    pregunta = st.session_state.lista_preguntas.iloc[st.session_state.indice_actual]
    
    # Progreso visual
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
        es_correcta = (seleccion == pregunta['Respuesta Correcta'])
        
        if es_correcta:
            st.session_state.aciertos += 1
            if modo != "Simulacro UdeA": st.success("¡Excelente, Onii-san! ✨")
        else:
            # Guardar para repetición espaciada usando el índice original del DataFrame
            idx_original = pregunta.name
            st.session_state.preguntas_falladas.add(idx_original)
            if modo != "Simulacro UdeA": 
                st.error(f"Incorrecto. La respuesta era: {pregunta['Respuesta Correcta']}")
        
        # Pequeña pausa para ver la respuesta si no es simulacro
        if modo != "Simulacro UdeA":
            time.sleep(1)
            
        st.session_state.indice_actual += 1
        st.rerun()

else:
    # --- RESULTADOS FINALES ---
    st.balloons()
    st.header("¡Misión Cumplida! 🦇")
    final_score = st.session_state.aciertos
    total_preg = len(st.session_state.lista_preguntas)
    
    st.metric("Puntaje Final", f"{final_score}/{total_preg}")
    
    if (final_score/total_preg) > 0.8:
        st.success("¡Nivel de Residente alcanzado! 🎖️")
    else:
        st.warning("Hay que seguir digiriendo la poción de conocimiento.")
        
    if st.button("🔄 Volver al Inicio"):
        st.session_state.lista_preguntas = pd.DataFrame()
        st.rerun()
