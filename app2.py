import streamlit as st
import pandas as pd
import random
import plotly.express as px
import os

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(
    page_title="UdeA Residency Mastery",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado (CSS) para ese feeling Médico-Gamer
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #2e7bcf; color: white; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #1e5faf; border: 1px solid #00d4ff; }
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
        df.columns = [c.strip() for c in df.columns]
        # Generar un ID basado en la pregunta para persistencia
        df['id_p'] = df['Pregunta'].apply(lambda x: hash(str(x)))
        return df
    except Exception as e:
        st.error(f"❌ Error al conectar con el servidor de datos: {e}")
        return None

# --- INICIALIZACIÓN DEL ESTADO ---
if 'history' not in st.session_state:
    st.session_state.history = {} # {id_p: {'score': 0, 'tries': 0}}
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = None
if 'view' not in st.session_state:
    st.session_state.view = "pregunta"

# --- LÓGICA DE SELECCIÓN (SPACED REPETITION) ---
def get_next_question(df_pool, mode):
    if df_pool.empty: return None
    
    if mode == "Repetición Espaciada (SR)":
        # Priorizar preguntas con score bajo (0 o 1)
        vistas = list(st.session_state.history.keys())
        pendientes = [id for id in vistas if st.session_state.history[id]['score'] < 2]
        
        # 50% de probabilidad de repetir una fallada si existen
        if pendientes and random.random() < 0.5:
            chosen_id = random.choice(pendientes)
            match = df_pool[df_pool['id_p'] == chosen_id]
            if not match.empty:
                return match.index[0]
                
    return random.choice(df_pool.index)

# --- UI PRINCIPAL ---
def main():
    df = load_data()
    if df is None: return

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=80)
        st.title("Med-Trainer v2.1")
        
        # Fix del error os.getlogin()
        user = os.environ.get('USER', os.environ.get('USERNAME', 'Onii-chan'))
        st.write(f"🩺 **Dr. {user}**")
        st.divider()
        
        modo = st.selectbox("🎮 MODO DE ESTUDIO", ["Repetición Espaciada (SR)", "Libre (Random)"])
        especialidades = st.multiselect("📚 ESPECIALIDAD", options=sorted(df['Especialidad'].unique()))
        
        st.divider()
        if st.button("🔄 Resetear Todo el Progreso"):
            st.session_state.history = {}
            st.session_state.current_idx = None
            st.rerun()

    # Filtrado dinámico
    df_filtered = df.copy()
    if especialidades:
        df_filtered = df_filtered[df_filtered['Especialidad'].isin(especialidades)]

    if df_filtered.empty:
        st.warning("No hay preguntas que coincidan con los filtros. Selecciona otra especialidad.")
        return

    # Selección inicial
    if st.session_state.current_idx is None or st.session_state.current_idx not in df_filtered.index:
        st.session_state.current_idx = get_next_question(df_filtered, modo)

    # --- DASHBOARD DE MÉTRICAS ---
    col_a, col_b, col_c = st.columns(3)
    total_vistas = len(st.session_state.history)
    dominadas = sum(1 for x in st.session_state.history.values() if x['score'] >= 3)
    
    with col_a:
        st.metric("Dominadas (Master)", f"{dominadas}/{len(df)}")
    with col_b:
        acc = (dominadas/total_vistas*100) if total_vistas > 0 else 0
        st.metric("Precisión Clínica", f"{acc:.1f}%")
    with col_c:
        st.metric("Nivel de XP", total_vistas * 25)

    st.divider()

    # --- INTERFAZ DE PREGUNTA ---
    q = df.loc[st.session_state.current_idx]
    
    st.markdown(f"#### 📍 {q['Especialidad']} | Tema: {q['Tema']}")
    
    st.markdown(f"""<div class="question-box"><h3>{q['Pregunta']}</h3></div>""", unsafe_allow_html=True)

    if st.session_state.view == "pregunta":
        if st.button("REVELAR RESPUESTA Y ANÁLISIS 🔓"):
            st.session_state.view = "retro"
            st.rerun()
    else:
        # Mostrar Retroalimentación
        st.markdown(f"""<div class="retro-box">
            <h4 style='color: #2ecc71;'>✅ Respuesta Correcta: {q['Respuesta correcta']}</h4>
            <hr>
            <p style='font-size: 1.1em;'>{q['Retroalimentación']}</p>
        </div>""", unsafe_allow_html=True)
        
        st.divider()
        st.write("### ¿Cómo estuvo tu desempeño en esta pregunta?")
        c1, c2, c3, c4 = st.columns(4)
        
        id_p = q['id_p']
        if id_p not in st.session_state.history:
            st.session_state.history[id_p] = {'score': 0, 'count': 0}

        def next_step(score):
            st.session_state.history[id_p]['score'] = score
            st.session_state.history[id_p]['count'] += 1
            st.session_state.current_idx = get_next_question(df_filtered, modo)
            st.session_state.view = "pregunta"
            st.rerun()

        if c1.button("🟢 FÁCIL (Dominado)"): next_step(4)
        if c2.button("🟡 BIEN (Repasar)"): next_step(2)
        if c3.button("🟠 DIFÍCIL (Mañana)"): next_step(1)
        if c4.button("🔴 NPI (Muerte)"): next_step(0)

    # --- ANALÍTICAS ---
    if st.session_state.history:
        st.divider()
        st.subheader("📊 Dominio por Especialidad")
        stats = []
        for id_p, data in st.session_state.history.items():
            row = df[df['id_p'] == id_p]
            if not row.empty:
                stats.append({'Especialidad': row.iloc[0]['Especialidad'], 'Score': data['score']})
        
        if stats:
            df_stats = pd.DataFrame(stats).groupby('Especialidad')['Score'].mean().reset_index()
            fig = px.bar(df_stats, x='Especialidad', y='Score', color='Score', 
                         color_continuous_scale='Viridis', range_y=[0,4])
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
