import streamlit as st
import pandas as pd
import random
import plotly.express as px
import os

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(
    page_title="UdeA Med-Trainer",
    page_icon="💊",
    layout="wide"
)

# Estilo personalizado (CSS) - Médico-Gamer Edition
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #2e7bcf; color: white; font-weight: bold; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #1e5faf; transform: scale(1.02); border: 1px solid #00d4ff; }
    .question-box { background-color: #1e2130; padding: 30px; border-radius: 15px; border-left: 8px solid #00d4ff; margin-bottom: 25px; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); }
    .retro-box { background-color: #162e24; padding: 20px; border-radius: 10px; border: 1px solid #2ecc71; margin-top: 20px; }
    .stat-card { background-color: #262730; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

# --- CARGA DE DATOS ---
URL_EXCEL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_excel(URL_EXCEL)
        # Limpieza de nombres de columnas (quita espacios invisibles)
        df.columns = [str(c).strip() for c in df.columns]
        
        # Generar ID basado en la pregunta para el sistema de repetición
        if 'Pregunta' in df.columns:
            df['id_p'] = df['Pregunta'].apply(lambda x: hash(str(x)))
        else:
            st.error("No se encontró la columna 'Pregunta' en el Excel.")
            return None
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar el Excel: {e}")
        return None

# --- INICIALIZACIÓN DEL ESTADO (SISTEMA DE GUARDADO) ---
if 'history' not in st.session_state:
    st.session_state.history = {} # {id_p: {'score': 0, 'count': 0}}
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = None
if 'view' not in st.session_state:
    st.session_state.view = "pregunta"

# --- LÓGICA DE REPETICIÓN ESPACIADA ---
def get_next_question(df, mode):
    if df.empty: return None
    
    if mode == "Repetición Espaciada (SR)":
        # Priorizar preguntas que fallaste o no conoces (score < 2)
        vistas = list(st.session_state.history.keys())
        pendientes = [id for id in vistas if st.session_state.history[id]['score'] < 2]
        
        # 40% de probabilidad de que salga una difícil, si no, una al azar
        if pendientes and random.random() < 0.4:
            chosen_id = random.choice(pendientes)
            match = df[df['id_p'] == chosen_id]
            if not match.empty:
                return match.index[0]
                
    return random.randint(0, len(df) - 1)

# --- UI PRINCIPAL ---
def main():
    df = load_data()
    if df is None: return

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=80)
        st.title("UdeA Mastery")
        
        user = os.environ.get('USER', os.environ.get('USERNAME', 'Onii-chan'))
        st.write(f"🩺 **Dr. {user}**")
        st.divider()
        
        modo = st.radio("🎮 MODO DE ENTRENAMIENTO", ["Libre (Random)", "Repetición Espaciada (SR)"])
        
        st.divider()
        if st.button("🔄 Resetear Progreso"):
            st.session_state.history = {}
            st.session_state.current_idx = None
            st.rerun()

    # Selección inicial
    if st.session_state.current_idx is None:
        st.session_state.current_idx = get_next_question(df, modo)

    # --- DASHBOARD DE MÉTRICAS ---
    col_a, col_b, col_c = st.columns(3)
    total_vistas = len(st.session_state.history)
    exitos = sum(1 for x in st.session_state.history.values() if x['score'] >= 3)
    
    with col_a:
        st.metric("Preguntas Vistas", f"{total_vistas}")
    with col_b:
        st.metric("Dominadas (Score 3+)", f"{exitos}")
    with col_c:
        st.metric("XP Médica", total_vistas * 15)

    st.divider()

    # --- ÁREA DE LA PREGUNTA ---
    q = df.loc[st.session_state.current_idx]
    
    with st.container():
        st.markdown(f"""<div class="question-box"><h3>{q['Pregunta']}</h3></div>""", unsafe_allow_html=True)
        
        if st.session_state.view == "pregunta":
            if st.button("REVELAR RESPUESTA 🔓"):
                st.session_state.view = "retro"
                st.rerun()
        else:
            # Mostramos Respuesta y Retroalimentación
            st.markdown(f"""<div class="retro-box">
                <h4 style='color: #2ecc71;'>✅ Respuesta: {q['Respuesta']}</h4>
                <hr>
                <p style='font-size: 1.1em;'>{q['Retroalimentación']}</p>
            </div>""", unsafe_allow_html=True)
            
            st.divider()
            st.write("### ¿Qué tan difícil fue?")
            c1, c2, c3, c4 = st.columns(4)
            
            id_p = q['id_p']
            if id_p not in st.session_state.history:
                st.session_state.history[id_p] = {'score': 0, 'count': 0}

            def handle_click(score):
                st.session_state.history[id_p]['score'] = score
                st.session_state.history[id_p]['count'] += 1
                st.session_state.current_idx = get_next_question(df, modo)
                st.session_state.view = "pregunta"
                st.rerun()

            if c1.button("🟢 FÁCIL"): handle_click(4)
            if c2.button("🟡 BIEN"): handle_click(2)
            if c3.button("🟠 DIFÍCIL"): handle_click(1)
            if c4.button("🔴 NPI"): handle_click(0)

    # --- GRÁFICO DE PROGRESO ---
    if st.session_state.history:
        st.divider()
        hist_df = pd.DataFrame([
            {'Pregunta': i, 'Score': data['score']} 
            for i, data in st.session_state.history.items()
        ])
        fig = px.histogram(hist_df, x="Score", nbins=5, title="Distribución de Conocimiento",
                           color_discrete_sequence=['#00d4ff'])
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
