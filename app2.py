import streamlit as st
import pandas as pd
import random
import os
import re

# --- CONFIGURACIÓN DE ESCENA ---
st.set_page_config(page_title="UdeA Mastery Pro", page_icon="🏥", layout="wide")

# CSS: FUENTE GRANDE, INTERFAZ LIMPIA Y COLORES DE ALTO CONTRASTE
st.markdown("""
    <style>
    .stApp { background-color: #f8faff; }
    .main-card {
        background-color: #ffffff; padding: 40px; border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05); color: #1a1a1a !important;
        margin-bottom: 25px; border-top: 10px solid #2e7bcf;
    }
    .question-text { font-size: 1.9rem !important; font-weight: 800; color: #0c243d !important; line-height: 1.4; }
    .stRadio > label { 
        font-size: 1.4rem !important; color: #334155 !important; 
        background: #f1f5f9; padding: 18px 25px; border-radius: 12px; 
        margin-bottom: 10px; border: 1px solid #e2e8f0;
    }
    /* Forzar que todo texto sea legible y negro */
    p, span, label, div, .stMarkdown { color: #1a1a1a !important; font-size: 1.3rem !important; }
    .stButton>button { font-size: 1.4rem !important; height: 3.5em !important; border-radius: 15px !important; font-weight: bold !important; }
    .retro-text { font-size: 1.5rem !important; font-weight: 500; color: #1e293b !important; background: #f0fdf4; padding: 20px; border-radius: 10px; border-left: 5px solid #22c55e; }
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
        st.error(f"Error cargando base de datos: {e}")
        return None

def get_col(df, options):
    """Busca una columna entre varias opciones posibles"""
    for opt in options:
        for c in df.columns:
            if c.lower() == opt.lower(): return c
    return None

def parse_question(text):
    text = str(text)
    parts = re.split(r'\s*\n?\s*(?=[A-E][\).])', text)
    enunciado = parts[0]
    opciones = [p.strip() for p in parts[1:] if p.strip()]
    return enunciado, opciones

if 'history' not in st.session_state: st.session_state.history = {}
if 'current_idx' not in st.session_state: st.session_state.current_idx = None
if 'answered' not in st.session_state: st.session_state.answered = False
if 'exam_questions' not in st.session_state: st.session_state.exam_questions = []

def main():
    df = load_data()
    if df is None: return

    # --- MAPEADO DINÁMICO DE COLUMNAS ---
    col_pregunta = get_col(df, ['Pregunta', 'Enunciado'])
    col_respuesta = get_col(df, ['Respuesta correcta', 'Respuesta', 'Correcta'])
    col_retro = get_col(df, ['Retroalimentación', 'Explicación', 'Retro'])

    if not col_pregunta or not col_respuesta:
        st.error(f"⚠️ No encontré las columnas necesarias. Columnas en tu Excel: {list(df.columns)}")
        return

    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=130)
        st.title("UdeA Mastery")
        modo = st.selectbox("Elegir Modo:", ["Repetición Espaciada", "Examen UdeA (70 Preguntas)"])
        if st.button("🔄 Reiniciar Todo"):
            st.session_state.clear()
            st.rerun()

    # --- MODO EXAMEN (70 PREG) ---
    if modo == "Examen UdeA (70 Preguntas)":
        st.header("📋 Simulacro Oficial: 70 Preguntas")
        if not st.session_state.exam_questions:
            if st.button("🚀 INICIAR EXAMEN"):
                n = min(len(df), 70)
                st.session_state.exam_questions = df.sample(n).to_dict('records')
                st.session_state.exam_idx = 0
                st.session_state.exam_answers = []
                st.rerun()
            return

        idx = st.session_state.exam_idx
        total = len(st.session_state.exam_questions)
        
        if idx < total:
            q = st.session_state.exam_questions[idx]
            enunciado, opciones = parse_question(q[col_pregunta])
            st.progress(idx / total)
            st.write(f"**Pregunta {idx+1} de {total}**")
            st.markdown(f'<div class="main-card"><div class="question-text">{enunciado}</div></div>', unsafe_allow_html=True)
            sel = st.radio("Opciones:", opciones, key=f"ex_{idx}", index=None)
            
            if st.button("Siguiente ➡️"):
                if sel:
                    st.session_state.exam_answers.append({'sel': sel[0].upper(), 'correcta': str(q[col_respuesta]).strip().upper()})
                    st.session_state.exam_idx += 1
                    st.rerun()
        else:
            aciertos = sum(1 for a in st.session_state.exam_answers if a['sel'] == a['correcta'])
            st.balloons()
            st.markdown(f'<div class="main-card" style="text-align:center;"><h1>Simulacro Terminado</h1>'
                        f'<h2 style="color:#2e7bcf; font-size:4rem;">{aciertos} / {total}</h2>'
                        f'<h3>Puntaje: {(aciertos/total)*100:.1f}%</h3></div>', unsafe_allow_html=True)
            if st.button("Cerrar Examen"):
                st.session_state.exam_questions = []
                st.rerun()
        return

    # --- MODO REPASO ---
    if st.session_state.current_idx is None:
        st.session_state.current_idx = random.randint(0, len(df)-1)

    q = df.iloc[st.session_state.current_idx]
    enunciado, opciones = parse_question(q[col_pregunta])

    st.markdown(f'<div class="main-card"><div class="question-text">{enunciado}</div></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        sel = st.radio("Selecciona tu respuesta:", opciones, index=None)
        if st.button("Verificar 🛡️"):
            if sel:
                st.session_state.answered = True
                correcta = str(q[col_respuesta]).strip().upper()
                st.session_state.is_correct = sel[0].upper() == correcta
                st.session_state.history[q['id_p']] = {'score': 1 if st.session_state.is_correct else 0}
                st.rerun()
    else:
        if st.session_state.is_correct: st.success("### ✅ ¡CORRECTO!")
        else: st.error(f"### ❌ INCORRECTO. La respuesta era: {q[col_respuesta]}")
        
        # MOSTRAR RETROALIMENTACIÓN SIEMPRE DESPUÉS DE RESPONDER
        if col_retro and pd.notna(q[col_retro]):
            st.markdown(f'<div class="retro-text"><b>Retroalimentación:</b><br>{q[col_retro]}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta ➡️"):
            st.session_state.current_idx = None
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
