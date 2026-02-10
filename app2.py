import streamlit as st
import pandas as pd
import random
import time
import plotly.express as px

# --- CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(
    page_title="UdeA Residency Mastery",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado (CSS)
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2e7bcf; color: white; border: none; }
    .stButton>button:hover { background-color: #1e5faf; border: 1px solid #ffffff; }
    .question-box { background-color: #1e2130; padding: 25px; border-radius: 15px; border-left: 5px solid #00d4ff; margin-bottom: 20px; }
    .stat-card { background-color: #262730; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE DATOS ---
URL_EXCEL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data(ttl=300)
def load_data():
    try:
        df = pd.read_excel(URL_EXCEL)
        df.columns = [c.strip() for c in df.columns]
        # Crear ID único basado en el contenido para persistencia de sesión
        df['id_p'] = df['Pregunta'].apply(hash)
        return df
    except Exception as e:
        st.error(f"⚠️ Error al conectar con la base de datos médica: {e}")
        return None

# --- INICIALIZACIÓN DE ESTADO (EL SAVE GAME) ---
if 'history' not in st.session_state:
    st.session_state.history = {} # {id_p: {'score': 0, 'hits': 0, 'total': 0}}
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = None
if 'view' not in st.session_state:
    st.session_state.view = "pregunta"

# --- FUNCIONES CORE ---
def get_next_question(df_pool, mode):
    if df_pool.empty: return None
    
    if mode == "Repetición Espaciada (SR)":
        # Priorizar preguntas con menos 'hits' o menor score en el historial
        ids_vistos = list(st.session_state.history.keys())
        # Simplificación: 40% probabilidad de ir a una fallada antes que una nueva
        if ids_vistos and random.random() < 0.4:
            fail_pool = [id for id in ids_vistos if st.session_state.history[id]['score'] < 2]
            if fail_pool:
                chosen_id = random.choice(fail_pool)
                return df_pool[df_pool['id_p'] == chosen_id].index[0]
        
    return random.choice(df_pool.index)

# --- UI PRINCIPAL ---
def main():
    df = load_data()
    if df is None: return

    # --- SIDEBAR (PANEL DE CONTROL) ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=100)
        st.title("Med-Trainer v2.0")
        st.write(f"🩺 **Dr. {os.getlogin() if hasattr(os, 'getlogin') else 'Onii-chan'}**")
        st.divider()
        
        modo = st.selectbox("🎯 MODO DE JUEGO", ["Libre (Random)", "Repetición Espaciada (SR)", "Simulacro UdeA"])
        especialidades = st.multiselect("📚 FILTRAR ÁREA", options=df['Especialidad'].unique())
        
        st.divider()
        if st.button("🗑️ Resetear Progreso"):
            st.session_state.history = {}
            st.rerun()

    # --- FILTRADO ---
    df_filtered = df.copy()
    if especialidades:
        df_filtered = df_filtered[df_filtered['Especialidad'].isin(especialidades)]

    # Seleccionar primera pregunta
    if st.session_state.current_idx is None:
        st.session_state.current_idx = get_next_question(df_filtered, modo)

    # --- DASHBOARD DE PROGRESO (SUPERIOR) ---
    col_a, col_b, col_c = st.columns(3)
    total_vistas = len(st.session_state.history)
    exitos = sum(1 for x in st.session_state.history.values() if x['score'] > 0)
    
    with col_a:
        st.metric("Preguntas Dominadas", f"{exitos}/{len(df)}")
    with col_b:
        accuracy = (exitos/total_vistas*100) if total_vistas > 0 else 0
        st.metric("Precisión (Accuracy)", f"{accuracy:.1f}%")
    with col_c:
        st.metric("Nivel (XP)", total_vistas * 10)

    st.divider()

    # --- ÁREA DE ESTUDIO ---
    if st.session_state.current_idx is not None:
        q = df.loc[st.session_state.current_idx]
        
        st.markdown(f"### 📍 {q['Especialidad']} > {q['Tema']}")
        
        with st.container():
            st.markdown(f"""<div class="question-box"><h4>{q['Pregunta']}</h4></div>""", unsafe_allow_html=True)
            
            if st.session_state.view == "pregunta":
                if st.button("REVELAR RESPUESTA (SPACE)"):
                    st.session_state.view = "retro"
                    st.rerun()
            
            else:
                st.success(f"✅ **RESPUESTA CORRECTA:** {q['Respuesta correcta']}")
                with st.expander("📖 VER ANÁLISIS CLÍNICO (RETROALIMENTACIÓN)", expanded=True):
                    st.write(q['Retroalimentación'])
                
                st.divider()
                st.write("¿Cómo estuvo tu desempeño?")
                c1, c2, c3, c4 = st.columns(4)
                
                id_p = q['id_p']
                if id_p not in st.session_state.history:
                    st.session_state.history[id_p] = {'score': 0, 'count': 0}
                
                def update_and_next(score):
                    st.session_state.history[id_p]['score'] = score
                    st.session_state.history[id_p]['count'] += 1
                    st.session_state.current_idx = get_next_question(df_filtered, modo)
                    st.session_state.view = "pregunta"
                    st.rerun()

                if c1.button("🟢 FÁCIL (Master)"): update_and_next(3)
                if c2.button("🟡 BIEN (Repasar)"): update_and_next(2)
                if c3.button("🟠 DIFÍCIL (Urgente)"): update_and_next(1)
                if c4.button("🔴 NPI (Muerte)"): update_and_next(0)

    # --- GRÁFICO DE RENDIMIENTO (INFERIOR) ---
    if st.session_state.history:
        st.divider()
        st.subheader("📊 Análisis de Especialidades")
        stats_data = []
        for id_p, data in st.session_state.history.items():
            row = df[df['id_p'] == id_p].iloc[0]
            stats_data.append({'Especialidad': row['Especialidad'], 'Score': data['score']})
        
        df_stats = pd.DataFrame(stats_data)
        fig = px.bar(df_stats.groupby('Especialidad').mean().reset_index(), 
                     x='Especialidad', y='Score', color='Score', 
                     range_y=[0,3], title="Dominio por Área")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
