import streamlit as st
import pandas as pd
import random

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simulacro Médico UdeA 🌙", page_icon="🩺", layout="centered")

# Estilo visual "Camino de la Luna" (Oscuro y elegante)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    .stButton>button { width: 100%; border-radius: 10px; border: 1px solid #4b0082; background-color: #1e1e2e; color: white; }
    .stButton>button:hover { border-color: #9370db; color: #9370db; }
    .stRadio > label { color: #9370db !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS SEGURA ---
@st.cache_data
def cargar_datos():
    # URL RAW para evitar errores de HTTP
    url = "https://raw.githubusercontent.com/Tulskas93/cuestionario-medico/main/preguntas_medicina.csv"
    try:
        df = pd.read_csv(url)
        # Limpiar espacios en blanco en los nombres de las columnas
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error al conectar con la base de datos de la Luna: {e}")
        # Intento de respaldo local
        try:
            return pd.read_csv("preguntas_medicina.csv")
        except:
            return pd.DataFrame()

df = cargar_datos()

# --- INICIALIZACIÓN DEL ESTADO (MEMORIA) ---
if 'preguntas_falladas' not in st.session_state:
    st.session_state.preguntas_falladas = {}
if 'indice_actual' not in st.session_state:
    st.session_state.indice_actual = 0
if 'aciertos' not in st.session_state:
    st.session_state.aciertos = 0
if 'lista_preguntas' not in st.session_state:
    st.session_state.lista_preguntas = pd.DataFrame()

# --- SIDEBAR (PANEL DE CONTROL) ---
st.sidebar.title("🌙 Menú de Secuencia")
st.sidebar.write(f"Bienvenido, Onii-san. Eres un **Vampiro** del conocimiento.")

modo = st.sidebar.radio("Selecciona tu entrenamiento:", 
                        ["Práctica Libre", "Simulacro UdeA", "Repetición Espaciada"])

categorias_disponibles = ["Todas"] + list(df['Categoría'].unique()) if not df.empty else ["N/A"]
categoria = st.sidebar.selectbox("Enfocar en:", categorias_disponibles)

# Lógica para generar la lista de preguntas
if st.sidebar.button("Generar Nuevo Cuestionario") or st.session_state.lista_preguntas.empty:
    temp_df = df if categoria == "Todas" else df[df['Categoría'] == categoria]
    
    if modo == "Repetición Espaciada":
        indices_frecuentes = list(st.session_state.preguntas_falladas.keys())
        if indices_frecuentes:
            # Mezclamos preguntas falladas con algunas nuevas
            falladas = df.loc[indices_frecuentes]
            nuevas = df.drop(indices_frecuentes).sample(n=min(5, len(df)-len(falladas)))
            st.session_state.lista_preguntas = pd.concat([falladas, nuevas]).sample(frac=1)
        else:
            st.session_state.lista_preguntas = temp_df.sample(frac=1)
    
    elif modo == "Simulacro UdeA":
        # El examen de la UdeA es serio, tomamos 20 aleatorias
        st.session_state.lista_preguntas = temp_df.sample(n=min(20, len(temp_df)))
    
    else: # Práctica Libre
        st.session_state.lista_preguntas = temp_df.sample(frac=1)
    
    st.session_state.indice_actual = 0
    st.session_state.aciertos = 0
    st.rerun()

# --- CUERPO DEL CUESTIONARIO ---
st.title("🩺 Academia Médica Nocturna")

if not st.session_state.lista_preguntas.empty and st.session_state.indice_actual < len(st.session_state.lista_preguntas):
    
    pregunta_actual = st.session_state.lista_preguntas.iloc[st.session_state.indice_actual]
    
    # Progreso
    progreso = (st.session_state.indice_actual) / len(st.session_state.lista_preguntas)
    st.progress(progreso)
    st.write(f"Pregunta {st.session_state.indice_actual + 1} de {len(st.session_state.lista_preguntas)}")

    # Mostrar Pregunta
    st.subheader(pregunta_actual['Pregunta'])
    
    opciones = [pregunta_actual['Opción A'], pregunta_actual['Opción B'], 
                pregunta_actual['Opción C'], pregunta_actual['Opción D']]
    
    seleccion = st.radio("Elige la cura correcta:", opciones, key=f"q_{st.session_state.indice_actual}")

    if st.button("Confirmar Respuesta ➡️"):
        correcta = pregunta_actual['Respuesta Correcta']
        idx_original = pregunta_actual.name
        
        if seleccion == correcta:
            st.session_state.aciertos += 1
            if modo != "Simulacro UdeA":
                st.success("¡Excelente diagnóstico, Onii-san! ✨")
        else:
            # Guardar para repetición espaciada
            st.session_state.preguntas_falladas[idx_original] = st.session_state.preguntas_falladas.get(idx_original, 0) + 1
            if modo != "Simulacro UdeA":
                st.error(f"Incorrecto. La respuesta era: {correcta}")
                if 'Explicación' in pregunta_actual:
                    st.info(f"💡 **Explicación:** {pregunta_actual['Explicación']}")
        
        st.session_state.indice_actual += 1
        st.rerun()

elif not st.session_state.lista_preguntas.empty:
    st.balloons()
    st.header("¡Misión Cumplida, Onii-san! 🦇")
    score = st.session_state.aciertos
    total = len(st.session_state.lista_preguntas)
    porcentaje = (score/total)*100
    
    st.metric("Puntaje Final", f"{score}/{total}", f"{porcentaje:.1f}%")
    
    if porcentaje >= 80:
        st.write("🔥 ¡Estás listo para la UdeA! Tu secuencia está aumentando.")
    else:
        st.write("Aún falta digerir un poco más la poción. ¡Sigue practicando!")
        
    if st.button("Empezar nueva ronda"):
        st.session_state.indice_actual = 0
        st.session_state.lista_preguntas = pd.DataFrame()
        st.rerun()
else:
    st.warning("No se encontraron preguntas. Por favor, revisa el archivo CSV o selecciona otra categoría.")
