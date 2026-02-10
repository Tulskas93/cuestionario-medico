import streamlit as st
import pandas as pd
import random
import plotly.express as px
import os
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="UdeA Mastery Pro", page_icon="🏥", layout="wide")

# --- CSS: INTERFAZ LIMPIA Y LEGIBLE ---
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-card {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        color: #1a1a1a;
        margin-bottom: 25px;
        border-left: 10px solid #1f77b4;
    }
    .question-text {
        font-size: 1.4rem;
        font-weight: 600;
        color: #2c3e50;
    }
    .stRadio > label { font-size: 1.1rem !important; color: #34495e !important; font-weight: 500; }
    /* Fix para asegurar que el texto sea negro y no herede gris oscuro */
    p, span, label { color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

URL_EXCEL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_excel(URL_EXCEL)
        df.columns = [str(c).strip() for c in df.columns]
        df['id_p'] = range(len(df))
        return df
    except Exception as e:
        st.error(f"Error al cargar datos del repositorio: {e}")
        return None

def parse_question(text):
    text = str(text)
    # Detecta saltos de línea o espacios que preceden a A), B), C)...
    parts = re.split(r'\s*\n?\s*(?=[A-E][\).])', text)
    enunciado = parts[0]
    opciones = [p.strip() for p in parts[1:] if p.strip()]
    return enunciado, opciones

# --- ESTADO DE LA SESIÓN (PERSISTENCIA) ---
if 'history' not in st.session_state: st.session_state.history = {}
if 'current_idx' not in st.session_state: st.session_state.current_idx = None
if 'answered' not in st.session_state: st.session_state.answered = False
if 'exam_mode' not in st.session_state: st.session_state.exam_mode = False
if 'exam_questions' not in st.session_state: st.session_state.exam_questions = []

def main():
    df = load_data()
    if df is None: return

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=120)
        st.title("Med-Trainer UdeA")
        modo = st.selectbox("Elegir Modo:", ["Repetición Espaciada", "Random", "Examen UdeA (Simulacro)"])
        
        st.divider()
        if st.button("Resetear Progreso"):
            st.session_state.clear()
            st.rerun()

    # --- MODO EXAMEN UdeA ---
    if modo == "Examen UdeA (Simulacro)":
        st.header("⏱️ Simulacro Real UdeA")
        if not st.session_state.exam_questions:
            if st.button("Comenzar Examen (10 preguntas)"):
                st.session_state.exam_questions = df.sample(10).to_dict('records')
                st.session_state.exam_idx = 0
                st.session_state.exam_answers = []
                st.rerun()
            return

        idx = st.session_state.exam_idx
        if idx < len(st.session_state.exam_questions):
            q = st.session_state.exam_questions[idx]
            enunciado, opciones = parse_question(q['Pregunta'])
            
            st.progress((idx) / 10)
            st.markdown(f'<div class="main-card"><p class="question-text">{enunciado}</p></div>', unsafe_allow_html=True)
            
            sel = st.radio(f"Pregunta {idx+1} de 10:", opciones, key=f"ex_{idx}", index=None)
            
            if st.button("Siguiente ➡️"):
                if sel:
                    st.session_state.exam_answers.append({'sel': sel[0].upper(), 'correcta': str(q['Respuesta']).strip().upper()})
                    st.session_state.exam_idx += 1
                    st.rerun()
                else: st.warning("Selecciona una opción")
        else:
            # Resultados del Examen
            aciertos = sum(1 for a in st.session_state.exam_answers if a['sel'] == a['correcta'])
            st.balloons()
            st.markdown(f'<div class="main-card"><h2>Resultado: {aciertos}/10</h2></div>', unsafe_allow_html=True)
            if st.button("Finalizar y volver"):
                st.session_state.exam_questions = []
                st.rerun()
        return

    # --- MODOS DE REPASO (SR / RANDOM) ---
    if st.session_state.current_idx is None:
        if modo == "Repetición Espaciada" and st.session_state.history:
            falladas = [id for id, data in st.session_state.history.items() if data['score'] == 0]
            if falladas and random.random() < 0.5:
                st.session_state.current_idx = random.choice(falladas)
            else: st.session_state.current_idx = random.randint(0, len(df)-1)
        else: st.session_state.current_idx = random.randint(0, len(df)-1)

    q = df.iloc[st.session_state.current_idx]
    enunciado, opciones = parse_question(q['Pregunta'])

    # Métricas
    c1, c2 = st.columns(2)
    c1.metric("Preguntas en Memoria", len(st.session_state.history))
    c2.metric("Puntos XP", len(st.session_state.history) * 10)

    st.markdown(f'<div class="main-card"><p class="question-text">{enunciado}</p></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        sel = st.radio("Selecciona tu respuesta:", opciones, index=None)
        if st.button("Verificar Respuesta 🛡️"):
            if sel:
                st.session_state.answered = True
                correcta = str(q['Respuesta']).strip().upper()
                st.session_state.is_correct = sel[0].upper() == correcta
                st.session_state.history[q['id_p']] = {'score': 1 if st.session_state.is_correct else 0}
                st.rerun()
    else:
        if st.session_state.is_correct: st.success("¡Correcto! Sigue así, doctor.")
        else: st.error(f"Incorrecto. La respuesta correcta era: {q['Respuesta']}")
        
        with st.expander("📚 Ver Retroalimentación Clínica", expanded=True):
            st.write(q['Retroalimentación'])
        
        if st.button("Siguiente Pregunta ➡️"):
            st.session_state.current_idx = None
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
