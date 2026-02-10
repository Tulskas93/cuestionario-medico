import streamlit as st
import pandas as pd
import random
import re

# 1. Configuración de pantalla y Estética (Legibilidad Máxima)
st.set_page_config(page_title="UdeA Residency Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .question-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border-top: 10px solid #2e7bcf;
        margin-bottom: 20px;
    }
    .q-text { font-size: 32px !important; font-weight: 700; color: #1a1a1a; line-height: 1.3; }
    .stRadio > label { 
        font-size: 24px !important; 
        color: #333 !important; 
        padding: 15px; 
        background-color: #f8f9fa;
        border-radius: 10px;
        margin-bottom: 5px;
    }
    .retro-box {
        background-color: #e3f2fd;
        padding: 25px;
        border-radius: 15px;
        border-left: 10px solid #2196f3;
        font-size: 22px !important;
        color: #0d47a1 !important;
    }
    .stButton>button { height: 3.5em; font-size: 22px !important; font-weight: bold; border-radius: 12px; }
    /* Forzar texto negro en métricas */
    [data-testid="stMetricValue"] { color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga de Datos
URL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(URL)
        # Limpiar nombres de columnas
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error al conectar con el Excel: {e}")
        return None

# 3. EL MOTOR DE SEPARACIÓN (CORREGIDO)
def split_question(text):
    text = str(text)
    # Busca patrones tipo A), B), C) o A., B., C. ya sea con salto de línea o espacio
    pattern = r'\s+(?=[A-E][\).])|\n+(?=[A-E][\).])'
    parts = re.split(pattern, text)
    
    enunciado = parts[0].strip()
    opciones = [p.strip() for p in parts[1:] if p.strip()]
    
    # Si el regex falla, intentamos un respaldo por letras directas
    if len(opciones) < 2:
        parts = re.split(r'(?=[A-E][\).])', text)
        enunciado = parts[0].strip()
        opciones = [p.strip() for p in parts[1:] if p.strip()]
        
    return enunciado, opciones

# 4. Estado de la Sesión
if 'correctas' not in st.session_state: st.session_state.correctas = 0
if 'incorrectas' not in st.session_state: st.session_state.incorrectas = 0
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'verificado' not in st.session_state: st.session_state.verificado = False

def main():
    df = load_data()
    if df is None: return

    # Mapeo de columnas por contenido (flexible)
    col_pregunta = next((c for c in df.columns if 'Pregunta' in c), df.columns[0])
    col_correcta = next((c for c in df.columns if 'correcta' in c), None)
    col_retro = next((c for c in df.columns if 'Retro' in c), None)

    # --- SIDEBAR (Stickers y Stats) ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=120)
        st.title("📊 Tu Rendimiento")
        st.metric("✅ Aciertos", st.session_state.correctas)
        st.metric("❌ Fallos", st.session_state.incorrectas)
        
        st.divider()
        modo = st.radio("Modo:", ["Estudio Libre 📖", "Simulacro 70 Preguntas ⏱️"])
        if st.button("🗑 Reiniciar Todo"):
            st.session_state.clear()
            st.rerun()

    # --- LÓGICA DE PREGUNTA ---
    q_raw = df.iloc[st.session_state.idx]
    enunciado, opciones = split_question(q_raw[col_pregunta])

    # Mostrar Pregunta
    st.markdown(f'<div class="question-card"><div class="q-text">🩺 {enunciado}</div></div>', unsafe_allow_html=True)

    if not st.session_state.verificado:
        if opciones:
            seleccion = st.radio("Selecciona la respuesta correcta:", opciones, index=None)
            if st.button("Validar Respuesta 🛡️"):
                if seleccion:
                    st.session_state.user_sel = seleccion
                    st.session_state.verificado = True
                    st.rerun()
                else:
                    st.warning("Doctor, debe seleccionar una opción.")
        else:
            st.error("Error al procesar las opciones. Revisa el formato en el Excel.")
    else:
        # Validación
        letra_sel = st.session_state.user_sel[0].upper()
        letra_cor = str(q_raw[col_correcta]).strip().upper()

        if letra_sel == letra_cor:
            st.success(f"### 🌟 ¡EXCELENTE! La respuesta correcta es {letra_cor}")
            if not hasattr(st.session_state, 'puntos_contados'):
                st.session_state.correctas += 1
                st.session_state.puntos_contados = True
        else:
            st.error(f"### ❌ INCORRECTO. La respuesta era {letra_cor}")
            if not hasattr(st.session_state, 'puntos_contados'):
                st.session_state.incorrectas += 1
                st.session_state.puntos_contados = True

        # Retroalimentación Gigante
        if col_retro and pd.notna(q_raw[col_retro]):
            st.markdown(f'<div class="retro-box"><b>📝 Explicación Médica:</b><br>{q_raw[col_retro]}</div>', unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta 🚀"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.verificado = False
            if hasattr(st.session_state, 'puntos_contados'): del st.session_state.puntos_contados
            st.rerun()

if __name__ == "__main__":
    main()
