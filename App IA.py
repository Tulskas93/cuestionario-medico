import streamlit as st
from model import generar_imagen

st.set_page_config(page_title="IA Local Segura", layout="centered")

st.title("🎨 IA generadora de imágenes (local y segura)")
st.caption("La IA no tiene acceso a tus archivos ni fotos 🛡️")

prompt = st.text_input("Describe la imagen")

steps = st.slider("Steps", 10, 50, 30)
cfg = st.slider("CFG Scale", 1.0, 15.0, 7.5)

if st.button("Generar imagen"):
    if prompt.strip() == "":
        st.warning("Escribe algo primero 😅")
    else:
        with st.spinner("Generando imagen..."):
            img = generar_imagen(prompt, steps, cfg)
            st.image(img, caption="Resultado ✨")
