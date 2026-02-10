import streamlit as st
import pandas as pd
import random
import re

# --- 1. CONFIGURACIÓN Y ESTÉTICA ---
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
    .stButton>button { 
        height: 3.5em; 
        font-size: 22px !important; 
        font-weight: bold; 
        border-radius: 15px; 
        width: 100%; 
        background-color: #2e7bcf !important; 
        color: white !important; 
    }
    [data-testid="stMetricValue"] { 
        color: #2e7bcf !important; 
        font-size: 45px !important; 
        font-weight: bold; 
    }
    p, span, label { color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MOTOR DE DATOS ---
# CORREGIDO: URL sin espacios al final
URL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(URL)
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return None

def process_cell(text):
    text = str(text)
    # 1. Extraer Respuesta
    ans_match = re.search(r'(?:Respuesta|Correcta|R/):\s*([A-E])', text, re.IGNORECASE)
    respuesta = ans_match.group(1).upper() if ans_match else "A"
    
    # 2. Limpiar texto de la respuesta
    clean_text = re.sub(r'(?:Respuesta|Correcta|R/):\s*[A-E]', '', text, flags=re.IGNORECASE).strip()
    
    # 3. Separar enunciado y opciones
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
    
    # Asegurar que siempre haya opciones
    if len(opciones) < 2:
        # Fallback: buscar opciones con otro patrón
        opciones_match = re.findall(r'([A-E][\).]\s*[^\n]+)', clean_text)
        if opciones_match:
            opciones = opciones_match
    
    return enunciado, opciones, respuesta, retro.strip()

# --- 3. INICIALIZACIÓN DE ESTADO ---
def init_session():
    defaults = {
        'correctas': 0,
        'intentos': 0,
        'idx': 0,
        'answered': False,
        'exam_list': [],
        'ex_idx': 0,
        'ex_score': 0,  # CORREGIDO: Inicializar ex_score
        'user_choice': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

def main():
    df = load_data()
    if df is None or df.empty:
        st.error("❌ No se pudieron cargar las preguntas. Verifica la URL de GitHub.")
        return

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=140)
        st.header("📊 Score Card")
        st.metric("✅ Correctas", st.session_state.correctas)
        
        eff = (st.session_state.correctas / st.session_state.intentos * 100) if st.session_state.intentos > 0 else 0
        st.metric("📈 Eficiencia", f"{eff:.1f}%")
        
        st.divider()
        modo = st.radio("Selecciona tu Modo:", ["📖 Práctica Libre", "⏱️ Examen 70 Preguntas"])
        
        if st.button("🔄 Reiniciar Todo"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # --- MODO EXAMEN 70 ---
    if "70" in modo:
        if not st.session_state.exam_list:
            st.info("🎯 Modo Examen: 70 preguntas aleatorias")
            if st.button("🚀 INICIAR SIMULACRO"):
                n_preguntas = min(70, len(df))
                st.session_state.exam_list = df.sample(n=n_preguntas).to_dict('records')
                st.session_state.ex_idx = 0
                st.session_state.ex_score = 0
                st.rerun()
            return

        actual = st.session_state.ex_idx
        
        if actual < len(st.session_state.exam_list):
            # Procesar pregunta actual
            q_raw = st.session_state.exam_list[actual][df.columns[0]]
            enunciado, opciones, correcta, retro = process_cell(q_raw)
            
            # Verificar que hay opciones válidas
            if not opciones:
                st.error(f"Error procesando pregunta {actual + 1}. Saltando...")
                st.session_state.ex_idx += 1
                st.rerun()
            
            st.write(f"**Pregunta {actual + 1} de {len(st.session_state.exam_list)}**")
            st.progress((actual) / len(st.session_state.exam_list))
            
            st.markdown(f'<div class="main-card"><div class="q-text">{enunciado}</div></div>', 
                       unsafe_allow_html=True)
            
            # CORREGIDO: Manejo seguro del radio button
            opciones_limpias = [opt for opt in opciones if opt.strip()]
            sel = st.radio("Selecciona tu respuesta:", opciones_limpias, key=f"ex_{actual}", index=None)
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Validar ➡️", key=f"btn_ex_{actual}"):
                    if sel:
                        es_correcta = sel[0].upper() == correcta
                        if es_correcta:
                            st.session_state.ex_score += 1
                            st.success("✅ ¡Correcto!")
                        else:
                            st.error(f"❌ Incorrecto. Era: {correcta}")
                        
                        # Mostrar retroalimentación breve
                        if retro:
                            st.info(f"💡 {retro[:200]}...")
                        
                        st.session_state.ex_idx += 1
                        st.rerun()
        else:
            # Fin del examen
            st.balloons()
            total = len(st.session_state.exam_list)
            score = st.session_state.ex_score
            porcentaje = (score / total * 100) if total > 0 else 0
            
            st.success(f"### 🏆 Simulacro Terminado!")
            st.metric("Puntuación Final", f"{score} / {total}")
            st.metric("Porcentaje", f"{porcentaje:.1f}%")
            
            if porcentaje >= 80:
                st.success("🎉 ¡Excelente desempeño!")
            elif porcentaje >= 60:
                st.warning("📚 Buen trabajo, pero hay margen de mejora")
            else:
                st.error("💪 Sigue practicando")
            
            if st.button("Volver al Menú"): 
                st.session_state.exam_list = []
                st.session_state.ex_idx = 0
                st.session_state.ex_score = 0
                st.rerun()
        return

    # --- MODO PRÁCTICA LIBRE ---
    # CORREGIDO: Validar índice
    if st.session_state.idx >= len(df):
        st.session_state.idx = 0
    
    q_data = df.iloc[st.session_state.idx][df.columns[0]]
    enunciado, opciones, correcta, retro = process_cell(q_data)
    
    if not opciones:
        st.error("Error en formato de pregunta. Cargando siguiente...")
        st.session_state.idx = random.randint(0, len(df)-1)
        st.rerun()
    
    st.markdown(f'<div class="main-card"><div class="q-text">🩺 {enunciado}</div></div>', 
               unsafe_allow_html=True)

    if not st.session_state.answered:
        opciones_limpias = [opt for opt in opciones if opt.strip()]
        user_sel = st.radio("Opciones:", opciones_limpias, index=None, key=f"prac_{st.session_state.idx}")
        
        if st.button("Validar Respuesta 🛡️"):
            if user_sel:
                st.session_state.user_choice = user_sel
                st.session_state.answered = True
                st.session_state.intentos += 1
                if user_sel[0].upper() == correcta:
                    st.session_state.correctas += 1
                st.rerun()
    else:
        es_correcta = st.session_state.user_choice[0].upper() == correcta
        
        if es_correcta:
            st.success(f"### ✅ ¡CORRECTO! La respuesta es la {correcta}")
        else:
            st.error(f"### ❌ INCORRECTO. La respuesta correcta era la {correcta}")
            st.info(f"Tu selección: {st.session_state.user_choice}")

        if retro and len(retro) > 5:
            st.markdown(f'<div class="retro-box"><b>📖 Retroalimentación Clínica:</b><br>{retro}</div>', 
                       unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta 🚀"):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.answered = False
            st.session_state.user_choice = None
            st.rerun()

if __name__ == "__main__":
    main()
