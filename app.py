import streamlit as st
import pandas as pd
import random
import re

# Configuración de la página
st.set_page_config(
    page_title="Cuestionario Médico",
    page_icon="🏥",
    layout="centered"
)

# CSS personalizado
st.markdown("""
<style>
    .main { padding: 1rem; }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-size: 16px;
    }
    .correct {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .incorrect {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #dc3545;
    }
    .stats-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar session_state
if 'preguntas' not in st.session_state:
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.correctas = 0
    st.session_state.incorrectas = 0
    st.session_state.respondido = False
    st.session_state.cargado = False

def procesar_preguntas(df):
    """Procesa el DataFrame separando caso, pregunta y opciones"""
    preguntas = []
    
    for idx, row in df.iterrows():
        try:
            texto_completo = str(row['Pregunta'])
            respuesta_correcta = str(row['Respuesta correcta']).strip().upper()
            retroalimentacion = str(row['Retroalimentación'])
            tema = str(row.get('Tema', 'No especificado'))
            
            # Encontrar el inicio de cada opción
            pos_a = texto_completo.find('A)')
            pos_b = texto_completo.find('B)')
            pos_c = texto_completo.find('C)')
            pos_d = texto_completo.find('D)')
            
            # Verificar que existan todas las opciones
            if pos_a == -1 or pos_b == -1 or pos_c == -1 or pos_d == -1:
                continue
            
            # El caso está antes de A)
            encabezado = texto_completo[:pos_a].strip()
            
            # Extraer cada opción por posición
            opciones = {}
            opciones['A'] = texto_completo[pos_a+2:pos_b].strip().replace('\n', ' ')
            opciones['B'] = texto_completo[pos_b+2:pos_c].strip().replace('\n', ' ')
            opciones['C'] = texto_completo[pos_c+2:pos_d].strip().replace('\n', ' ')
            
            # La opción D va hasta el final
            texto_d = texto_completo[pos_d+2:].strip().replace('\n', ' ')
            opciones['D'] = texto_d
            
            # Verificar que no estén vacías
            if all(opciones.values()):
                preguntas.append({
                    'caso': encabezado,
                    'opciones': opciones,
                    'respuesta': respuesta_correcta,
                    'explicacion': retroalimentacion,
                    'tema': tema
                })
                
        except Exception as e:
            st.error(f"Error en fila {idx}: {str(e)}")
            continue
    
    return preguntas

# TÍTULO PRINCIPAL
st.title("🏥 Cuestionario Médico")
st.markdown("---")

# CARGAR DATOS desde Google Drive
if not st.session_state.cargado:
    try:
        # Instalar gdown si no está
        import subprocess
        import sys
        
        try:
            import gdown
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
            import gdown
        
        # ID del archivo de Google Drive
        file_id = "1PXszau9XOTummO8t66XRCVxvGL3KhYN6"
        
        # Descargar archivo
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, "temp.xlsx", quiet=False)
        
        # Leer el archivo
        df = pd.read_excel("temp.xlsx")
        st.success("✅ Datos cargados desde Google Drive")
        
    except Exception as e:
        st.error(f"❌ Error al cargar desde Drive: {str(e)}")
        st.info("Intentando cargar archivo local...")
        
        try:
            df = pd.read_excel("tus_preguntas.xlsx")
            st.success("✅ Datos cargados localmente")
        except:
            st.error("❌ No se encontró el archivo Excel")
            st.stop()
    
    # Procesar preguntas
    df.columns = df.columns.str.strip()
    st.session_state.preguntas = procesar_preguntas(df)
    
    if st.session_state.preguntas:
        random.shuffle(st.session_state.preguntas)
        st.session_state.cargado = True
        st.info(f"📚 {len(st.session_state.preguntas)} preguntas listas")
    else:
        st.error("❌ No se pudieron procesar las preguntas")
        st.info("Verifica que el Excel tenga las columnas: Pregunta, Respuesta correcta, Retroalimentación")

# SIDEBAR con estadísticas
with st.sidebar:
    st.header("📊 Estadísticas")
    
    if st.session_state.cargado:
        total = st.session_state.correctas + st.session_state.incorrectas
        
        st.markdown(f"""
        <div class="stats-box">
            <h4>Progreso</h4>
            <p>✅ <b>Correctas:</b> {st.session_state.correctas}</p>
            <p>❌ <b>Incorrectas:</b> {st.session_state.incorrectas}</p>
            <p>📊 <b>Total respondidas:</b> {total}</p>
            <hr>
            <p>🎯 <b>Precisión:</b> {((st.session_state.correctas/total)*100 if total > 0 else 0):.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.header("⚙️ Configuración")
    
    if st.button("🔄 Reiniciar Cuestionario"):
        st.session_state.indice = 0
        st.session_state.correctas = 0
        st.session_state.incorrectas = 0
        st.session_state.respondido = False
        if st.session_state.preguntas:
            random.shuffle(st.session_state.preguntas)
        st.rerun()

# CONTENIDO PRINCIPAL
if st.session_state.cargado and st.session_state.indice < len(st.session_state.preguntas):
    total = len(st.session_state.preguntas)
    actual = st.session_state.indice + 1
    progreso = st.session_state.indice / total
    
    # Barra de progreso
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progreso)
    with col2:
        st.markdown(f"**{actual}/{total}**")
    
    # Mostrar pregunta
    preg = st.session_state.preguntas[st.session_state.indice]
    
    st.markdown(f"**📚 Tema:** *{preg['tema']}*")
    
    with st.expander("📋 Ver Caso Clínico", expanded=True):
        st.markdown(preg['caso'])
    
    st.markdown("---")
    st.subheader("Selecciona tu respuesta:")
    
    # Mostrar opciones de forma simple
    opcion_a = f"A) {preg['opciones']['A']}"
    opcion_b = f"B) {preg['opciones']['B']}"
    opcion_c = f"C) {preg['opciones']['C']}"
    opcion_d = f"D) {preg['opciones']['D']}"
    
    respuesta_usuario = st.radio(
        "Elige una opción:",
        options=[opcion_a, opcion_b, opcion_c, opcion_d],
        index=None,
        key=f"pregunta_{st.session_state.indice}"
    )
    
    # Botón responder
    if not st.session_state.respondido:
        if st.button("✅ Responder", type="primary"):
            if respuesta_usuario is None:
                st.warning("⚠️ Selecciona una opción primero")
            else:
                st.session_state.respondido = True
                # Extraer la letra de la respuesta seleccionada
                seleccion = respuesta_usuario[0]  # Primera letra (A, B, C o D)
                
                if seleccion == preg['respuesta']:
                    st.session_state.correctas += 1
                    st.session_state.ultima_correcta = True
                else:
                    st.session_state.incorrectas += 1
                    st.session_state.ultima_correcta = False
                
                st.rerun()
    
    else:
        # Mostrar resultado
        if st.session_state.ultima_correcta:
            st.markdown("""
            <div class="correct">
                <h3>✅ ¡CORRECTO!</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="incorrect">
                <h3>❌ Incorrecto</h3>
                <p>Respuesta correcta: <b>{preg['respuesta']}</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Explicación
        with st.expander("📖 Ver Explicación", expanded=True):
            st.markdown(preg['explicacion'])
        
        # Botón siguiente
        if st.button("➡️ Siguiente Pregunta", type="primary"):
            st.session_state.indice += 1
            st.session_state.respondido = False
            st.rerun()

elif st.session_state.cargado:
    # RESULTADOS FINALES
    st.balloons()
    st.success("🎉 ¡Cuestionario completado!")
    
    total_preguntas = len(st.session_state.preguntas)
    total_respondidas = st.session_state.correctas + st.session_state.incorrectas
    porcentaje = (st.session_state.correctas / total_respondidas * 100) if total_respondidas > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Correctas", st.session_state.correctas)
    with col2:
        st.metric("❌ Incorrectas", st.session_state.incorrectas)
    with col3:
        st.metric("📊 Precisión", f"{porcentaje:.1f}%")
    
    # Mensaje según desempeño
    if porcentaje >= 80:
        emoji, mensaje = "🌟", "¡Excelente trabajo!"
    elif porcentaje >= 60:
        emoji, mensaje = "👍", "¡Buen trabajo, sigue así!"
    else:
        emoji, mensaje = "💪", "Sigue practicando, ¡tú puedes!"
    
    st.markdown(f"### {emoji} {mensaje}")
    
    if st.button("🔄 Volver a empezar"):
        st.session_state.indice = 0
        st.session_state.correctas = 0
        st.session_state.incorrectas = 0
        st.session_state.respondido = False
        random.shuffle(st.session_state.preguntas)
        st.rerun()

st.markdown("---")
st.markdown("*Hecho con ❤️ para estudiantes de medicina*")

