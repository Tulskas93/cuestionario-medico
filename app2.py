 import streamlit as st
import pandas as pd
import random
import re

# --- 1. CONFIGURACIÓN Y ESTÉTICA (FUENTES GIGANTES Y DISEÑO LIMPIO) ---
st.set_page_config(page_title="UdeA Mastery Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border-top: 12px solid #2e7bcf;
        margin-bottom: 25px;
    }
    .q-text { font-size: 34px !important; font-weight: 800; color: #1a1a1a !important; line-height: 1.4; }
    .stRadio > label { 
        font-size: 26px !important; color: #333 !important; 
        background: #f8f9fa; padding: 20px; border-radius: 15px;
        border: 1px solid #dee2e6; margin-bottom: 12px;
        transition: 0.3s;
    }
    .stRadio > label:hover { background: #eef2f7; border-color: #2e7bcf; }
    .retro-box {
        background-color: #e3f2fd;
        padding: 30px;
        border-radius: 20px;
        border-left: 12px solid #2e7bcf;
        font-size: 24px !important;
        color: #0d47a1 !important;
        margin-top: 25px;
    }
    .stButton>button { height: 3.5em; font-size: 22px !important; font-weight: bold; border-radius: 15px; width: 100%; background-color: #2e7bcf !important; color: white !important; }
    [data-testid="stMetricValue"] { color: #2e7bcf !important; font-size: 45px !important; font-weight: bold; }
    p, span, label { color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
URL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(URL)
        return df
    except:
        return None

def process_cell(text):
    text = str(text)
    # 1. Extraer Respuesta (ej: Respuesta: A)
    ans_match = re.search(r'(?:Respuesta|Correcta|R/):\s*([A-E])', text, re.IGNORECASE)
    respuesta = ans_match.group(1).upper() if ans_match else "A"
    
    # 2. Separar enunciado de opciones (A), B), C)...)
    # Quitamos la parte de la respuesta del texto para no ensuciar las opciones
    clean_text = re.sub(r'(?:Respuesta|Correcta|R/):\s*[A-E]', '', text, flags=re.IGNORECASE).strip()
    
    parts = re.split(r'\s*(?=[A-E][\).])', clean_text)
    enunciado = parts[0].strip()
    
    opciones = []
    retro = ""
    for p in parts[1:]:
        content = p.strip()
        if re.match(r'^[A-E][\).]', content):
            opciones.append(content)
        else:
            retro += content + " "
    return enunciado, opciones, respuesta, retro

# --- 3. PERSISTENCIA (ESTADO DE SESIÓN) ---
if 'correctas' not in st.session_state: st.session_state.correctas = 0
if 'intentos' not in st.session_state: st.session_state.intentos = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'answered' not in st.session_state: st.session_state.answered = False
if 'exam_list' not in st.session_state: st.session_state.exam_list = []
if 'ex_idx' not in st.session_state: st.session_state.ex_idx = 0

def main():
    df = load_data()
    if df is None:
        st.error("❌ Error cargando el Excel. Revisa GitHub.")
        return

    # --- SIDEBAR: RENDIMIENTO ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=140)
        st.header("📊 Score Card")
        st.metric("✅ Correctas", st.session_state.correctas)
        eff = (st.session_state.correctas/st.session_state.intentos*100) if st.session_state.intentos > 0 else 0
        st.metric("📈 Eficiencia", f"{eff:.1f}%")
        
        st.divider()
        modo = st.radio("Selecciona tu Modo:", ["📖 Práctica Libre", "⏱️ Examen 70 Preguntas"])
        
        if st.button("🔄 Reiniciar Todo"):
            st.session_state.clear()
            st.rerun()

    # --- LÓGICA MODO EXAMEN 70 ---
    if "70" in modo:
        if not st.session_state.exam_list:
            if st.button("🚀 INICIAR SIMULACRO"):
                st.session_state.exam_list = df.sample(n=min(70, len(df))).to_dict('records')
                st.session_state.ex_idx = 0
                st.session_state.ex_score = 0
                st.rerun()
            return

        actual = st.session_state.ex_idx
        if actual < len(st.session_state.exam_list):
            q_raw = st.session_state.exam_list[actual][df.columns[0]]
            enunciado, opciones, correcta, retro = process_cell(q_raw)
            
            st.write(f"Pregunta {actual + 1} de {len(st.session_state.exam_list)}")
            st.progress((actual + 1) / len(st.session_state.exam_list))
            
            st.markdown(f'<div class="main-card"><div class="q-text">{enunciado}</div></div>', unsafe_allow_html=True)
            sel = st.radio("Selecciona tu respuesta:", opciones, key=f"ex_{actual}", index=None)
            
            if st.button("Siguiente ➡️"):
                if sel:
                    if sel[0].upper() == correcta: st.session_state.ex_score += 1
                    st.session_state.ex_idx += 1
                    st.rerun()
        else:
            st.balloons()
            st.success(f"### 🏆 Simulacro Terminado! Score: {st.session_state.ex_score} / {len(st.session_state.exam_list)}")
            if st.button("Volver al Menú"): 
                st.session_state.exam_list = []
                st.rerun()
        return

    # --- LÓGICA MODO PRÁCTICA LIBRE ---
    q_data = df.iloc[st.session_state.idx][df.columns[0]]
    enunciado, opciones, correcta, retro = process_cell(q_data)

    st.markdown(f'<div class="main-card"><div class="q-text">🩺 {enunciado}</div></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        user_sel = st.radio("Opciones:", opciones, index=None)
        if st.button("Validar Respuesta 🛡️"):
            if user_sel:
                st.session_state.user_choice = user_sel
                st.session_state.answered = True
                st.session_state.intentos += 1
                if user_sel[0].upper() == correcta: st.session_state.correctas += 1
                st.rerun()
    else:
        if st.session_state.user_choice[0].upper() == correcta:
            st.success(f"### ✅ ¡CORRECTO! La respuesta es la {correcta}")
        else:
            st.error(f"### ❌ INCORRECTO. La respuesta correcta era la {correcta}")

        if retro and len(retro) > 5:
            st.markdown(f'<div class="retro-box"><b>📖 Retroalimentación Clínica:</b><br>{retro}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta 🚀"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
