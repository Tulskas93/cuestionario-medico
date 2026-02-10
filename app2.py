import streamlit as st
import pandas as pd
import random
import re

# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN VISUAL (ESTÉTICA KIMI + UDEA)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="UdeA Simulator Pro", layout="wide", page_icon="🏥")

st.markdown("""
<style>
    /* Fondo General */
    .stApp { background-color: #f0f4f8; }

    /* Tarjeta de Pregunta (El recuadro blanco) */
    .question-card {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 15px solid #2e7bcf; /* Azul UdeA */
        margin-bottom: 30px;
    }

    /* Texto de la Pregunta (GIGANTE) */
    .q-text {
        font-size: 32px !important;
        font-weight: 800;
        color: #102a43;
        line-height: 1.4;
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Opciones (Radio Buttons) - Estilo Botón */
    .stRadio > label {
        background-color: #ffffff;
        border: 2px solid #e1e4e8;
        border-radius: 12px;
        padding: 20px;
        font-size: 24px !important; /* Letra grande opciones */
        color: #333 !important;
        margin-bottom: 15px;
        display: block;
        transition: all 0.2s;
    }
    .stRadio > label:hover {
        border-color: #2e7bcf;
        background-color: #f8fbff;
    }

    /* Caja de Retroalimentación (Feedback) */
    .retro-box {
        background-color: #dcfce7; /* Verde suave */
        border: 2px solid #22c55e;
        color: #14532d;
        padding: 25px;
        border-radius: 15px;
        font-size: 22px !important;
        margin-top: 20px;
    }
    
    .retro-box-error {
        background-color: #fee2e2; /* Rojo suave */
        border: 2px solid #ef4444;
        color: #7f1d1d;
        padding: 25px;
        border-radius: 15px;
        font-size: 22px !important;
        margin-top: 20px;
    }

    /* Botones de Acción (Siguiente/Validar) */
    .stButton > button {
        width: 100%;
        background-color: #2e7bcf;
        color: white;
        font-size: 24px !important;
        font-weight: bold;
        padding: 15px;
        border-radius: 12px;
        border: none;
    }
    .stButton > button:hover { background-color: #1c5b9e; color: white; }

    /* Métricas del Sidebar */
    [data-testid="stMetricValue"] { font-size: 36px !important; color: #2e7bcf; }
    
    /* Ocultar elementos molestos */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. PROCESAMIENTO INTELIGENTE DE DATOS (EL CIRUJANO)
# -----------------------------------------------------------------------------
URL_DATA = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data
def get_data():
    try:
        df = pd.read_excel(URL_DATA)
        return df
    except:
        return None

def parse_full_cell(text):
    """
    Toma una celda sucia y devuelve: (Pregunta, [Opciones], RespuestaCorrecta, Explicación)
    """
    text = str(text).strip()
    
    # 1. Buscar la respuesta correcta (Patrones: "Respuesta: A", "R/ A", "Clave: A")
    # Busca al final o en medio del texto
    match_resp = re.search(r'(?:Respuesta|R\/|Clave|Correcta)[:\s\.-]*([A-E])', text, re.IGNORECASE)
    correcta = match_resp.group(1).upper() if match_resp else "A" # Default A si no encuentra
    
    # 2. Limpiar la etiqueta de respuesta para que no salga en el texto visible
    text_clean = re.sub(r'(?:Respuesta|R\/|Clave|Correcta)[:\s\.-]*[A-E].*', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # 3. Separar Pregunta de Opciones usando Regex
    # Busca A), A., B), B. etc.
    # El patrón (?=...) es un "lookahead" para cortar justo antes de la letra
    chunks = re.split(r'\s+(?=[A-E][\)\.])', text_clean)
    
    pregunta = chunks[0].strip()
    raw_opciones = chunks[1:] if len(chunks) > 1 else []
    
    # 4. Limpiar opciones y detectar si hay retroalimentación pegada a la última opción
    opciones_limpias = []
    retro = "Analiza bien el caso clínico." # Texto por defecto
    
    for i, opt in enumerate(raw_opciones):
        # Si es la última opción, a veces trae la retroalimentación pegada
        if i == len(raw_opciones) - 1:
            # Aquí podríamos intentar separar texto extra si no es parte de la opción
            # Por ahora asumimos que todo es opción salvo que tengamos el match de respuesta original
            pass
        opciones_limpias.append(opt.strip())

    # Intentar recuperar la retroalimentación del texto original (lo que estaba después de "Respuesta: X")
    match_retro = re.search(r'(?:Respuesta|R\/|Clave|Correcta)[:\s\.-]*[A-E](.*)', text, re.IGNORECASE | re.DOTALL)
    if match_retro:
        retro_found = match_retro.group(1).strip()
        if len(retro_found) > 5:
            retro = retro_found

    # Si el regex falló en separar opciones (caso raro), devuelve lista vacía para manejar error visual
    return pregunta, opciones_limpias, correcta, retro

# -----------------------------------------------------------------------------
# 3. GESTIÓN DE ESTADO (MEMORIA)
# -----------------------------------------------------------------------------
if 'mode' not in st.session_state: st.session_state.mode = 'setup'
if 'score_ok' not in st.session_state: st.session_state.score_ok = 0
if 'score_bad' not in st.session_state: st.session_state.score_bad = 0
if 'history' not in st.session_state: st.session_state.history = []

# Variables para modo examen
if 'exam_questions' not in st.session_state: st.session_state.exam_questions = []
if 'exam_index' not in st.session_state: st.session_state.exam_index = 0
if 'exam_answers' not in st.session_state: st.session_state.exam_answers = []

# Variable para modo práctica
if 'practice_q' not in st.session_state: st.session_state.practice_q = None
if 'practice_answered' not in st.session_state: st.session_state.practice_answered = False

# -----------------------------------------------------------------------------
# 4. INTERFAZ PRINCIPAL
# -----------------------------------------------------------------------------
def main():
    df = get_data()
    if df is None:
        st.error("❌ Error Crítico: No se pudo cargar el Excel. Revisa el enlace.")
        return

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=120)
        st.title("Med-UdeA Pro")
        
        st.markdown("### 📊 Rendimiento Global")
        c1, c2 = st.columns(2)
        c1.metric("✅", st.session_state.score_ok)
        c2.metric("❌", st.session_state.score_bad)
        
        st.divider()
        st.markdown("### ⚙️ Configuración")
        mode_select = st.radio("Modo de Estudio:", 
                               ["🏠 Inicio", "📖 Práctica Infinita", "📝 Simulacro UdeA (70)"])
        
        if st.button("🗑️ Reiniciar Todo"):
            st.session_state.clear()
            st.rerun()

    # --- LÓGICA DE NAVEGACIÓN ---
    
    # 1. PANTALLA DE INICIO
    if mode_select == "🏠 Inicio":
        st.markdown(f"""
        <div style="text-align:center; padding: 50px;">
            <h1>¡Bienvenido, Doctor! 👨‍⚕️</h1>
            <p style="font-size: 24px;">Base de datos cargada: <b>{len(df)} preguntas</b>.</p>
            <p style="font-size: 20px;">Selecciona un modo en el menú izquierdo para comenzar.</p>
        </div>
        """, unsafe_allow_html=True)

    # 2. MODO PRÁCTICA (FEEDBACK INMEDIATO)
    elif mode_select == "📖 Práctica Infinita":
        st.header("📖 Estudio Continuo")
        
        # Cargar nueva pregunta si no hay una activa
        if st.session_state.practice_q is None:
            random_row = df.sample(1).iloc[0]
            raw_text = str(random_row[0]) # Asumimos columna 0
            q, ops, ans, retro = parse_full_cell(raw_text)
            st.session_state.practice_q = {'q': q, 'ops': ops, 'ans': ans, 'retro': retro}
            st.session_state.practice_answered = False
        
        current = st.session_state.practice_q
        
        # MOSTRAR TARJETA
        st.markdown(f'<div class="question-card"><div class="q-text">{current["q"]}</div></div>', unsafe_allow_html=True)
        
        if not st.session_state.practice_answered:
            # Formulario para evitar recargas raras
            with st.form("practice_form"):
                if current['ops']:
                    user_sel = st.radio("Seleccione su diagnóstico:", current['ops'])
                else:
                    st.warning("⚠️ No se detectaron opciones claras (A, B, C...). Revisa el formato.")
                    user_sel = None
                
                submitted = st.form_submit_button("Confirmar Respuesta 🛡️")
                
                if submitted and user_sel:
                    st.session_state.user_selection = user_sel
                    st.session_state.practice_answered = True
                    # Validar
                    letra_user = user_sel.strip()[0].upper() # Toma la primera letra "A" de "A) Opcion..."
                    if letra_user == current['ans']:
                        st.session_state.score_ok += 1
                        st.session_state.is_correct = True
                    else:
                        st.session_state.score_bad += 1
                        st.session_state.is_correct = False
                    st.rerun()
        
        else:
            # PANTALLA DE RESULTADO
            if st.session_state.is_correct:
                st.success(f"### ✅ ¡CORRECTO! La respuesta es {current['ans']}")
                st.markdown(f'<div class="retro-box"><b>📝 Retroalimentación:</b><br>{current["retro"]}</div>', unsafe_allow_html=True)
            else:
                st.error(f"### ❌ ERROR. La correcta era {current['ans']}")
                st.markdown(f'<div class="retro-box-error"><b>📝 Corrección:</b><br>{current["retro"]}</div>', unsafe_allow_html=True)
            
            if st.button("Siguiente Pregunta ➡️"):
                st.session_state.practice_q = None # Reset para cargar nueva
                st.rerun()

    # 3. MODO SIMULACRO (70 PREGUNTAS SIN FEEDBACK HASTA EL FINAL)
    elif mode_select == "📝 Simulacro UdeA (70)":
        st.header("📝 Examen de Admisión Simulado")
        
        # Inicializar examen
        if not st.session_state.exam_questions:
            if st.button("🚀 INICIAR SIMULACRO (70 Preguntas)"):
                sample_size = min(70, len(df))
                # Guardamos solo los índices o el texto crudo para ahorrar memoria
                raw_samples = df.sample(sample_size)[df.columns[0]].tolist()
                st.session_state.exam_questions = raw_samples
                st.session_state.exam_index = 0
                st.session_state.exam_answers = [] # Lista de bool (True/False)
                st.rerun()
        else:
            # Estamos en examen
            idx = st.session_state.exam_index
            total = len(st.session_state.exam_questions)
            
            if idx < total:
                # Procesar pregunta actual
                raw_text = st.session_state.exam_questions[idx]
                q, ops, ans, retro = parse_full_cell(raw_text)
                
                # Barra de progreso
                st.progress((idx + 1) / total)
                st.caption(f"Pregunta {idx + 1} de {total}")
                
                # Tarjeta
                st.markdown(f'<div class="question-card"><div class="q-text">{q}</div></div>', unsafe_allow_html=True)
                
                # Selección
                # Usamos key dinámica para resetear el radio button
                sel = st.radio("Opciones:", ops, key=f"exam_q_{idx}", index=None)
                
                c_prev, c_next = st.columns([1, 1])
                
                if st.button("Siguiente ➡️"):
                    if sel:
                        letra = sel.strip()[0].upper()
                        es_correcta = (letra == ans)
                        st.session_state.exam_answers.append(es_correcta)
                        st.session_state.exam_index += 1
                        st.rerun()
                    else:
                        st.warning("⚠️ Debes marcar una opción para avanzar.")
            else:
                # FIN DEL EXAMEN
                score = sum(st.session_state.exam_answers)
                final_grade = (score / total) * 100
                
                st.balloons()
                st.markdown(f"""
                <div style="background-color: white; padding: 40px; border-radius: 20px; text-align: center; border: 2px solid #2e7bcf;">
                    <h1>🏁 Examen Finalizado</h1>
                    <h2 style="font-size: 60px; color: #2e7bcf;">{score} / {total}</h2>
                    <h3>Porcentaje: {final_grade:.1f}%</h3>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Salir del Simulacro"):
                    st.session_state.exam_questions = []
                    st.rerun()

if __name__ == "__main__":
    main()
