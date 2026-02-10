import streamlit as st
import pandas as pd
import random
import re
import requests
from io import BytesIO

# --- 1. CONFIGURACIÓN ---
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
        height: 3.5em; font-size: 22px !important; font-weight: bold; 
        border-radius: 15px; width: 100%; background-color: #2e7bcf !important; color: white !important; 
    }
    .debug-box { 
        background: #fff3cd; border: 2px solid #ffc107; padding: 10px; 
        border-radius: 5px; margin: 10px 0; font-family: monospace; font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CARGA DE DATOS ROBUSTA ---
URL_RAW = "https://github.com/Tulskas93/cuestionario-medico/raw/refs/heads/main/tus_preguntas.xlsx"

@st.cache_data(ttl=3600, show_spinner="📚 Cargando banco de preguntas...")
def load_data():
    try:
        # Método 1: Intentar con requests (más confiable en Streamlit Cloud)
        st.write("🔍 Intentando cargar desde GitHub...")
        response = requests.get(URL_RAW, timeout=30)
        response.raise_for_status()
        
        st.write(f"✅ Archivo descargado: {len(response.content)} bytes")
        
        # Leer Excel desde bytes
        df = pd.read_excel(BytesIO(response.content), engine='openpyxl')
        
        if df.empty:
            st.error("❌ El archivo Excel está vacío")
            return None
            
        st.write(f"📊 DataFrame cargado: {len(df)} filas, {len(df.columns)} columnas")
        st.write(f"📝 Columnas: {list(df.columns)}")
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de red: {e}")
        return None
    except Exception as e:
        st.error(f"❌ Error procesando Excel: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None

def process_cell(text):
    """Procesa una celda de pregunta con manejo de errores"""
    try:
        text = str(text)
        if not text or text == 'nan':
            return None, [], None, ""
            
        # Extraer respuesta
        ans_match = re.search(r'(?:Respuesta|Correcta|R/)[:\s]*([A-E])', text, re.IGNORECASE)
        respuesta = ans_match.group(1).upper() if ans_match else None
        
        # Limpiar texto
        clean_text = re.sub(r'(?:Respuesta|Correcta|R/)[:\s]*[A-E]', '', text, flags=re.IGNORECASE).strip()
        
        # Separar enunciado y opciones
        # Buscar patrón: A) o A. o A-
        parts = re.split(r'\s*(?=[A-E][\.\)\-])', clean_text)
        
        if len(parts) < 2:
            # Fallback: buscar con regex más flexible
            enunciado = clean_text[:200]  # Primeros 200 chars como enunciado
            opciones = re.findall(r'([A-E][\.\)\-]\s*[^\n]+)', clean_text)
        else:
            enunciado = parts[0].strip()
            opciones = []
            
            for p in parts[1:]:
                p = p.strip()
                if re.match(r'^[A-E][\.\)\-]', p):
                    # Limpiar la opción
                    opt_clean = re.sub(r'^\s*[A-E][\.\)\-]\s*', '', p).strip()
                    if opt_clean:
                        opciones.append(f"{p[0]}. {opt_clean}")
        
        return enunciado, opciones, respuesta, ""
        
    except Exception as e:
        st.error(f"Error procesando celda: {e}")
        return "Error en pregunta", [], "A", ""

# --- 3. INICIALIZACIÓN ESTADO ---
def init_session():
    defaults = {
        'correctas': 0,
        'intentos': 0,
        'idx': 0,
        'answered': False,
        'exam_list': [],
        'ex_idx': 0,
        'ex_score': 0,
        'user_choice': None,
        'df_loaded': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# --- 4. INTERFAZ PRINCIPAL ---
def main():
    st.title("🎓 UdeA Mastery Pro")
    st.markdown("**Plataforma de preparación para exámenes médicos**")
    
    # Cargar datos con feedback visual
    df = load_data()
    
    if df is None:
        st.error("""
        ⚠️ **No se pudo cargar el banco de preguntas**
        
        Posibles causas:
        1. El archivo Excel no existe en la URL
        2. Problemas de conectividad con GitHub
        3. El archivo está corrupto o protegido
        
        **URL intentada:** 
        ```
        {}
        ```
        """.format(URL_RAW))
        
        # Opción de carga manual
        st.divider()
        st.subheader("📁 Carga manual (fallback)")
        uploaded_file = st.file_uploader("Sube el archivo tus_preguntas.xlsx", type=['xlsx'])
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.success(f"✅ Archivo cargado manualmente: {len(df)} preguntas")
            except Exception as e:
                st.error(f"Error leyendo archivo: {e}")
                return
        else:
            return
    
    # Verificar estructura mínima
    if len(df.columns) == 0:
        st.error("❌ El Excel no tiene columnas")
        return
    
    col_pregunta = df.columns[0]
    st.session_state.df_loaded = True
    
    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/b/b5/Escudo_UdeA.svg", width=120)
        st.header("📊 Estadísticas")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Correctas", st.session_state.correctas)
        with col2:
            eff = (st.session_state.correctas/st.session_state.intentos*100) if st.session_state.intentos > 0 else 0
            st.metric("📈 Eficiencia", f"{eff:.0f}%")
        
        st.divider()
        modo = st.radio("Modo:", ["📖 Práctica Libre", "⏱️ Examen 70 Preguntas"])
        
        if st.button("🔄 Reiniciar Todo"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        # Debug info (colapsable)
        with st.expander("🔧 Info Técnica"):
            st.write(f"Total preguntas: {len(df)}")
            st.write(f"Índice actual: {st.session_state.idx}")
            st.write(f"Columna usada: {col_pregunta}")

    # --- MODO EXAMEN ---
    if "70" in modo:
        render_examen_mode(df, col_pregunta)
    else:
        render_practica_mode(df, col_pregunta)

def render_examen_mode(df, col_pregunta):
    """Renderiza el modo examen de 70 preguntas"""
    if not st.session_state.exam_list:
        st.info("🎯 **Modo Examen**: Simulacro de 70 preguntas aleatorias")
        
        n_disponible = min(70, len(df))
        st.write(f"Preguntas disponibles: {n_disponible}")
        
        if st.button("🚀 INICIAR SIMULACRO", use_container_width=True):
            if len(df) < 70:
                st.warning(f"⚠️ Solo hay {len(df)} preguntas disponibles. Usando todas.")
            
            st.session_state.exam_list = df.sample(n=n_disponible).to_dict('records')
            st.session_state.ex_idx = 0
            st.session_state.ex_score = 0
            st.rerun()
        return
    
    # Mostrar progreso
    actual = st.session_state.ex_idx
    total = len(st.session_state.exam_list)
    
    if actual >= total:
        # Resultados finales
        st.balloons()
        score = st.session_state.ex_score
        porcentaje = (score/total*100)
        
        st.success(f"### 🏆 Simulacro Completado!")
        st.metric("Puntuación", f"{score}/{total}", f"{porcentaje:.1f}%")
        
        if porcentaje >= 80:
            st.success("🌟 ¡Excelente! Dominas el tema")
        elif porcentaje >= 60:
            st.info("📚 Buen intento, sigue practicando")
        else:
            st.warning("💪 Necesitas más preparación")
            
        if st.button("Volver al Menú", use_container_width=True):
            st.session_state.exam_list = []
            st.rerun()
        return
    
    # Procesar pregunta actual
    q_raw = st.session_state.exam_list[actual][col_pregunta]
    resultado = process_cell(q_raw)
    
    if resultado[0] is None:
        st.error(f"⚠️ Pregunta {actual+1} con formato inválido. Saltando...")
        st.session_state.ex_idx += 1
        st.rerun()
    
    enunciado, opciones, correcta, retro = resultado
    
    # Validar datos
    if not opciones or correcta is None:
        st.warning(f"⚠️ Pregunta {actual+1} incompleta. Saltando...")
        st.session_state.ex_idx += 1
        st.rerun()
    
    # UI de pregunta
    progress = actual / total
    st.progress(progress, text=f"Pregunta {actual + 1} de {total}")
    
    st.markdown(f'<div class="main-card"><div class="q-text">{enunciado}</div></div>', 
               unsafe_allow_html=True)
    
    # Opciones
    opciones_dict = {}
    for opt in opciones:
        match = re.match(r'^([A-E])[\.\)\-]\s*(.+)', opt)
        if match:
            opciones_dict[match.group(1)] = match.group(2)
    
    if not opciones_dict:
        st.error("Error procesando opciones")
        return
    
    sel = st.radio("Selecciona:", 
                   [f"{k}) {v}" for k, v in opciones_dict.items()],
                   key=f"ex_{actual}",
                   index=None)
    
    if st.button("Validar y Continuar ➡️", use_container_width=True):
        if sel:
            respuesta_usuario = sel[0]
            es_correcta = respuesta_usuario == correcta
            
            if es_correcta:
                st.session_state.ex_score += 1
                st.success("✅ ¡Correcto!")
            else:
                st.error(f"❌ Incorrecto. Era: {correcta}")
            
            st.session_state.ex_idx += 1
            st.rerun()

def render_practica_mode(df, col_pregunta):
    """Renderiza el modo práctica libre"""
    # Validar índice
    if st.session_state.idx >= len(df):
        st.session_state.idx = 0
    
    q_raw = df.iloc[st.session_state.idx][col_pregunta]
    resultado = process_cell(q_raw)
    
    if resultado[0] is None:
        st.error("⚠️ Error en formato de pregunta. Cargando otra...")
        st.session_state.idx = random.randint(0, len(df)-1)
        st.rerun()
    
    enunciado, opciones, correcta, retro = resultado
    
    if not opciones:
        st.error("⚠️ No se encontraron opciones. Siguiente pregunta...")
        st.session_state.idx = random.randint(0, len(df)-1)
        st.rerun()
    
    st.markdown(f'<div class="main-card"><div class="q-text">🩺 {enunciado}</div></div>', 
               unsafe_allow_html=True)
    
    # Preparar opciones
    opciones_dict = {}
    for opt in opciones:
        match = re.match(r'^([A-E])[\.\)\-]\s*(.+)', opt)
        if match:
            opciones_dict[match.group(1)] = match.group(2)
    
    if not st.session_state.answered:
        sel = st.radio("Opciones:", 
                      [f"{k}) {v}" for k, v in opciones_dict.items()],
                      index=None,
                      key=f"prac_{st.session_state.idx}")
        
        if st.button("Validar Respuesta 🛡️", use_container_width=True):
            if sel:
                st.session_state.user_choice = sel[0]
                st.session_state.answered = True
                st.session_state.intentos += 1
                
                if sel[0] == correcta:
                    st.session_state.correctas += 1
                
                st.rerun()
    else:
        # Mostrar resultado
        es_correcta = st.session_state.user_choice == correcta
        
        if es_correcta:
            st.success(f"### ✅ ¡CORRECTO! Respuesta: {correcta}")
        else:
            st.error(f"### ❌ INCORRECTO. Era: {correcta}")
            st.info(f"Tu respuesta: {st.session_state.user_choice}")
        
        if retro:
            st.markdown(f'<div class="retro-box"><b>💡 Explicación:</b><br>{retro}</div>', 
                       unsafe_allow_html=True)
        
        if st.button("Siguiente Pregunta 🚀", use_container_width=True):
            st.session_state.idx = random.randint(0, len(df)-1)
            st.session_state.answered = False
            st.session_state.user_choice = None
            st.rerun()

if __name__ == "__main__":
    main()
