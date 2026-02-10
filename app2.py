import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE SESIÓN (EL "SAVE GAME") ---
if 'db_preguntas' not in st.session_state:
    st.session_state.db_preguntas = None
if 'historial' not in st.session_state:
    st.session_state.historial = {} # Para Spaced Repetition {id_pregunta: nivel_dificultad}

def load_data():
    df = pd.read_excel("preguntas.xlsx")
    df.columns = [c.strip() for c in df.columns]
    # Creamos un ID único si no existe para rastrear la repetición
    if 'ID' not in df.columns:
        df['ID'] = range(len(df))
    return df

def main():
    st.set_page_config(page_title="UdeA Med-Training Pro", layout="wide")
    st.title("🩺 UdeA Residency Prep - Spaced Repetition Mode")

    if st.session_state.db_preguntas is None:
        st.session_state.db_preguntas = load_data()

    # --- SIDEBAR: SELECCIÓN DE MODO ---
    with st.sidebar:
        st.header("🎮 Game Settings")
        modo = st.radio("Selecciona tu modo:", 
                        ["Repetición Espaciada (UdeA)", "Simulacro Libre", "Boss Rush (Solo Falladas)"])
        
        filtro_tema = st.multiselect("Filtrar por Especialidad:", 
                                     options=st.session_state.db_preguntas['Especialidad'].unique())

    # --- LÓGICA DE FILTRADO ---
    df_pool = st.session_state.db_preguntas
    if filtro_tema:
        df_pool = df_pool[df_pool['Especialidad'].isin(filtro_tema)]

    # --- MOTOR DE REPETICIÓN ESPACIADA (SIMPLIFICADO) ---
    if modo == "Repetición Espaciada (UdeA)":
        st.caption("🚀 Priorizando preguntas que te cuestan más trabajo...")
        # Aquí filtraríamos preguntas según la "fecha de próximo repaso" 
        # Por ahora, seleccionamos una que no sea la actual
        pregunta = df_pool.sample(1).iloc[0]
    else:
        pregunta = df_pool.sample(1).iloc[0]

    # --- UI DE LA PREGUNTA ---
    with st.container():
        st.markdown(f"### {pregunta['Pregunta']}")
        
        # Opciones (Asumiendo formato estándar A, B, C, D)
        # Nota: Si tu Excel tiene las opciones en columnas separadas, habría que iterarlas aquí
        
        with st.expander("Revelar Respuesta y Retroalimentación"):
            st.success(f"**Respuesta Correcta:** {pregunta['Respuesta correcta']}")
            st.info(f"**Análisis Clínico:** \n {pregunta['Retroalimentación']}")
            
            # Botones de Feedback para Repetición Espaciada
            st.write("---")
            st.write("**¿Qué tan difícil fue?** (Esto ajusta cuándo volverás a verla)")
            col1, col2, col3, col4 = st.columns(4)
            if col1.button("Easy (En 7 días)"): pass
            if col2.button("Good (En 3 días)"): pass
            if col3.button("Hard (Mañana)"): pass
            if col4.button("Again (En 10 min)"): pass

    if st.button("Siguiente Pregunta ➡️"):
        st.rerun()

if __name__ == "__main__":
    main()
