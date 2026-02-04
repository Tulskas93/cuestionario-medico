import streamlit as st
import pandas as pd
import random
import re
import json
import os
from datetime import datetime

# Configuración inicial
st.set_page_config(
    page_title="Cuestionario Médico",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ============================================
# INICIALIZAR SESSION STATE
# ============================================
defaults = {
    'preguntas': [],
    'preguntas_filtradas': [],
    'indice': 0,
    'correctas': 0,
    'incorrectas': 0,
    'respondido': False,
    'cargado': False,
    'tema_seleccionado': "Todos",
    'modo_repaso': False,
    'preguntas_falladas': [],
    'modo_oscuro': False,
    'voz_activada': False,
    'mostrar_resultado': False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

PROGRESO_FILE = "progreso_medico.json"

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def cargar_progreso():
    """Carga progreso guardado"""
    if os.path.exists(PROGRESO_FILE):
        try:
            with open(PROGRESO_FILE, 'r', encoding='utf-8') as f:
                datos = json.load(f)
                st.session_state.correctas = datos.get('correctas', 0)
                st.session_state.incorrectas = datos.get('incorrectas', 0)
                st.session_state.preguntas_falladas = datos.get('falladas', [])
                return True
        except:
            pass
    return False

def guardar_progreso():
    """Guarda progreso actual"""
    datos = {
        'fecha': datetime.now().isoformat(),
        'correctas': st.session_state.correctas,
        'incorrectas': st.session_state.incorrectas,
        'falladas': st.session_state.preguntas_falladas,
        'total_preguntas': len(st.session_state.preguntas)
    }
    with open(PROGRESO_FILE, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def hablar(texto, tipo="mujer"):
    """Lector de voz con voz femenina dulce"""
    if not st.session_state.voz_activada:
        return
    
    # Limpiar texto para JavaScript
    texto_limpio = texto.replace('"', "'").replace('\n', ' ').replace('\r', '')
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()[:500]  # Limitar longitud
    
    js = f"""
    <script>
    (function() {{
        if ('speechSynthesis' in window) {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance();
            msg.text = "{texto_limpio}";
            msg.lang = 'es-ES';
            msg.rate = 0.85;
            msg.pitch = 1.2;
            msg.volume = 1.0;
            
            // Buscar voz femenina española
            var voces = window.speechSynthesis.getVoices();
            var vozFemenina = voces.find(function(v) {{
                return v.lang.includes('es') && (v.name.includes('Female') || 
                       v.name.includes('Mujer') || v.name.includes('Monica') || 
                       v.name.includes('Helena') || v.name.includes('Laura'));
            }});
            
            if (vozFemenina) {{
                msg.voice = vozFemenina;
            }}
            
            window.speechSynthesis.speak(msg);
        }}
    }})();
    </script>
    """
    st.components.v1.html(js, height=0)

def extraer_preguntas(df):
    """Extrae preguntas del Excel con formato texto plano"""
    preguntas = []
    
    for idx, row in df.iterrows():
        try:
            texto = str(row.get('Pregunta', ''))
            respuesta = str(row.get('Respuesta correcta', '')).strip().upper()
            explicacion = str(row.get('Retroalimentación', ''))
            tema = str(row.get('Tema', 'General'))
            
            # Encontrar posiciones de opciones
            pos_a = texto.find('A)')
            pos_b = texto.find('B)')
            pos_c = texto.find('C)')
            pos_d = texto.find('D)')
            
            # Validar que existan todas
            if any(p == -1 for p in [pos_a, pos_b, pos_c, pos_d]):
                continue
            
            # Extraer partes
            caso = texto[:pos_a].strip()
            op_a = texto[pos_a+2:pos_b].strip()
            op_b = texto[pos_b+2:pos_c].strip()
            op_c = texto[pos_c+2:pos_d].strip()
            op_d = texto[pos_d+2:].strip()
            
            # Limpiar saltos de línea
            caso = caso.replace('\n', ' ')
            op_a = op_a.replace('\n', ' ')
            op_b = op_b.replace('\n', ' ')
            op_c = op_c.replace('\n', ' ')
            op_d = op_d.replace('\n', ' ')
            
            # Crear ID único
            pregunta_id = f"{tema}_{idx}_{caso[:30]}"
            
            preguntas.append({
                'id': pregunta_id,
                'caso': caso,
                'opciones': {
                    'A': op_a,
                    'B': op_b,
                    'C': op_c,
                    'D': op_d
                },
                'respuesta_correcta': respuesta,
                'explicacion': explicacion,
                'tema': tema
            })
            
        except Exception as e:
            continue
    
    return preguntas

def obtener_temas(preguntas):
    """Obtiene lista única de temas"""
    temas = sorted(list(set(p['tema'] for p in preguntas)))
    return ["Todos"] + temas

def filtrar_preguntas(preguntas, tema):
    """Filtra por tema seleccionado"""
    if tema == "Todos":
        return preguntas[:]
    return [p for p in preguntas if p['tema'] == tema]

def preparar_preguntas():
    """Prepara lista final según modo y filtros"""
    lista = filtrar_preguntas(st.session_state.preguntas, st.session_state.tema_seleccionado)
    
    # Modo repaso: solo falladas
    if st.session_state.modo_repaso:
        ids_falladas = [f['id'] for f in st.session_state.preguntas_falladas]
        lista = [p for p in lista if p['id'] in ids_falladas]
        if not lista:
            st.warning("⚠️ No hay preguntas falladas en este tema")
            lista = filtrar_preguntas(st.session_state.preguntas, st.session_state.tema_seleccionado)
    
    return lista

# ============================================
# CSS - MODO OSCURO PERFECTO
# ============================================

def aplicar_css():
    if st.session_state.modo_oscuro:
        st.markdown("""
        <style>
        /* Fondo general oscuro */
        .stApp {
            background-color: #0d1117;
        }
        
        /* Texto claro en todo */
        .stApp, .stMarkdown, p, h1, h2, h3, h4, h5, h6, label, .stRadio label {
            color: #c9d1d9 !important;
        }
        
        /* Contenedores */
        .stExpander {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 10px;
        }
        
        /* Botones */
        .stButton>button {
            background-color: #238636;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1rem;
        }
        
        .stButton>button:hover {
            background-color: #2ea043;
        }
        
        /* Sidebar */
        .css-1d391kg, .css-163ttbj {
            background-color: #161b22;
        }
        
        /* Radio buttons */
        .stRadio > div {
            background-color: #161b22;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #30363d;
        }
        
        /* Correcto/Incorrecto */
        .box-correcto {
            background-color: #0f3d0f;
            border-left: 5px solid #3fb950;
            color: #aff5b4;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .box-incorrecto {
            background-color: #3d0f0f;
            border-left: 5px solid #f85149;
            color: #ffdcd7;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Estadísticas */
        .stats-box {
            background-color: #161b22;
            border: 1px solid #30363d;
            padding: 1rem;
            border-radius: 10px;
            color: #c9d1d9;
        }
        
        /* Selectbox y otros inputs */
        .stSelectbox, .stSlider {
            background-color: #21262d;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .box-correcto {
            background-color: #d4edda;
            border-left: 5px solid #28a745;
            color: #155724;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .box-incorrecto {
            background-color: #f8d7da;
            border-left: 5px solid #dc3545;
            color: #721c24;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .stats-box {
            background-color: #e7f3ff;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #b6d4fe;
        }
        </style>
        """, unsafe_allow_html=True)

aplicar_css()

# ============================================
# INTERFAZ PRINCIPAL
# ============================================

st.title("🏥 Cuestionario Médico")
st.markdown("---")

# ============================================
# CARGA DE DATOS
# ============================================

if not st.session_state.cargado:
    with st.spinner("📂 Cargando preguntas..."):
        try:
            # URL del archivo en GitHub (cambiar por tu URL)
            URL_EXCEL = "https://raw.githubusercontent.com/Tulskas93/cuestionario-medico/main/tus_preguntas.xlsx"
            
            df = pd.read_excel(URL_EXCEL)
            df.columns = df.columns.str.strip()
            
            st.session_state.preguntas = extraer_preguntas(df)
            
            if st.session_state.preguntas:
                st.session_state.temas_disponibles = obtener_temas(st.session_state.preguntas)
                
                # Intentar cargar progreso anterior
                if cargar_progreso():
                    st.success(f"✅ {len(st.session_state.preguntas)} preguntas cargadas + progreso recuperado")
                else:
                    st.success(f"✅ {len(st.session_state.preguntas)} preguntas cargadas")
                
                st.session_state.cargado = True
                st.rerun()
            else:
                st.error("❌ No se pudieron procesar las preguntas. Verifica el formato del Excel.")
                
        except Exception as e:
            st.error(f"❌ Error cargando datos: {str(e)}")
            st.info("💡 Asegúrate de que el archivo Excel esté en GitHub con acceso público")
            st.stop()

# ============================================
# SIDEBAR - CONFIGURACIÓN
# ============================================

with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Modo oscuro
    oscuro = st.toggle("🌙 Modo Oscuro", value=st.session_state.modo_oscuro)
    if oscuro != st.session_state.modo_oscuro:
        st.session_state.modo_oscuro = oscuro
        st.rerun()
    
    # Voz
    st.session_state.voz_activada = st.toggle("🔊 Voz Femenina", value=st.session_state.voz_activada)
    
    # Tema
    tema_nuevo = st.selectbox(
        "📚 Tema",
        options=st.session_state.temas_disponibles,
        index=st.session_state.temas_disponibles.index(st.session_state.tema_seleccionado) if st.session_state.tema_seleccionado in st.session_state.temas_disponibles else 0
    )
    if tema_nuevo != st.session_state.tema_seleccionado:
        st.session_state.tema_seleccionado = tema_nuevo
        st.session_state.indice = 0
        st.session_state.respondido = False
        st.session_state.mostrar_resultado = False
        st.rerun()
    
    # Modo repaso
    repaso = st.toggle("🎯 Modo Repaso (falladas)", value=st.session_state.modo_repaso)
    if repaso != st.session_state.modo_repaso:
        st.session_state.modo_repaso = repaso
        st.session_state.indice = 0
        st.session_state.respondido = False
        st.session_state.mostrar_resultado = False
        st.rerun()
    
    st.markdown("---")
    
    # Estadísticas
    st.header("📊 Estadísticas")
    total_resp = st.session_state.correctas + st.session_state.incorrectas
    precision = (st.session_state.correctas / total_resp * 100) if total_resp > 0 else 0
    
    st.markdown(f"""
    <div class="stats-box">
        <p>✅ <b>Correctas:</b> {st.session_state.correctas}</p>
        <p>❌ <b>Incorrectas:</b> {st.session_state.incorrectas}</p>
        <p>📊 <b>Total:</b> {total_resp}</p>
        <p>🎯 <b>Precisión:</b> {precision:.1f}%</p>
        <p>📝 <b>En repaso:</b> {len(st.session_state.preguntas_falladas)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Botones
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar"):
            guardar_progreso()
            st.success("✅ Guardado")
    with col2:
        if st.button("🔄 Reiniciar"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ============================================
# MOSTRAR PREGUNTAS
# ============================================

if st.session_state.cargado:
    # Preparar lista de preguntas
    preguntas_lista = preparar_preguntas()
    
    if not preguntas_lista:
        st.warning("⚠️ No hay preguntas disponibles")
        st.stop()
    
    # Barajar si es primera vez
    if st.session_state.indice == 0 and not st.session_state.respondido:
        random.shuffle(preguntas_lista)
        st.session_state.preguntas_filtradas = preguntas_lista
    
    preguntas_lista = st.session_state.preguntas_filtradas
    total = len(preguntas_lista)
    
    # Verificar si terminó
    if st.session_state.indice >= total:
        st.balloons()
        st.success("🎉 ¡Felicitaciones! Has completado todas las preguntas")
        
        precision_final = (st.session_state.correctas / (st.session_state.correctas + st.session_state.incorrectas) * 100) if (st.session_state.correctas + st.session_state.incorrectas) > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("✅ Correctas", st.session_state.correctas)
        col2.metric("❌ Incorrectas", st.session_state.incorrectas)
        col3.metric("🎯 Precisión", f"{precision_final:.1f}%")
        
        if st.button("🔄 Volver a empezar", type="primary"):
            st.session_state.indice = 0
            st.session_state.respondido = False
            st.session_state.mostrar_resultado = False
            st.rerun()
        
        if st.button("🎯 Practicar falladas") and st.session_state.preguntas_falladas:
            st.session_state.modo_repaso = True
            st.session_state.indice = 0
            st.session_state.respondido = False
            st.session_state.mostrar_resultado = False
            st.rerun()
        
        st.stop()
    
    # Mostrar pregunta actual
    pregunta = preguntas_lista[st.session_state.indice]
    
    # Progreso
    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(st.session_state.indice / total)
    with col2:
        st.markdown(f"**{st.session_state.indice + 1} / {total}**")
    
    # Tema
    st.markdown(f"**📚 Tema:** *{pregunta['tema']}*")
    
    # Caso clínico
    with st.expander("📋 Leer Caso Clínico", expanded=True):
        st.markdown(f"### {pregunta['caso']}")
        if st.session_state.voz_activada:
            if st.button("🔊 Escuchar caso", key=f"btn_caso_{st.session_state.indice}"):
                hablar(pregunta['caso'])
    
    st.markdown("---")
    st.subheader("📝 Selecciona tu respuesta:")
    
    # Opciones
    opciones_texto = [
        f"A) {pregunta['opciones']['A']}",
        f"B) {pregunta['opciones']['B']}",
        f"C) {pregunta['opciones']['C']}",
        f"D) {pregunta['opciones']['D']}"
    ]
    
    # Si no ha respondido, mostrar radio
    if not st.session_state.respondido:
        respuesta_seleccionada = st.radio(
            "Elige una opción:",
            options=opciones_texto,
            index=None,
            key=f"radio_{st.session_state.indice}"
        )
        
        if st.button("✅ Responder", type="primary", use_container_width=True):
            if respuesta_seleccionada is None:
                st.warning("⚠️ Por favor selecciona una respuesta")
            else:
                # Procesar respuesta
                letra_elegida = respuesta_seleccionada[0]  # A, B, C o D
                es_correcta = letra_elegida == pregunta['respuesta_correcta']
                
                # Actualizar estadísticas
                if es_correcta:
                    st.session_state.correctas += 1
                    # Quitar de falladas si existe
                    st.session_state.preguntas_falladas = [
                        f for f in st.session_state.preguntas_falladas 
                        if f['id'] != pregunta['id']
                    ]
                else:
                    st.session_state.incorrectas += 1
                    # Agregar a falladas si no existe
                    if not any(f['id'] == pregunta['id'] for f in st.session_state.preguntas_falladas):
                        st.session_state.preguntas_falladas.append(pregunta)
                
                # Guardar estado
                st.session_state.ultima_respuesta_correcta = es_correcta
                st.session_state.letra_elegida = letra_elegida
                st.session_state.respondido = True
                
                # Leer resultado en voz
                if st.session_state.voz_activada:
                    mensaje_voz = "¡Correcto!" if es_correcta else f"Incorrecto. La respuesta correcta es {pregunta['respuesta_correcta']}"
                    hablar(mensaje_voz)
                
                st.rerun()
    
    # Si ya respondió, mostrar resultado
    else:
        es_correcta = st.session_state.ultima_respuesta_correcta
        
        if es_correcta:
            st.markdown(f"""
            <div class="box-correcto">
                <h3>✅ ¡CORRECTO!</h3>
                <p>Muy bien, pequeñín. Sigues así. 🌸</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="box-incorrecto">
                <h3>❌ Incorrecto</h3>
                <p>Tu respuesta: <b>{st.session_state.letra_elegida}</b></p>
                <p>Respuesta correcta: <b>{pregunta['respuesta_correcta']}</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Explicación
        with st.expander("📖 Ver Explicación", expanded=True):
            st.markdown(pregunta['explicacion'])
            if st.session_state.voz_activada:
                if st.button("🔊 Escuchar explicación", key=f"btn_exp_{st.session_state.indice}"):
                    hablar(pregunta['explicacion'])
        
        # Botón siguiente
        if st.button("➡️ Siguiente pregunta", type="primary", use_container_width=True):
            st.session_state.indice += 1
            st.session_state.respondido = False
            st.session_state.mostrar_resultado = False
            st.rerun()

st.markdown("---")
st.markdown("*🏥 Cuestionario Médico - Hecho con 💕 para ti, pequeñín*")
