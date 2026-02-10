import streamlit as st
import pandas as pd
import random
import os
import re

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="UdeA Mastery Pro", page_icon="🏥", layout="wide")

# --- CSS: FUENTE GRANDE Y LEGIBILIDAD MÁXIMA ---
st.markdown("""
    <style>
    .stApp { background-color: #f4f7f6; }
    
    /* Tarjeta Principal */
    .main-card {
        background-color: #ffffff;
        padding: 45px;
        border-radius: 25px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        color: #1a1a1a;
        margin-bottom: 30px;
        border-left: 12px solid #2e7bcf;
    }
    
    /* Texto de la Pregunta - TAMAÑO EXTRA */
    .question-text {
        font-size: 1.8rem !important;
        font-weight: 700;
        color: #1a1a1a;
        line-height: 1.5;
        margin-bottom: 20px;
    }
    
    /* Opciones de Radio - TAMAÑO EXTRA */
    .stRadio > label { 
        font-size: 1.4rem !important; 
        color: #2c3e50 !important; 
        font-weight: 500;
        padding: 10px 0px;
    }
    
    /* Estilo para los textos generales */
    p, span, label, .stMarkdown {
        font-size: 1.3rem !important;
        color: #1a1a1a !important;
    }
    
    /* Botones más grandes */
    .stButton>button {
        font-size: 1.4rem !important;
        height: 3.5em !important;
        border-radius: 15px !important;
    }
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
        st.error(f"Error al cargar datos: {e}")
        return None

def parse_question(text):
    text = str(text)
    # Parser para separar enunciado de opciones A, B, C, D
    parts = re.split(r'\s*\n?\s*(?=[A-E][\).])', text)
    enunciado = parts[0]
    opciones = [p.strip() for p in parts[1:] if p.strip()]
    return enunciado, opciones

# --- ESTADO DE LA SESIÓN ---
if 'history' not in st.session_state: st.session_state.history = {}
if 'current_idx' not in st.session_state: st.session_state.current_idx = None
if 'answered' not in st.session_state: st.session_state.answered = False
if 'exam_questions' not in st.session_state: st.session_state.exam_questions = []

def main():
    df = load_data()
    if df is None: return

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=140)
        st.title("Med-Trainer v3.5")
        modo = st.selectbox("Modo de Estudio:", ["Repetición Espaciada", "Random", "Examen UdeA (70 Preguntas)"])
        
        st.divider()
        if st.button("Limpiar Progreso"):
            st.session_state.clear()
            st.rerun()

    # --- MODO EXAMEN UdeA (70 PREGUNTAS) ---
    if modo == "Examen UdeA (70 Preguntas)":
        st.header("⏱️ Simulacro Completo: 70 Preguntas")
        
        if not st.session_state.exam_questions:
            if st.button("🚀 INICIAR SIMULACRO"):
                # Si el excel tiene menos de 70, toma todas las disponibles
                n_preguntas = min(len(df), 70)
                st.session_state.exam_questions = df.sample(n_preguntas).to_dict('records')
                st.session_state.exam_idx = 0
                st.session_state.exam_answers = []
                st.rerun()
            return

        idx = st.session_state.exam_idx
        num_total = len(st.session_state.exam_questions)
        
        if idx < num_total:
            q = st.session_state.exam_questions[idx]
            enunciado, opciones = parse_question(q['Pregunta'])
            
            st.progress((idx) / num_total)
            st.subheader(f"Pregunta {idx + 1} de {num_total}")
            
            st.markdown(f'<div class="main-card"><p class="question-text">{enunciado}</p></div>', unsafe_allow_html=True)
            
            sel = st.radio("Elija su respuesta:", opciones, key=f"ex70_{idx}", index=None)
            
            if st.button("Siguiente ➡️"):
                if sel:
                    st.session_state.exam_answers.append({
                        'sel': sel[0].upper(), 
                        'correcta': str(q['Respuesta']).strip().upper()
                    })
                    st.session_state.exam_idx += 1
                    st.rerun()
                else: st.warning("Por favor seleccione una opción para continuar.")
        else:
            # RESULTADOS FINALES
            aciertos = sum(1 for a in st.session_state.exam_answers if a['sel'] == a['correcta'])
            porcentaje = (aciertos / num_total) * 100
            
            st.balloons()
            st.markdown(f'<div class="main-card" style="text-align:center;">'
                        f'<h1>Resultado Final</h1>'
                        f'<h2 style="color:#2e7bcf;">{aciertos} / {num_total}</h2>'
                        f'<h3>Porcentaje: {porcentaje:.1f}%</h3>'
                        f'</div>', unsafe_allow_html=True)
            
            if st.button("Finalizar y Salir"):
                st.session_state.exam_questions = []
                st.rerun()
        return

    # --- MODO REPASO DIARIO ---
    if st.session_state.current_idx is None:
        if modo == "Repetición Espaciada" and st.session_state.history:
            falladas = [id for id, data in st.session_state.history.items() if data['score'] == 0]
            if falladas and random.random() < 0.6:
                st.session_state.current_idx = random.choice(falladas)
            else: st.session_state.current_idx = random.randint(0, len(df)-1)
        else: st.session_state.current_idx = random.randint(0, len(df)-1)

    q = df.iloc[st.session_state.current_idx]
    enunciado, opciones = parse_question(q['Pregunta'])

    st.markdown(f'<div class="main-card"><p class="question-text">{enunciado}</p></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        sel = st.radio("Opciones disponibles:", opciones, index=None)
        if st.button("Confirmar Respuesta 🛡️"):
            if sel:
                st.session_state.answered = True
                correcta = str(q['Respuesta']).strip().upper()
                st.session_state.is_correct = sel[0].upper() == correcta
                st.session_state.history[q['id_p']] = {'score': 1 if st.session_state.is_correct else 0}
                st.rerun()
    else:
        if st.session_state.is_correct: st.success("### ✅ ¡CORRECTO!")
        else: st.error(f"### ❌ INCORRECTO. La respuesta es: {q['Respuesta']}")
        
        with st.expander("📖 VER RETROALIMENTACIÓN", expanded=True):
            st.markdown(f"#### {q['Retroalimentación']}")
        
        if st.button("Siguiente Pregunta ➡️"):
            st.session_state.current_idx = None
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
