import streamlit as st
import pandas as pd
import random
import re

# --- CONFIGURACIÓN DE PÁGINA Y ESTILO (KIMI STYLE) ---
st.set_page_config(page_title="UdeA Simulator", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    /* Estilo General */
    .stApp { background-color: #f5f7fa; }
    
    /* Tarjeta de Pregunta */
    .question-card {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border-left: 8px solid #3498db;
        margin-bottom: 20px;
    }
    .q-text { font-size: 28px !important; font-weight: 700; color: #2c3e50; }
    
    /* Opciones grandes */
    .stRadio p { font-size: 22px !important; }
    .stRadio > div { background-color: white; padding: 10px; border-radius: 10px; }
    
    /* Feedback */
    .feedback-good { 
        background-color: #d4edda; color: #155724; 
        padding: 20px; border-radius: 10px; margin-top: 15px; font-size: 20px; 
    }
    .feedback-bad { 
        background-color: #f8d7da; color: #721c24; 
        padding: 20px; border-radius: 10px; margin-top: 15px; font-size: 20px; 
    }
    
    /* Botones */
    .stButton>button { width: 100%; font-size: 20px; font-weight: bold; border-radius: 10px; height: 50px; }
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
URL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(URL)
        return df
    except:
        return None

# --- PARSER: EL CEREBRO QUE ENTIENDE TU FORMATO ---
def parse_question(text):
    text = str(text).strip()
    
    # 1. Buscar la Respuesta Correcta (al final del texto generalmente)
    # Busca "Respuesta: X", "R/ X", "Clave: X"
    match_resp = re.search(r'(?:Respuesta|R\/|Correcta|Clave)[:\.\s-]*([A-E])', text, re.IGNORECASE)
    correcta = match_resp.group(1).upper() if match_resp else "A" # Default A si falla
    
    # 2. Separar el texto para encontrar las opciones
    # Esta Regex busca: Salto de línea o espacio + Letra (A-E) + Paréntesis o Punto
    # Ej: "A)", "A.", " B)", " B."
    parts = re.split(r'(?:\n|\s{2,})(?=[A-E][\)\.])', text)
    
    if len(parts) > 1:
        pregunta = parts[0].strip() # La primera parte es la pregunta
        opciones = [p.strip() for p in parts[1:]] # Las siguientes son opciones
    else:
        # PLAN B: Si no encuentra letras A) B), corta por saltos de línea simples
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if len(lines) >= 2:
            pregunta = lines[0]
            opciones = lines[1:]
        else:
            pregunta = text
            opciones = ["Opción A", "Opción B", "Opción C", "Opción D"] # Fallback total

    # Limpiar la "Respuesta: X" de la última opción para que no se vea
    if opciones:
        opciones[-1] = re.sub(r'(?:Respuesta|R\/|Correcta|Clave)[:\.\s-]*[A-E].*', '', opciones[-1], flags=re.IGNORECASE).strip()
        
    return pregunta, opciones, correcta

# --- LÓGICA DE ESTADO ---
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'score' not in st.session_state: st.session_state.score = 0
if 'fails' not in st.session_state: st.session_state.fails = 0
if 'answered' not in st.session_state: st.session_state.answered = False
if 'exam_list' not in st.session_state: st.session_state.exam_list = []

def main():
    df = load_data()
    if df is None:
        st.error("Error cargando Excel. Verifica URL.")
        return

    # Usamos la PRIMERA columna disponible, sin importar el nombre
    col_data = df.columns[0]

    with st.sidebar:
        st.header("📊 Estadísticas")
        st.metric("Aciertos", st.session_state.score)
        st.metric("Fallos", st.session_state.fails)
        st.divider()
        modo = st.radio("Modo:", ["Práctica Libre", "Examen (70 Preguntas)"])
        if st.button("Reiniciar"):
            st.session_state.clear()
            st.rerun()

    # --- MODO EXAMEN 70 ---
    if modo == "Examen (70 Preguntas)":
        if not st.session_state.exam_list:
            if st.button("Comenzar Simulacro"):
                st.session_state.exam_list = df.sample(min(70, len(df))).to_dict('records')
                st.session_state.ex_idx = 0
                st.session_state.ex_pts = 0
                st.rerun()
            return
        
        idx = st.session_state.ex_idx
        if idx < len(st.session_state.exam_list):
            raw = st.session_state.exam_list[idx][col_data]
            preg, ops, cor = parse_question(raw)
            
            st.markdown(f"### Pregunta {idx+1} / {len(st.session_state.exam_list)}")
            st.progress((idx+1)/len(st.session_state.exam_list))
            
            st.markdown(f'<div class="question-card"><div class="q-text">{preg}</div></div>', unsafe_allow_html=True)
            
            sel = st.radio("Selecciona:", ops, key=f"ex_{idx}", index=None)
            
            if st.button("Siguiente ➡️"):
                if sel:
                    if sel[0].upper() == cor: st.session_state.ex_pts += 1
                    st.session_state.ex_idx += 1
                    st.rerun()
        else:
            st.balloons()
            st.success(f"Examen Terminado. Nota: {st.session_state.ex_pts} / {len(st.session_state.exam_list)}")
            if st.button("Volver"): st.session_state.exam_list = []; st.rerun()
        return

    # --- MODO PRÁCTICA ---
    raw = df.iloc[st.session_state.idx][col_data]
    preg, ops, cor = parse_question(raw)

    st.markdown(f'<div class="question-card"><div class="q-text">{preg}</div></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        user_sel = st.radio("Tu respuesta:", ops, index=None)
        if st.button("Validar"):
            if user_sel:
                st.session_state.last_sel = user_sel
                st.session_state.answered = True
                if user_sel[0].upper() == cor:
                    st.session_state.score += 1
                    st.session_state.last_res = True
                else:
                    st.session_state.fails += 1
                    st.session_state.last_res = False
                st.rerun()
    else:
        # Mostrar resultado
        sel = st.session_state.last_sel
        res = st.session_state.last_res
        
        if res:
            st.markdown(f'<div class="feedback-good">✅ ¡Correcto! Respuesta: {sel}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="feedback-bad">❌ Incorrecto. La correcta era la {cor}</div>', unsafe_allow_html=True)
            
        if st.button("Siguiente Pregunta"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
