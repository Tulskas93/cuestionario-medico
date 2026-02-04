import streamlit as st
import pandas as pd
import random
import re
import time
import json
import os
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Cuestionario Médico Pro",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Inicializar variables en session_state
if 'preguntas' not in st.session_state:
    st.session_state.preguntas = []
    st.session_state.indice = 0
    st.session_state.correctas = 0
    st.session_state.incorrectas = 0
    st.session_state.respondido = False
    st.session_state.cargado = False
    st.session_state.tema_seleccionado = "Todos"
    st.session_state.modo_repaso = False
    st.session_state.preguntas_falladas = []
    st.session_state.tiempo_inicio = None
    st.session_state.tiempo_pregunta = 30  # segundos por pregunta
    st.session_state.modo_oscuro = False
    st.session_state.voz_activada = False

# Archivo para guardar progreso
PROGRESO_FILE = "progreso.json"

def cargar_progreso():
    """Carga el progreso guardado"""
    if os.path.exists(PROGRESO_FILE):
        try:
            with open(PROGRESO_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_progreso():
    """Guarda el progreso actual"""
    progreso = {
        'fecha': datetime.now().isoformat(),
        'correctas': st.session_state.correctas,
        'incorrectas': st.session_state.incorrectas,
        'total_preguntas': len(st.session_state.preguntas),
        'preguntas_falladas_ids': [p['caso'][:50] for p in st.session_state.preguntas_falladas],
        'tema': st.session_state.tema_seleccionado
    }
    with open(PROGRESO_FILE, 'w') as f:
        json.dump(progreso, f)

def formatear_tiempo(segundos):
    """Convierte segundos a formato MM:SS"""
    return str(timedelta(seconds=int(segundos)))[2:7]

def leer_texto(texto):
    """Función para lector de voz (usando HTML5)"""
    if st.session_state.voz_activada:
        # Usar JavaScript para síntesis de voz
        js_code = f"""
        <script>
        if ('speechSynthesis' in window) {{
            var msg = new SpeechSynthesisUtterance();
            msg.text = "{texto.replace('"', "'")}";
            msg.lang = 'es-ES';
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        }}
        </script>
        """
        st.components.v1.html(js_code, height=0)

def procesar_preguntas(df):
    """Procesa el DataFrame separando caso, pregunta y opciones"""
    preguntas = []
    
    for idx, row in df.iterrows():
        try:
            texto_completo = str(row['Pregunta'])
            respuesta_correcta = str(row['Respuesta correcta']).strip().upper()
            retroalimentacion = str(row['Retroalimentación'])
            tema = str(row.get('Tema', 'Sin tema'))
            
            # Encontrar el inicio de cada opción
            pos_a = texto_completo.find('A)')
            pos_b = texto_completo.find('B)')
            pos_c = texto_completo.find('C)')
            pos_d = texto_completo.find('D)')
            
            if pos_a == -1 or pos_b == -1 or pos_c == -1 or pos_d == -1:
                continue
            
            encabezado = texto_completo[:pos_a].strip()
            
            opciones = {
                'A': texto_completo[pos_a+2:pos_b].strip().replace('\n', ' '),
                'B': texto_completo[pos_b+2:pos_c].strip().replace('\n', ' '),
                'C': texto_completo[pos_c+2:pos_d].strip().replace('\n', ' '),
                'D': texto_completo[pos_d+2:].strip().replace('\n', ' ')
            }
            
            if all(opciones.values()):
                preguntas.append({
                    'id': f"{tema}_{idx}",
                    'caso': encabezado,
                    'opciones': opciones,
                    'respuesta': respuesta_correcta,
                    'explicacion': retroalimentacion,
                    'tema': tema
                })
        except:
            continue
    
    return preguntas

def get_temas_disponibles(preguntas):
    """Obtiene lista de temas únicos"""
    temas = list(set([p['tema'] for p in preguntas]))
    return ["Todos"] + sorted(temas)

def filtrar_por_tema(preguntas, tema):
    """Filtra preguntas por tema seleccionado"""
    if tema == "Todos":
        return preguntas
    return [p for p in preguntas if p['tema'] == tema]

# CSS personalizado con modo oscuro
def get_css():
    if st.session_state.modo_oscuro:
        return """
        <style>
        .main { 
            background-color: #1a1a1a;
            color: #ffffff;
            padding: 1rem;
        }
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            font-size: 16px;
            background-color: #2c3e50;
            color: white;
        }
        .correct {
            background-color: #1e4620;
            color: white;
            padding: 1rem;
            border-radius: 10px;
            border-left: 5px solid #4caf50;
        }
        .incorrect {
            background-color: #4a1c1c;
            color: white;
            padding: 1rem;
            border-radius: 10px;
            border-left: 5px solid #f44336;
        }
        .stats-box {
            background-color: #2c3e50;
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .timer-box {
            background-color: #e74c3c;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        .timer-box.warning {
            background-color: #f39c12;
        }
        h1, h2, h3, h4, p { color: #ffffff !important; }
        </style>
        """
    else:
        return """
        <style>
        .main { 
            background-color: #f5f5f5;
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
        .stats-box {
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .timer-box {
            background-color: #3498db;
            color: white;
            padding: 0.5rem;
            border-radius: 5px;
            text-align: center;
            font-size: 1.2em;
            font-weight: bold;
        }
        .timer-box.warning {
            background-color: #e67e22;
        }
        </style>
        """

st.markdown(get_css(), unsafe_allow_html=True)

# TÍTULO PRINCIPAL
st.title("🏥 Cuestionario Médico Pro")
st.markdown("---")

# CARGAR DATOS
if not st.session_state.cargado:
    with st.spinner("Cargando preguntas..."):
        try:
            import subprocess
            import sys
            
            try:
                import gdown
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
                import gdown
            
            file_id = "1PXszau9XOTummO8t66XRCVxvGL3KhYN6"
            url = f"https://drive.google.com/uc?id={file_id}"
            gdown.download(url, "temp.xlsx", quiet=True)
            
            df = pd.read_excel("temp.xlsx")
            df.columns = df.columns.str.strip()
            st.session_state.preguntas = procesar_preguntas(df)
            
            if st.session_state.preguntas:
                # Cargar progreso anterior
                progreso = cargar_progreso()
                if progreso and 'preguntas_falladas_ids' in progreso:
                    st.info(f"📂 Progreso anterior encontrado: {progreso['correctas']} correctas, {progreso['incorrectas']} incorrectas")
                
                st.session_state.temas_disponibles = get_temas_disponibles(st.session_state.preguntas)
                st.session_state.cargado = True
                st.success(f"✅ {len(st.session_state.preguntas)} preguntas cargadas")
            else:
                st.error("❌ No se pudieron procesar las preguntas")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.stop()

# SIDEBAR - Configuración completa
with st.sidebar:
    st.header("⚙️ Configuración")
    
    if st.session_state.cargado:
        # Modo oscuro
        st.session_state.modo_oscuro = st.toggle("🌙 Modo Oscuro", value=st.session_state.modo_oscuro)
        
        # Lector de voz
        st.session_state.voz_activada = st.toggle("🔊 Lector de Voz", value=st.session_state.voz_activada)
        
        # Selección de tema
        st.session_state.tema_seleccionado = st.selectbox(
            "📚 Seleccionar Tema",
            options=st.session_state.temas_disponibles
        )
        
        # Modo repaso
        st.session_state.modo_repaso = st.toggle(
            "🎯 Modo Repaso (solo falladas)",
            value=st.session_state.modo_repaso,
            help="Practica solo las preguntas que has respondido incorrectamente"
        )
        
        # Tiempo por pregunta
        st.session_state.tiempo_pregunta = st.slider(
            "⏱️ Tiempo por pregunta (segundos)",
            min_value=10,
            max_value=120,
            value=30
        )
        
        st.markdown("---")
        
        # Estadísticas
        st.header("📊 Estadísticas")
        total_resp = st.session_state.correctas + st.session_state.incorrectas
        
        st.markdown(f"""
        <div class="stats-box">
            <p>✅ <b>Correctas:</b> {st.session_state.correctas}</p>
            <p>❌ <b>Incorrectas:</b> {st.session_state.incorrectas}</p>
            <p>📊 <b>Total:</b> {total_resp}</p>
            <p>🎯 <b>Precisión:</b> {(st.session_state.correctas/total_resp*100 if total_resp > 0 else 0):.1f}%</p>
            <p>📝 <b>Falladas guardadas:</b> {len(st.session_state.preguntas_falladas)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Guardar progreso
        if st.button("💾 Guardar Progreso"):
            guardar_progreso()
            st.success("✅ Progreso guardado")
        
        # Reiniciar
        if st.button("🔄 Reiniciar Todo"):
            st.session_state.indice = 0
            st.session_state.correctas = 0
            st.session_state.incorrectas = 0
            st.session_state.respondido = False
            st.session_state.preguntas_falladas = []
            st.session_state.tiempo_inicio = None
            random.shuffle(st.session_state.preguntas)
            st.rerun()

# Preparar preguntas según filtros
if st.session_state.cargado:
    # Filtrar por tema
    preguntas_filtradas = filtrar_por_tema(st.session_state.preguntas, st.session_state.tema_seleccionado)
    
    # Si está en modo repaso, usar solo falladas de este tema
    if st.session_state.modo_repaso and st.session_state.preguntas_falladas:
        ids_falladas = [p['id'] for p in st.session_state.preguntas_falladas]
        preguntas_a_mostrar = [p for p in preguntas_filtradas if p['id'] in ids_falladas]
        if not preguntas_a_mostrar:
            st.warning("⚠️ No hay preguntas falladas en este tema. Mostrando todas.")
            preguntas_a_mostrar = preguntas_filtradas
    else:
        preguntas_a_mostrar = preguntas_filtradas
    
    # Barajar si es primera vez
    if st.session_state.indice == 0 and not st.session_state.respondido:
        random.shuffle(preguntas_a_mostrar)
    
    total = len(preguntas_a_mostrar)
    
    if total > 0 and st.session_state.indice < total:
        preg = preguntas_a_mostrar[st.session_state.indice]
        
        # Iniciar tiempo si es primera vez
        if st.session_state.tiempo_inicio is None:
            st.session_state.tiempo_inicio = time.time()
        
        # Calcular tiempo restante
        tiempo_transcurrido = time.time() - st.session_state.tiempo_inicio
        tiempo_restante = max(0, st.session_state.tiempo_pregunta - tiempo_transcurrido)
        
        # Mostrar barra de progreso y tiempo
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.progress(st.session_state.indice / total)
        with col2:
            st.markdown(f"**{st.session_state.indice + 1}/{total}**")
        with col3:
            timer_class = "timer-box warning" if tiempo_restante < 10 else "timer-box"
            st.markdown(f'<div class="{timer_class}">⏱️ {formatear_tiempo(tiempo_restante)}</div>', unsafe_allow_html=True)
        
        # Tema
        st.markdown(f"**📚 Tema:** *{preg['tema']}*")
        
        # Caso clínico con lector de voz
        with st.expander("📋 Ver Caso Clínico", expanded=True):
            st.markdown(preg['caso'])
            if st.session_state.voz_activada:
                if st.button("🔊 Escuchar caso"):
                    leer_texto(preg['caso'])
        
        st.markdown("---")
        st.subheader("Selecciona tu respuesta:")
        
        # Opciones
        opciones_lista = [
            f"A) {preg['opciones']['A']}",
            f"B) {preg['opciones']['B']}",
            f"C) {preg['opciones']['C']}",
            f"D) {preg['opciones']['D']}"
        ]
        
        respuesta_usuario = st.radio(
            "Elige una opción:",
            options=opciones_lista,
            index=None,
            key=f"pregunta_{st.session_state.indice}"
        )
        
        # Verificar si se acabó el tiempo
        tiempo_agotado = tiempo_restante <= 0 and not st.session_state.respondido
        
        if tiempo_agotado:
            st.error("⏰ ¡Tiempo agotado!")
            st.session_state.respondido = True
            st.session_state.incorrectas += 1
            st.session_state.ultima_correcta = False
            # Guardar como fallada
            if preg not in st.session_state.preguntas_falladas:
                st.session_state.preguntas_falladas.append(preg)
            st.rerun()
        
        # Botón responder
        if not st.session_state.respondido:
            if st.button("✅ Responder", type="primary"):
                if respuesta_usuario is None:
                    st.warning("⚠️ Selecciona una opción")
                else:
                    st.session_state.respondido = True
                    seleccion = respuesta_usuario[0]
                    
                    if seleccion == preg['respuesta']:
                        st.session_state.correctas += 1
                        st.session_state.ultima_correcta = True
                        # Si acertó y estaba en falladas, quitarla
                        st.session_state.preguntas_falladas = [
                            p for p in st.session_state.preguntas_falladas if p['id'] != preg['id']
                        ]
                    else:
                        st.session_state.incorrectas += 1
                        st.session_state.ultima_correcta = False
                        # Guardar como fallada
                        if preg not in st.session_state.preguntas_falladas:
                            st.session_state.preguntas_falladas.append(preg)
                    
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
            
            # Explicación con lector de voz
            with st.expander("📖 Ver Explicación", expanded=True):
                st.markdown(preg['explicacion'])
                if st.session_state.voz_activada:
                    if st.button("🔊 Escuchar explicación"):
                        leer_texto(preg['explicacion'])
            
            # Botón siguiente
            if st.button("➡️ Siguiente Pregunta", type="primary"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.tiempo_inicio = None
                st.rerun()
    
    else:
        # RESULTADOS FINALES
        st.balloons()
        st.success("🎉 ¡Cuestionario completado!")
        
        total_resp = st.session_state.correctas + st.session_state.incorrectas
        porcentaje = (st.session_state.correctas / total_resp * 100) if total_resp > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Correctas", st.session_state.correctas)
        with col2:
            st.metric("❌ Incorrectas", st.session_state.incorrectas)
        with col3:
            st.metric("📊 Precisión", f"{porcentaje:.1f}%")
        with col4:
            st.metric("📝 Falladas", len(st.session_state.preguntas_falladas))
        
        # Mensaje según desempeño
        if porcentaje >= 80:
            emoji, mensaje = "🌟", "¡Excelente trabajo!"
        elif porcentaje >= 60:
            emoji, mensaje = "👍", "¡Buen trabajo!"
        else:
            emoji, mensaje = "💪", "Sigue practicando"
        
        st.markdown(f"### {emoji} {mensaje}")
        
        # Opciones al finalizar
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Volver a empezar"):
                st.session_state.indice = 0
                st.session_state.correctas = 0
                st.session_state.incorrectas = 0
                st.session_state.respondido = False
                st.session_state.tiempo_inicio = None
                random.shuffle(preguntas_a_mostrar)
                st.rerun()
        
        with col2:
            if st.button("🎯 Modo Repaso (Falladas)"):
                st.session_state.indice = 0
                st.session_state.correctas = 0
                st.session_state.incorrectas = 0
                st.session_state.respondido = False
                st.session_state.modo_repaso = True
                st.session_state.tiempo_inicio = None
                st.rerun()
        
        with col3:
            if st.button("💾 Guardar y Salir"):
                guardar_progreso()
                st.success("✅ Progreso guardado. ¡Hasta luego!")

st.markdown("---")
st.markdown("*🏥 Cuestionario Médico Pro - Hecho con ❤️*")
