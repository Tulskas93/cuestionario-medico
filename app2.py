import streamlit as st
import pandas as pd
import random
import re

# 1. ESTÉTICA (KIMI-STYLE)
st.set_page_config(page_title="UdeA Mastery", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .q-card { 
        background-color: white; padding: 30px; border-radius: 15px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-left: 10px solid #2e7bcf;
    }
    .q-text { font-size: 30px !important; font-weight: bold; color: #1a1a1a; }
    .stRadio p { font-size: 24px !important; color: #333; }
    .stButton>button { height: 3em; font-size: 20px !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARGA DE DATOS
@st.cache_data
def load_data():
    url = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"
    return pd.read_excel(url)

# 3. EL PARSER DEFINITIVO (POR POSICIÓN DE LETRAS)
def parse_celda(texto):
    texto = str(texto)
    # Buscamos dónde empieza la "A)" para separar enunciado de opciones
    split_punto = texto.find("A)")
    if split_punto == -1: split_punto = texto.find("A.") # Intento con punto
    
    enunciado = texto[:split_punto].strip()
    resto = texto[split_punto:]
    
    # Buscamos la respuesta (ej: "Respuesta: B")
    res_match = re.search(r'Respuesta:\s*([A-E])', texto, re.IGNORECASE)
    correcta = res_match.group(1).upper() if res_match else "A"
    
    # Separamos opciones por letras A) B) C) D) E)
    opciones = re.split(r'\s*(?=[A-E][\)\.])', resto)
    opciones = [o.strip() for o in opciones if len(o.strip()) > 1]
    # Limpiamos la palabra "Respuesta" de la última opción
    if opciones:
        opciones[-1] = opciones[-1].split("Respuesta")[0].strip()
        
    return enunciado, opciones, correcta

# 4. LÓGICA DE LA APP
def main():
    df = load_data()
    if 'idx' not in st.session_state: st.session_state.idx = 0
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'answered' not in st.session_state: st.session_state.answered = False

    # Sidebar
    st.sidebar.title("📊 Progreso")
    st.sidebar.metric("Aciertos", st.session_state.score)
    if st.sidebar.button("Resetear"):
        st.session_state.clear()
        st.rerun()

    # Pregunta Actual
    fila = df.iloc[st.session_state.idx][0]
    enunciado, opciones, correcta = parse_celda(fila)

    st.markdown(f'<div class="q-card"><p class="q-text">{enunciado}</p></div>', unsafe_allow_html=True)
    st.write("---")

    if not st.session_state.answered:
        seleccion = st.radio("Selecciona una respuesta:", opciones, index=None)
        if st.button("Confirmar ✅"):
            if seleccion:
                st.session_state.user_sel = seleccion
                st.session_state.answered = True
                if seleccion.strip().startswith(correcta):
                    st.session_state.score += 1
                st.rerun()
    else:
        if st.session_state.user_sel.strip().startswith(correcta):
            st.success(f"🌟 ¡CORRECTO! La respuesta es {correcta}")
        else:
            st.error(f"❌ INCORRECTO. La respuesta era {correcta}")
        
        if st.button("Siguiente Pregunta ➡️"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
