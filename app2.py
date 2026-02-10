import streamlit as st
import pandas as pd
import random
import plotly.express as px
import os
import re

# --- CONFIGURACIÓN DE ESCENA ---
st.set_page_config(page_title="UdeA Resident Mastery v3.0", page_icon="💊", layout="wide")

# CSS para estilo "Misión Médica"
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .question-box { background-color: #1e2130; padding: 25px; border-radius: 15px; border-left: 8px solid #00d4ff; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .stRadio > label { font-size: 1.1rem !important; color: #00d4ff !important; font-weight: bold; }
    .retro-box { padding: 20px; border-radius: 10px; margin-top: 15px; border: 1px solid #444; }
    .stat-card { background-color: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

URL_EXCEL = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_excel(URL_EXCEL)
        df.columns = [str(c).strip() for c in df.columns]
        df['id_p'] = range(len(df))
        return df
    except Exception as e:
        st.error(f"Error de conexión con el Excel: {e}")
        return None

# --- PARSER DE PREGUNTAS (Separa texto de opciones A, B, C, D) ---
def parse_question(text):
    text = str(text)
    # Divide por saltos de línea que empiecen con A), B), A., B. o espacios seguidos de la letra
    parts = re.split(r'\s*\n?\s*(?=[A-E][\).])', text)
    enunciado = parts[0]
    opciones = [p.strip() for p in parts[1:] if p.strip()]
    return enunciado, opciones

# --- ESTADO DE LA SESIÓN ---
if 'history' not in st.session_state: st.session_state.history = {} 
if 'current_idx' not in st.session_state: st.session_state.current_idx = None
if 'answered' not in st.session_state: st.session_state.answered = False
if 'last_result' not in st.session_state: st.session_state.last_result = None

def main():
    df = load_data()
    if df is None: return

    # --- SIDEBAR: ESTADÍSTICAS ---
    with st.sidebar:
        st.title("👨‍⚕️ Dr. Master")
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=100)
        st.divider()
        
        modo = st.radio("Modo de Juego:", ["Repetición Espaciada", "Random Total"])
        
        # Mini Dashboard
        total = len(df)
        vistas = len(st.session_state.history)
        st.markdown(f"""
        <div class="stat-card">
            <small>Progreso Total</small><h3>{vistas}/{total}</h3>
            <small>XP Ganada</small><h4 style="color:#00d4ff;">{vistas * 100}</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🗑 Resetear Datos"):
            st.session_state.history = {}
            st.session_state.current_idx = None
            st.rerun()

    # --- LÓGICA DE SELECCIÓN ---
    if st.session_state.current_idx is None:
        if modo == "Repetición Espaciada" and st.session_state.history:
            # Prioriza las que tienen score 0 (falladas)
            falladas = [id for id, data in st.session_state.history.items() if data['score'] == 0]
            if falladas and random.random() < 0.6: # 60% probabilidad de repetir fallada
                st.session_state.current_idx = random.choice(falladas)
            else:
                st.session_state.current_idx = random.randint(0, len(df)-1)
        else:
            st.session_state.current_idx = random.randint(0, len(df)-1)

    q_data = df.iloc[st.session_state.current_idx]
    enunciado, opciones = parse_question(q_data['Pregunta'])

    # --- INTERFAZ PRINCIPAL ---
    st.markdown(f'<div class="question-box"><h4>{enunciado}</h4></div>', unsafe_allow_html=True)

    # Formulario de Respuesta
    with st.container():
        if not st.session_state.answered:
            if opciones:
                seleccion = st.radio("Selecciona la opción correcta:", opciones, index=None, key=f"q_{st.session_state.current_idx}")
                if st.button("Confirmar Diagnóstico 🛡️"):
                    if seleccion:
                        letra_sel = seleccion[0].upper()
                        correcta = str(q_data['Respuesta']).strip().upper()
                        
                        st.session_state.answered = True
                        if letra_sel == correcta:
                            st.session_state.last_result = ("success", "✅ ¡EXCELENTE DOCTOR! Respuesta correcta.")
                            st.session_state.history[st.session_state.current_idx] = {'score': 1}
                        else:
                            st.session_state.last_result = ("error", f"❌ ERROR CLÍNICO. La respuesta era {correcta}")
                            st.session_state.history[st.session_state.current_idx] = {'score': 0}
                        st.rerun()
            else:
                st.warning("Formato de opciones no detectado en esta celda.")
        
        else:
            # Mostrar Resultado y Retroalimentación
            tipo, msg = st.session_state.last_result
            if tipo == "success": st.success(msg)
            else: st.error(msg)

            st.markdown(f"""<div class="retro-box">
                <strong>Análisis de la Pregunta:</strong><br>{q_data['Retroalimentación']}
            </div>""", unsafe_allow_html=True)

            if st.button("Siguiente Paciente (Pregunta) ➡️"):
                st.session_state.current_idx = None
                st.session_state.answered = False
                st.session_state.last_result = None
                st.rerun()

    # Gráfico inferior
    if st.session_state.history:
        st.divider()
        fallos = sum(1 for x in st.session_state.history.values() if x['score'] == 0)
        aciertos = sum(1 for x in st.session_state.history.values() if x['score'] == 1)
        fig = px.pie(values=[aciertos, fallos], names=['Aciertos', 'Fallos'], 
                     color_discrete_sequence=['#2ecc71', '#e74c3c'], hole=0.4, title="Rendimiento de la Sesión")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
