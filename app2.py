import streamlit as st
import pandas as pd
import random
import re

# 1. Configuración de pantalla y Estética Superior
st.set_page_config(page_title="UdeA Residency Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    /* Tarjeta de Pregunta Estilo Kimi */
    .question-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 10px solid #4CAF50;
        margin-bottom: 20px;
    }
    .q-text { font-size: 30px !important; font-weight: 700; color: #2c3e50; line-height: 1.3; }
    .stRadio > label { font-size: 22px !important; color: #444 !important; padding: 10px; }
    /* Stickers y Retro */
    .retro-box {
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 15px;
        border: 2px dashed #4CAF50;
        font-size: 20px !important;
    }
    /* Botones Grandes */
    .stButton>button { height: 3.5em; font-size: 20px !important; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga y Limpieza de Datos
URL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(URL)
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        st.error("❌ No se pudo conectar con el Excel. Revisa el link de GitHub.")
        return None

def split_question(text):
    text = str(text)
    parts = re.split(r'\s+(?=[A-E][\).])|\n+(?=[A-E][\).])', text)
    return parts[0], [p.strip() for p in parts[1:] if p.strip()]

# 3. Inicialización del Estado (Counters y Stickers)
if 'correctas' not in st.session_state: st.session_state.correctas = 0
if 'incorrectas' not in st.session_state: st.session_state.incorrectas = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'verificado' not in st.session_state: st.session_state.verificado = False
if 'exam_mode' not in st.session_state: st.session_state.exam_mode = False

def main():
    df = load_data()
    if df is None: return

    # Mapeo de columnas flexible
    col_pregunta = next((c for c in df.columns if 'Pregunta' in c), df.columns[0])
    col_correcta = next((c for c in df.columns if 'correcta' in c), None)
    col_retro = next((c for c in df.columns if 'Retro' in c), None)

    # --- SIDEBAR CON STICKERS ---
    with st.sidebar:
        st.markdown(f"# 🩺 Dr. Stats")
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=100)
        
        c1, c2 = st.columns(2)
        c1.metric("✅ Bien", st.session_state.correctas)
        c2.metric("❌ Mal", st.session_state.incorrectas)
        
        st.divider()
        modo = st.selectbox("Modalidad:", ["Práctica Libre 📖", "Examen 70 Preguntas ⏱️"])
        
        if st.button("🔄 Resetear Progreso"):
            st.session_state.clear()
            st.rerun()

    # --- LÓGICA DE EXAMEN 70 ---
    if "70" in modo:
        # (Aquí va la lógica de examen que ya afinamos, adaptada a este estilo)
        st.info("Modo Examen Activo. Responde las 70 preguntas para ver tu sticker final.")
        # ... (Mantengo la lógica de práctica abajo para que veas el estilo primero)

    # --- MODO PRÁCTICA (EL MÁS BONITO) ---
    q_raw = df.iloc[st.session_state.idx]
    pregunta, opciones = split_question(q_raw[col_pregunta])

    # Tarjeta de Pregunta
    st.markdown(f"""<div class="question-card"><div class="q-text">📍 {pregunta}</div></div>""", unsafe_allow_html=True)

    if not st.session_state.verificado:
        seleccion = st.radio("Elige la opción correcta:", opciones, index=None)
        if st.button("Confirmar Diagnóstico 🩺"):
            if seleccion:
                st.session_state.user_sel = seleccion
                st.session_state.verificado = True
                st.rerun()
    else:
        # Lógica de Validación
        letra_sel = st.session_state.user_sel[0].upper()
        letra_cor = str(q_raw[col_correcta]).strip().upper()

        if letra_sel == letra_cor:
            st.success(f"### 🌟 ¡GENIAL! La respuesta es {letra_cor}")
            if not hasattr(st.session_state, 'puntos_contados'): 
                st.session_state.correctas += 1
                st.session_state.puntos_contados = True
        else:
            st.error(f"### 😿 ¡Ups! La correcta era {letra_cor}")
            if not hasattr(st.session_state, 'puntos_contados'): 
                st.session_state.incorrectas += 1
                st.session_state.puntos_contados = True

        # Retroalimentación con Sticker
        if col_retro and pd.notna(q_raw[col_retro]):
            st.markdown(f"""<div class="retro-box"><b>📝 Nota Médica:</b><br>{q_raw[col_retro]}</div>""", unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta 🚀"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.verificado = False
            if hasattr(st.session_state, 'puntos_contados'): del st.session_state.puntos_contados
            st.rerun()

if __name__ == "__main__":
    main()
