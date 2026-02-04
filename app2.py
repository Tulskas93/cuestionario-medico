import streamlit as st
import pandas as pd
import random
import re
import time
import json
import os
from datetime import datetime, timedelta

# Configuración de la página - DEBE SER LO PRIMERO
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
    st.session_state.tiempo_pregunta = 30
    st.session_state.modo_oscuro = False
    st.session_state.voz_activada = False
    st.session_state.tiempo_restante = 30

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
    return str(timedelta(seconds=int(max(0, segundos))))[2:7]

def leer_texto(texto):
    """Función para lector de voz"""
    if st.session_state.voz_activada:
        js_code = f"""
        <script>
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance();
            msg.text = "{texto.replace('"', "'").replace(chr(10), ' ')}";
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

# CSS personalizado con modo oscuro CORREGIDO
if st.session_state.modo_oscuro:
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-size: 16px;
        background-color: #262730;
        color: #fafafa;
        border: 1px solid #4a4a4a;
    }
    .stRadio > label {
        color: #fafafa !important;
    }
    .stMarkdown {
        color: #fafafa !important;
    }
    .stExpander {
        background-color: #262730;
        border: 1px solid #4a4a4a;
    }
    .correct {
        background-color: #1e4620;
        color: #fafafa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4caf50;
    }
    .incorrect {
        background-color: #4a1c1c;
        color: #fafafa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #f44336;
    }
    .stats-box {
        background-color: #262730;
        color: #fafafa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #4a4a4a;
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
    h1, h2, h3, h4, h5, h6, p, label {
        color: #fafafa !important;
    }
    .stSidebar {
        background-color: #1e2129;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        color: #31333f;
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
    """, unsafe_allow_html=True)

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
                progreso = cargar_progreso()
                if progreso:
                    st.info(f"📂 Progreso anterior: {progreso['correctas']}✓ {progreso['incorrectas']}✗")
                
                st.session_state.temas_disponibles = get_temas_disponibles(st.session_state.preguntas)
                st.session_state.cargado = True
                st.success(f"✅ {len(st.session_state.preguntas)} preguntas cargadas")
            else:
                st.error("❌ No se pudieron procesar las preguntas")
                
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.stop()

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configuración")
    
    if st.session_state.cargado:
        # Modo oscuro
        modo_oscuro_nuevo = st.toggle("🌙 Modo Oscuro", value=st.session_state.modo_oscuro)
        if modo_oscuro_nuevo != st.session_state.modo_oscuro:
            st.session_state.modo_oscuro = modo_oscuro_nuevo
            st.rerun()
        
        # Lector de voz
        st.session_state.voz_activada = st.toggle("🔊 Lector de Voz", value=st.session_state.voz_activada)
        
        # Selección de tema
        tema_nuevo = st.selectbox("📚 Tema", options=st.session_state.temas_disponibles, 
                                  index=st.session_state.temas_disponibles.index(st.session_state.tema_seleccionado))
        if tema_nuevo != st.session_state.tema_seleccionado:
            st.session_state.tema_seleccionado = tema_nuevo
            st.session_state.indice = 0
            st.session_state.respondido = False
            st.rerun()
        
        # Modo repaso
        st.session_state.modo_repaso = st.toggle("🎯 Modo Repaso (falladas)", value=st.session_state.modo_repaso)
        
        # Tiempo por pregunta
        st.session_state.tiempo_pregunta = st.slider("⏱️ Tiempo (segundos)", 10, 120, 30)
        
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
            <p>📝 <b>En repaso:</b> {len(st.session_state.preguntas_falladas)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 Guardar Progreso"):
            guardar_progreso()
            st.success("✅ Guardado")
        
        if st.button("🔄 Reiniciar Todo"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# Preparar preguntas
if st.session_state.cargado:
    preguntas_filtradas = filtrar_por_tema(st.session_state.preguntas, st.session_state.tema_seleccionado)
    
    if st.session_state.modo_repaso and st.session_state.preguntas_falladas:
        ids_falladas = [p['id'] for p in st.session_state.preguntas_falladas]
        preguntas_a_mostrar = [p for p in preguntas_filtradas if p['id'] in ids_falladas]
        if not preguntas_a_mostrar:
            st.warning("⚠️ No hay falladas en este tema")
            preguntas_a_mostrar = preguntas_filtradas
    else:
        preguntas_a_mostrar = preguntas_filtradas
    
    if st.session_state.indice == 0 and not st.session_state.respondido:
        random.shuffle(preguntas_a_mostrar)
    
    total = len(preguntas_a_mostrar)
    
    if total > 0 and st.session_state.indice < total:
        preg = preguntas_a_mostrar[st.session_state.indice]
        
        # Iniciar tiempo
        if st.session_state.tiempo_inicio is None:
            st.session_state.tiempo_inicio = time.time()
        
        # Contenedor para el tiempo (se actualizará)
        tiempo_container = st.empty()
        
        # Calcular y mostrar tiempo
        tiempo_transcurrido = time.time() - st.session_state.tiempo_inicio
        tiempo_restante = max(0, st.session_state.tiempo_pregunta - tiempo_transcurrido)
        
        # Actualizar visual del tiempo
        timer_class = "timer-box warning" if tiempo_restante < 10 else "timer-box"
        tiempo_container.markdown(f'<div class="{timer_class}">⏱️ {formatear_tiempo(tiempo_restante)}</div>', 
                                   unsafe_allow_html=True)
        
        # Verificar tiempo agotado
        if tiempo_restante <= 0 and not st.session_state.respondido:
            st.error("⏰ ¡Tiempo agotado!")
            st.session_state.respondido = True
            st.session_state.incorrectas += 1
            st.session_state.ultima_correcta = False
            if preg not in st.session_state.preguntas_falladas:
                st.session_state.preguntas_falladas.append(preg)
            st.rerun()
        
        # Auto-refresh para tiempo real (cada segundo)
        if not st.session_state.respondido and tiempo_restante > 0:
            time.sleep(0.5)
            st.rerun()
        
        # Barra de progreso
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(st.session_state.indice / total)
        with col2:
            st.markdown(f"**{st.session_state.indice + 1}/{total}**")
        
        # Tema
        st.markdown(f"**📚 Tema:** *{preg['tema']}*")
        
        # Caso clínico
        with st.expander("📋 Ver Caso Clínico", expanded=True):
            st.markdown(preg['caso'])
            if st.session_state.voz_activada and st.button("🔊 Escuchar caso", key=f"voz_caso_{st.session_state.indice}"):
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
                        st.session_state.preguntas_falladas = [
                            p for p in st.session_state.preguntas_falladas if p['id'] != preg['id']
                        ]
                    else:
                        st.session_state.incorrectas += 1
                        st.session_state.ultima_correcta = False
                        if preg not in st.session_state.preguntas_falladas:
                            st.session_state.preguntas_falladas.append(preg)
                    
                    st.rerun()
        
        else:
            # Resultado
            if st.session_state.ultima_correcta:
                st.markdown('<div class="correct"><h3>✅ ¡CORRECTO!</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="incorrect"><h3>❌ Incorrecto</h3><p>Respuesta: <b>{preg["respuesta"]}</b></p></div>', 
                           unsafe_allow_html=True)
            
            # Explicación
            with st.expander("📖 Ver Explicación", expanded=True):
                st.markdown(preg['explicacion'])
                if st.session_state.voz_activada and st.button("🔊 Escuchar explicación", key=f"voz_exp_{st.session_state.indice}"):
                    leer_texto(preg['explicacion'])
            
            # Siguiente
            if st.button("➡️ Siguiente", type="primary"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.tiempo_inicio = None
                st.rerun()
    
    else:
        # RESULTADOS FINALES
        st.balloons()
        st.success("🎉 ¡Completado!")
        
        total_resp = st.session_state.correctas + st.session_state.incorrectas
        porcentaje = (st.session_state.correctas / total_resp * 100) if total_resp > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ Correctas", st.session_state.correctas)
        col2.metric("❌ Incorrectas", st.session_state.incorrectas)
        col3.metric("📊 Precisión", f"{porcentaje:.1f}%")
        col4.metric("📝 En repaso", len(st.session_state.preguntas_falladas))
        
        if porcentaje >= 80:
            emoji, mensaje = "🌟", "¡Excelente!"
        elif porcentaje >= 60:
            emoji, mensaje = "👍", "¡Buen trabajo!"
        else:
            emoji, mensaje = "💪", "Sigue practicando"
        
        st.markdown(f"### {emoji} {mensaje}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Reiniciar"):
                st.session_state.indice = 0
                st.session_state.correctas = 0
                st.session_state.incorrectas = 0
                st.session_state.respondido = False
                st.session_state.tiempo_inicio = None
                st.rerun()
        with col2:
            if st.button("🎯 Modo Repaso"):
                st.session_state.indice = 0
                st.session_state.correctas = 0
                st.session_state.incorrectas = 0
                st.session_state.respondido = False
                st.session_state.modo_repaso = True
                st.session_state.tiempo_inicio = None
                st.rerun()
        with col3:
            if st.button("💾 Guardar"):
                guardar_progreso()
                st.success("✅ Guardado")

st.markdown("---")
st.markdown("*🏥 Cuestionario Médico Pro*")
