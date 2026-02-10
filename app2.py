 import streamlit as st
import pandas as pd
import random
import re

# --- 1. CONFIGURACIÓN Y ESTILO (ESTÉTICA UDEA) ---
st.set_page_config(page_title="UdeA Mastery Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f7f9; }
    .main-card {
        background-color: #ffffff;
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-top: 10px solid #2e7bcf;
        margin-bottom: 25px;
    }
    .q-text { font-size: 32px !important; font-weight: 800; color: #1a1a1a; line-height: 1.3; }
    .stRadio > label { 
        font-size: 24px !important; color: #333 !important; 
        background: #f8f9fa; padding: 15px; border-radius: 12px;
        border: 1px solid #dee2e6; margin-bottom: 10px;
    }
    .retro-box {
        background-color: #e7f3ff;
        padding: 25px;
        border-radius: 15px;
        border-left: 10px solid #2e7bcf;
        font-size: 22px !important;
        color: #1a1a1a !important;
        margin-top: 20px;
    }
    .stButton>button { height: 3.5em; font-size: 22px !important; font-weight: bold; border-radius: 15px; }
    [data-testid="stMetricValue"] { color: #2e7bcf !important; font-size: 40px !important; }
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
    """
    Separa una celda única en: Enunciado, Opciones, Respuesta y Retroalimentación.
    """
    text = str(text)
    
    # 1. Extraer Respuesta Correcta (ej: "Respuesta: A")
    ans_match = re.search(r'(?:Respuesta|Correcta|R/):\s*([A-E])', text, re.IGNORECASE)
    respuesta = ans_match.group(1).upper() if ans_match else "A"
    
    # 2. Dividir por opciones A), B), C)...
    # Cortamos el texto donde veamos el patrón de opciones
    parts = re.split(r'\s*(?=[A-E][\).])', text)
    
    enunciado = parts[0].strip()
    
    # 3. Identificar opciones y posible retroalimentación
    opciones = []
    retro = ""
    
    for p in parts[1:]:
        content = p.strip()
        # Si la parte empieza por una opción válida (A-E), es opción
        if re.match(r'^[A-E][\).]', content):
            # Limpiar etiquetas de "Respuesta:" dentro de la opción
            clean_option = re.sub(r'(?:Respuesta|Correcta|R/):\s*[A-E]', '', content, flags=re.IGNORECASE).strip()
            opciones.append(clean_option)
        else:
            retro += content + " "

    return enunciado, opciones, respuesta, retro

# --- 3. ESTADO PERSISTENTE ---
if 'total_correctas' not in st.session_state: st.session_state.total_correctas = 0
if 'total_intentos' not in st.session_state: st.session_state.total_intentos = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'answered' not in st.session_state: st.session_state.answered = False
if 'exam_list' not in st.session_state: st.session_state.exam_list = []

def main():
    df = load_data()
    if df is None:
        st.error("No se pudo cargar el Excel. Revisa el link de GitHub.")
        return

    # --- SIDEBAR: ESTADÍSTICAS Y MODOS ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=120)
        st.title("📊 Mi Progreso")
        st.metric("✅ Aciertos", st.session_state.total_correctas)
        st.metric("📈 Efectividad", f"{(st.session_state.total_correctas/(st.session_state.total_intentos if st.session_state.total_intentos > 0 else 1))*100:.1f}%")
        
        st.divider()
        modo = st.selectbox("Modo de Juego:", ["Estudio Libre 📖", "Simulacro 70 Preguntas ⏱️"])
        
        if st.button("🗑 Reiniciar Todo"):
            st.session_state.clear()
            st.rerun()

    # --- MODO EXAMEN 70 ---
    if "Simulacro" in modo:
        if not st.session_state.exam_list:
            if st.button("🚀 EMPEZAR EXAMEN DE 70"):
                st.session_state.exam_list = df.sample(n=min(70, len(df))).to_dict('records')
                st.session_state.ex_idx = 0
                st.session_state.ex_score = 0
                st.rerun()
            return
        
        actual = st.session_state.ex_idx
        if actual < len(st.session_state.exam_list):
            q_raw = st.session_state.exam_list[actual][df.columns[0]]
            enunciado, opciones, correcta, retro = process_cell(q_raw)
            
            st.write(f"**Pregunta {actual + 1} de {len(st.session_state.exam_list)}**")
            st.markdown(f'<div class="main-card"><div class="q-text">{enunciado}</div></div>', unsafe_allow_html=True)
            
            sel = st.radio("Elige una:", opciones, key=f"ex_{actual}", index=None)
            if st.button("Siguiente ➡️"):
                if sel:
                    if sel[0].upper() == correcta: st.session_state.ex_score += 1
                    st.session_state.ex_idx += 1
                    st.rerun()
        else:
            st.balloons()
            st.success(f"### 🎉 ¡Examen Finalizado! Puntaje: {st.session_state.ex_score} / {len(st.session_state.exam_list)}")
            if st.button("Volver al Inicio"):
                st.session_state.exam_list = []
                st.rerun()
        return

    # --- MODO ESTUDIO LIBRE ---
    q_data = df.iloc[st.session_state.idx][df.columns[0]]
    enunciado, opciones, correcta, retro = process_cell(q_data)

    st.markdown(f'<div class="main-card"><div class="q-text">📍 {enunciado}</div></div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        user_sel = st.radio("Selecciona tu respuesta:", opciones, index=None)
        if st.button("Confirmar Diagnóstico 🩺"):
            if user_sel:
                st.session_state.user_choice = user_sel
                st.session_state.answered = True
                st.session_state.total_intentos += 1
                if user_sel[0].upper() == correcta:
                    st.session_state.total_correctas += 1
                st.rerun()
    else:
        # Resultado
        es_correcta = st.session_state.user_choice[0].upper() == correcta
        if es_correcta:
            st.success(f"### ✅ ¡CORRECTO! La respuesta es {correcta}")
        else:
            st.error(f"### ❌ INCORRECTO. La respuesta correcta era {correcta}")

        # Retroalimentación (Aquí se muestra el texto extraído)
        with st.container():
            st.markdown(f'<div class="retro-box"><b>📖 Explicación / Retroalimentación:</b><br>{retro if len(retro) > 5 else "Analiza las opciones arriba para reforzar el concepto."}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta 🚀"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()
