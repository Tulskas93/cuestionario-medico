import streamlit as st
import pandas as pd
import random
import re
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

# Inicializar session_state
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

PROGRESO_FILE = "progreso.json"

def cargar_progreso():
    if os.path.exists(PROGRESO_FILE):
        try:
            with open(PROGRESO_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def guardar_progreso():
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
    return f"{int(max(0, segundos))//60:02d}:{int(max(0, segundos))%60:02d}"

def leer_texto(texto):
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
            
            if -1 in [pos_a, pos_b, pos_c, pos_d]:
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

def get_temas(preguntas):
    temas = list(set([p['tema'] for p in preguntas]))
    return ["Todos"] + sorted(temas)

def filtrar_tema(preguntas, tema):
    if tema == "Todos":
        return preguntas
    return [p for p in preguntas if p['tema'] == tema]

# CSS según modo
if st.session_state.modo_oscuro:
    st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stButton>button { background-color: #262730; color: #fafafa; }
    .correct { background-color: #1e4620; color: #fafafa; padding: 1rem; border-radius: 10px; border-left: 5px solid #4caf50; }
    .incorrect { background-color: #4a1c1c; color: #fafafa; padding: 1rem; border-radius: 10px; border-left: 5px solid #f44336; }
    .stats-box { background-color: #262730; color: #fafafa; padding: 1rem; border-radius: 10px; }
    .timer-box { background-color: #3498db; color: white; padding: 0.5rem; border-radius: 5px; text-align: center; font-size: 1.2em; font-weight: bold; }
    .timer-warning { background-color: #e74c3c; }
    h1, h2, h3, p, label { color: #fafafa !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .correct { background-color: #d4edda; padding: 1rem; border-radius: 10px; border-left: 5px solid #28a745; }
    .incorrect { background-color: #f8d7da; padding: 1rem; border-radius: 10px; border-left: 5px solid #dc3545; }
    .stats-box { background-color: #e3f2fd; padding: 1rem; border-radius: 10px; }
    .timer-box { background-color: #3498db; color: white; padding: 0.5rem; border-radius: 5px; text-align: center; font-size: 1.2em; font-weight: bold; }
    .timer-warning { background-color: #e74c3c; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Cuestionario Médico Pro")
st.markdown("---")

# CARGAR DATOS
if not st.session_state.cargado:
    with st.spinner("Cargando..."):
        try:
            import subprocess, sys
            try:
                import gdown
            except:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])
                import gdown
            
            file_id = "1PXszau9XOTummO8t66XRCVxvGL3KhYN6"
            gdown.download(f"https://drive.google.com/uc?id={file_id}", "temp.xlsx", quiet=True)
            
            df = pd.read_excel("temp.xlsx")
            df.columns = df.columns.str.strip()
            st.session_state.preguntas = procesar_preguntas(df)
            
            if st.session_state.preguntas:
                st.session_state.temas_disponibles = get_temas(st.session_state.preguntas)
                st.session_state.cargado = True
                st.success(f"✅ {len(st.session_state.preguntas)} preguntas cargadas")
            else:
                st.error("❌ No se procesaron preguntas")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.stop()

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Configuración")
    
    if st.session_state.cargado:
        # Modo oscuro
        modo_nuevo = st.toggle("🌙 Modo Oscuro", value=st.session_state.modo_oscuro)
        if modo_nuevo != st.session_state.modo_oscuro:
            st.session_state.modo_oscuro = modo_nuevo
            st.rerun()
        
        st.session_state.voz_activada = st.toggle("🔊 Lector de Voz", value=st.session_state.voz_activada)
        
        tema_nuevo = st.selectbox("📚 Tema", options=st.session_state.temas_disponibles,
                                  index=st.session_state.temas_disponibles.index(st.session_state.tema_seleccionado))
        if tema_nuevo != st.session_state.tema_seleccionado:
            st.session_state.tema_seleccionado = tema_nuevo
            st.session_state.indice = 0
            st.session_state.respondido = False
            st.rerun()
        
        st.session_state.modo_repaso = st.toggle("🎯 Modo Repaso", value=st.session_state.modo_repaso)
        st.session_state.tiempo_pregunta = st.slider("⏱️ Tiempo (seg)", 10, 120, 30)
        
        st.markdown("---")
        st.header("📊 Estadísticas")
        total = st.session_state.correctas + st.session_state.incorrectas
        st.markdown(f"""
        <div class="stats-box">
            <p>✅ Correctas: {st.session_state.correctas}</p>
            <p>❌ Incorrectas: {st.session_state.incorrectas}</p>
            <p>📊 Total: {total}</p>
            <p>🎯 Precisión: {(st.session_state.correctas/total*100 if total > 0 else 0):.1f}%</p>
            <p>📝 En repaso: {len(st.session_state.preguntas_falladas)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("💾 Guardar"):
            guardar_progreso()
            st.success("✅ Guardado")
        
        if st.button("🔄 Reiniciar"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# MOSTRAR PREGUNTAS
if st.session_state.cargado:
    preguntas_filtradas = filtrar_tema(st.session_state.preguntas, st.session_state.tema_seleccionado)
    
    if st.session_state.modo_repaso and st.session_state.preguntas_falladas:
        ids_falladas = [p['id'] for p in st.session_state.preguntas_falladas]
        preguntas_mostrar = [p for p in preguntas_filtradas if p['id'] in ids_falladas]
        if not preguntas_mostrar:
            st.warning("⚠️ No hay falladas en este tema")
            preguntas_mostrar = preguntas_filtradas
    else:
        preguntas_mostrar = preguntas_filtradas
    
    if st.session_state.indice == 0 and not st.session_state.respondido:
        random.shuffle(preguntas_mostrar)
    
    total = len(preguntas_mostrar)
    
    if total > 0 and st.session_state.indice < total:
        preg = preguntas_mostrar[st.session_state.indice]
        
        # Iniciar tiempo
        if st.session_state.tiempo_inicio is None:
            st.session_state.tiempo_inicio = time.time()
        
        # Calcular tiempo (solo una vez por render)
        tiempo_transcurrido = time.time() - st.session_state.tiempo_inicio
        tiempo_restante = max(0, st.session_state.tiempo_pregunta - tiempo_transcurrido)
        
        # SOLO UN RELOJ
        timer_class = "timer-box timer-warning" if tiempo_restante < 10 else "timer-box"
        st.markdown(f'<div class="{timer_class}">⏱️ {formatear_tiempo(tiempo_restante)}</div>', unsafe_allow_html=True)
        
        # Auto-refresh cada 1 segundo usando JavaScript (mejor que time.sleep)
        if not st.session_state.respondido and tiempo_restante > 0:
            st.markdown("""
            <script>
            setTimeout(function() {
                window.location.reload();
            }, 1000);
            </script>
            """, unsafe_allow_html=True)
        
        # Verificar tiempo agotado
        if tiempo_restante <= 0 and not st.session_state.respondido:
            st.error("⏰ ¡Tiempo agotado!")
            st.session_state.respondido = True
            st.session_state.incorrectas += 1
            if preg not in st.session_state.preguntas_falladas:
                st.session_state.preguntas_falladas.append(preg)
            st.rerun()
        
        # Barra de progreso
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(st.session_state.indice / total)
        with col2:
            st.markdown(f"**{st.session_state.indice + 1}/{total}**")
        
        # TEMA
        st.markdown(f"**📚 Tema:** *{preg['tema']}*")
        
        # CASO CLÍNICO - AQUÍ ESTÁ EL TEXTO
        with st.expander("📋 Ver Caso Clínico", expanded=True):
            st.markdown(preg['caso'])
            if st.session_state.voz_activada:
                if st.button("🔊 Escuchar", key=f"voz_{st.session_state.indice}"):
                    leer_texto(preg['caso'])
        
        st.markdown("---")
        st.subheader("Selecciona tu respuesta:")
        
        # OPCIONES
        opciones = [
            f"A) {preg['opciones']['A']}",
            f"B) {preg['opciones']['B']}",
            f"C) {preg['opciones']['C']}",
            f"D) {preg['opciones']['D']}"
        ]
        
        respuesta = st.radio("Elige:", options=opciones, index=None, key=f"resp_{st.session_state.indice}")
        
        if not st.session_state.respondido:
            if st.button("✅ Responder", type="primary"):
                if respuesta is None:
                    st.warning("⚠️ Selecciona una opción")
                else:
                    st.session_state.respondido = True
                    seleccion = respuesta[0]
                    
                    if seleccion == preg['respuesta']:
                        st.session_state.correctas += 1
                        st.session_state.ultima_correcta = True
                        st.session_state.preguntas_falladas = [p for p in st.session_state.preguntas_falladas if p['id'] != preg['id']]
                    else:
                        st.session_state.incorrectas += 1
                        st.session_state.ultima_correcta = False
                        if preg not in st.session_state.preguntas_falladas:
                            st.session_state.preguntas_falladas.append(preg)
                    
                    st.rerun()
        else:
            # RESULTADO
            if st.session_state.ultima_correcta:
                st.markdown('<div class="correct"><h3>✅ ¡CORRECTO!</h3></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="incorrect"><h3>❌ Incorrecto</h3><p>Respuesta: <b>{preg["respuesta"]}</b></p></div>', unsafe_allow_html=True)
            
            with st.expander("📖 Ver Explicación", expanded=True):
                st.markdown(preg['explicacion'])
                if st.session_state.voz_activada:
                    if st.button("🔊 Escuchar explicación", key=f"exp_{st.session_state.indice}"):
                        leer_texto(preg['explicacion'])
            
            if st.button("➡️ Siguiente", type="primary"):
                st.session_state.indice += 1
                st.session_state.respondido = False
                st.session_state.tiempo_inicio = None
                st.rerun()
    
    else:
        # FIN
        st.balloons()
        st.success("🎉 ¡Completado!")
        total = st.session_state.correctas + st.session_state.incorrectas
        prec = (st.session_state.correctas/total*100 if total > 0 else 0)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("✅", st.session_state.correctas)
        c2.metric("❌", st.session_state.incorrectas)
        c3.metric("📊", f"{prec:.1f}%")
        c4.metric("📝", len(st.session_state.preguntas_falladas))
        
        if st.button("🔄 Reiniciar"):
            st.session_state.indice = 0
            st.session_state.correctas = 0
            st.session_state.incorrectas = 0
            st.session_state.respondido = False
            st.session_state.tiempo_inicio = None
            st.rerun()

st.markdown("---")
st.markdown("*🏥 Cuestionario Médico Pro*")
