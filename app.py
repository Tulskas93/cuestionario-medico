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

# CSS personalizado para que se vea lindo en celular
st.markdown("""
<style>
    .main {
        padding: 1rem;
    }
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
</style>
""", unsafe_allow_html=True)

# Inicializar variables en session_state
if 'preguntas' not in st.session_state:
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.correctas = 0
    st.session_state.respondido = False
    st.session_state.modo_examen = False
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
            
            # Buscar donde empieza la opción A)
            match_a = re.search(r'A\)', texto_completo)
            
            if not match_a:
                continue
                
            # Separar encabezado de opciones
            inicio_opciones = match_a.start()
            encabezado = texto_completo[:inicio_opciones].strip()
            opciones_texto = texto_completo[inicio_opciones:]
            
            # Extraer cada opción
            opciones = {}
            letras = ['A', 'B', 'C', 'D']
            
            for i, letra in enumerate(letras):
                if i < 3:
                    patron = rf'{letra}\)\s*(.+?)(?=\n{letras[i+1]}\)|$)'
                else:
                    patron = rf'{letra}\)\s*(.+)'
                    
                match = re.search(patron, opciones_texto, re.DOTALL)
                if match:
                    opciones[letra] = match.group(1).strip().replace('\n', ' ')
                else:
                    # Intento alternativo
                    patron_alt = rf'{letra}\)\s*([^\n]+)'
                    match_alt = re.search(patron_alt, opciones_texto)
                    if match_alt:
                        opciones[letra] = match_alt.group(1).strip()
            
            if len(opciones) == 4:
                preguntas.append({
                    'caso': encabezado,
                    'opciones': opciones,
                    'respuesta': respuesta_correcta,
                    'explicacion': retroalimentacion,
                    'tema': tema
                })
        except:
            continue
    
    return preguntas

# TÍTULO PRINCIPAL
st.title("🏥 Cuestionario Médico")
st.markdown("---")

# SIDEBAR - Configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Cargar automáticamente el Excel al inicio
    if not st.session_state.cargado:
        try:
            # LEE EL EXCEL AUTOMÁTICAMENTE - Cambia el nombre aquí
            import urllib.request

url = "https://raw.githubusercontent.com/Tulskas93/cuestionario-medico/main/tus_preguntas.xlsx"
urllib.request.urlretrieve(url, "temp.xlsx")
df = pd.read_excel("temp.xlsx")
            
            df.columns = df.columns.str.strip()
            st.session_state.preguntas = procesar_preguntas(df)
            
            if st.session_state.preguntas:
                random.shuffle(st.session_state.preguntas)
                st.session_state.cargado = True
                st.success(f"✅ {len(st.session_state.preguntas)} preguntas cargadas")
            else:
                st.error("❌ No se pudieron procesar las preguntas")
        except FileNotFoundError:
            st.error("❌ No se encontró 'tus_preguntas.xlsx'\n\nVerifica que esté en la misma carpeta")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    if st.session_state.cargado:
        st.info(f"📚 {len(st.session_state.preguntas)} preguntas listas")
    
    # Modo de estudio
    st.session_state.modo_examen = st.checkbox("🎯 Modo Examen", value=st.session_state.modo_examen)
    
    # Reiniciar
    if st.button("🔄 Reiniciar"):
        st.session_state.indice = 0
        st.session_state.correctas = 0
        st.session_state.respondido = False
        if st.session_state.preguntas:
            random.shuffle(st.session_state.preguntas)
        st.rerun()

# CONTENIDO PRINCIPAL
if not st.session_state.cargado:
    st.warning("👆 Esperando archivo Excel...")
    
    st.markdown("""
    ### 📋 Instrucciones:
    1. Guarda tu Excel como: **tus_preguntas.xlsx**
    2. Ponlo en la **misma carpeta** que app.py
    3. **Recarga** la página (F5)
    
    ### Formato esperado:
    - **Pregunta** (caso + opciones A-D)
    - **Respuesta correcta** (A, B, C, D)
    - **Retroalimentación** (explicación)
    - **Tema** (opcional)
    """)
    
else:
    # Barra de progreso
    total = len(st.session_state.preguntas)
    actual = st.session_state.indice + 1
    progreso = st.session_state.indice / total
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progreso)
    with col2:
        st.markdown(f"**{actual}/{total}**")
    
    # Mostrar pregunta actual
    if st.session_state.indice < total:
        preg = st.session_state.preguntas[st.session_state.indice]
        
        # Tema
        st.markdown(f"**📚 Tema:** *{preg['tema']}*")
        
        # Caso clínico
        with st.expander("📋 Ver Caso Clínico", expanded=True):
            st.markdown(preg['caso'])
        
        st.markdown("---")
        
        # Opciones
        st.subheader("Selecciona tu respuesta:")
        
        opciones_mostradas = {f"{letra}) {texto}": letra 
                             for letra, texto in preg['opciones'].items()}
        
        respuesta_usuario = st.radio(
            "Elige una opción:",
            options=list(opciones_mostradas.keys()),
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
                    seleccion = opciones_mostradas[respuesta_usuario]
                    
                    if seleccion == preg['respuesta']:
                        st.session_state.correctas += 1
                        st.session_state.ultima_correcta = True
                    else:
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
            if not st.session_state.modo_examen:
                with st.expander("📖 Ver Explicación", expanded=True):
                    st.markdown(preg['explicacion'])
            
            # Botón siguiente
            if st.button("➡️ Siguiente Pregunta", type="primary"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.rerun()
    
    else:
        # RESULTADOS FINALES
        st.balloons()
        st.success("🎉 ¡Cuestionario completado!")
        
        porcentaje = (st.session_state.correctas / total) * 100
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Correctas", f"{st.session_state.correctas}/{total}")
        with col2:
            st.metric("Porcentaje", f"{porcentaje:.1f}%")
        with col3:
            if porcentaje >= 80:
                emoji, mensaje = "🌟", "¡Excelente!"
            elif porcentaje >= 60:
                emoji, mensaje = "👍", "¡Bien hecho!"
            else:
                emoji, mensaje = "💪", "Sigue practicando"
            st.markdown(f"### {emoji}\n**{mensaje}**")
        
        if st.button("🔄 Volver a empezar"):
            st.session_state.indice = 0
            st.session_state.correctas = 0
            st.session_state.respondido = False
            random.shuffle(st.session_state.preguntas)
            st.rerun()

st.markdown("---")
st.markdown("*Hecho con ❤️ para estudiantes de medicina*")

