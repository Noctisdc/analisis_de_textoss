import re
import time
import pandas as pd
import streamlit as st
from textblob import TextBlob
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Detective de textos", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Special+Elite&display=swap');
.stApp {
    background-color: #efe6d2;
}
[data-testid="stHeader"] {
    background: transparent;
}
section[data-testid="stSidebar"] {
    background-color: #ddd0b3;
}
.stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3 {
    color: #2b2b2b;
}
[data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
    color: #2b2b2b !important;
}
h1, h2, h3 {
    font-family: 'Special Elite', cursive;
}
textarea {
    background-color: #fffaf0 !important;
    color: #2b2b2b !important;
}
div.stButton > button {
    background-color: #2b2b2b;
    color: #efe6d2 !important;
    border-radius: 4px;
    border: none;
    padding: 8px 24px;
    font-family: 'Special Elite', cursive;
}
div.stButton > button:hover {
    background-color: #b3261e;
}
.sello {
    display: inline-block;
    border: 4px solid #b3261e;
    color: #b3261e !important;
    font-family: 'Special Elite', cursive;
    font-size: 30px;
    padding: 4px 16px;
    transform: rotate(-4deg);
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

vacias = set("""a al algo ante con como cual cuando de del desde donde el ella ellos en entre era es esa ese eso esta este esto
fue ha han hay la las le les lo los me mi mis muy nada ni no nos o otra otro para pero por porque que quien se si sin sobre
son su sus también te tiene tu un una uno unos y ya yo the an and are as at be but by for from had has have he her his i if
in is it its my of on or our she so that their them they this to was we were what with you your""".split())

ejemplos = {
    "Escribir el mío": "",
    "Reseña de un viaje": "El viaje a Japón fue increíble. Los templos de Kyoto son hermosos y la gente fue muy amable. La comida estuvo deliciosa en cada ciudad. Volvería mañana mismo.",
    "Queja de un cliente": "El pedido llegó tarde y la caja estaba rota. Nadie respondió mis mensajes. El servicio fue pésimo y estoy muy decepcionado. No pienso volver a comprar aquí.",
    "Noticia neutra": "La empresa abrirá una nueva sede el próximo mes. El edificio tiene tres pisos. Se contratará a cincuenta personas.",
}


@st.cache_data(show_spinner=False)
def traducir_frases(frases):
    salida = []
    fallos = 0
    for f in frases:
        traducida = f
        exito = False
        for intento in range(3):
            try:
                traducida = GoogleTranslator(source="auto", target="en").translate(f)
                exito = True
                break
            except Exception:
                time.sleep(1.5)
        if not exito:
            fallos += 1
        salida.append(traducida)
        time.sleep(0.25)
    return salida, fallos


def humor(p):
    if p > 0.25:
        return "POSITIVO", "El texto respira entusiasmo. Todo apunta a un ánimo alegre."
    if p > 0.05:
        return "ALGO POSITIVO", "Hay buen ánimo, aunque sin exagerar."
    if p < -0.25:
        return "NEGATIVO", "El texto está cargado de queja o tristeza. El ánimo es sombrío."
    if p < -0.05:
        return "ALGO NEGATIVO", "Hay cierto malestar entre líneas."
    return "NEUTRAL", "El texto no se inclina hacia ningún lado. Informa sin mostrar emociones."


def analizar(texto, limite):
    frases = [f.strip() for f in re.split(r"[.!?\n]+", texto) if f.strip()][:limite]
    if len(frases) == 0:
        return None
    traducidas, fallos = traducir_frases(tuple(frases))
    polaridades = [TextBlob(t).sentiment.polarity for t in traducidas]
    general = TextBlob(" ".join(traducidas)).sentiment
    palabras = re.findall(r"\b\w+\b", texto.lower())
    claves = [p for p in palabras if p not in vacias and len(p) > 2]
    return {
        "frases": frases,
        "polaridades": polaridades,
        "sentimiento": general.polarity,
        "subjetividad": general.subjectivity,
        "palabras": palabras,
        "claves": claves,
        "fallos": fallos,
    }


with st.sidebar:
    st.subheader("Agencia de detectives")
    st.write("Entrega una pista escrita y el detective te devuelve su informe: ánimo, opinión, palabras sospechosas y frases clave.")
    entrada = st.radio("¿Cómo entregas la pista?", ["Escribir o pegar", "Subir archivo"])
    limite = st.slider("Frases a investigar", 3, 20, 10)
    st.caption("Cada frase se traduce al inglés para poder analizarla, así que más frases tardan más.")

st.title("🕵️ Detective de textos")
st.write("Un texto llega a la oficina y nadie sabe qué siente. El detective lo va a descubrir.")

texto = ""

if entrada == "Escribir o pegar":
    caso = st.selectbox("Elige un caso", list(ejemplos.keys()))
    texto = st.text_area("Pista (el texto a investigar)", value=ejemplos[caso], height=180, key=f"txt_{caso}")
else:
    archivo = st.file_uploader("Sube la pista", type=["txt", "md", "csv"])
    if archivo is not None:
        texto = archivo.getvalue().decode("utf-8", errors="ignore")
        with st.expander("Ver la pista"):
            st.text(texto[:1000])

if st.button("Abrir el caso"):
    if texto.strip() == "":
        st.warning("El detective necesita una pista. Escribe o sube un texto.")
    else:
        with st.spinner("El detective está investigando..."):
            resultado = analizar(texto[:3000], limite)
        if resultado is None:
            st.warning("No encontré frases en ese texto.")
        else:
            st.session_state.informe = resultado

inf = st.session_state.get("informe")

if inf:
    st.divider()
    etiqueta, frase_veredicto = humor(inf["sentimiento"])

    st.header("Informe del caso")
    st.markdown(f'<div class="sello">{etiqueta}</div>', unsafe_allow_html=True)
    st.write(frase_veredicto)

    if inf["fallos"] > 0:
        st.warning(f"No pude traducir {inf['fallos']} frase(s), así que el resultado puede ser menos preciso. Intenta de nuevo en un minuto.")

    st.write("**Ánimo del texto**")
    st.progress((inf["sentimiento"] + 1) / 2)

    st.write("**Opinión frente a hechos**")
    st.progress(inf["subjetividad"])
    if inf["subjetividad"] > 0.5:
        st.write("El testigo opina más de lo que informa.")
    else:
        st.write("El testigo se ciñe a los hechos.")

    total = len(inf["palabras"])
    unicas = len(set(inf["palabras"]))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Palabras", total)
    c2.metric("Frases", len(inf["frases"]))
    c3.metric("Únicas", unicas)
    c4.metric("Riqueza", f"{unicas / total:.0%}" if total else "0%")

    st.subheader("Línea de tiempo emocional")
    st.line_chart(pd.DataFrame({"Ánimo": inf["polaridades"]}, index=range(1, len(inf["polaridades"]) + 1)))
    st.caption("Cada punto es una frase. Arriba es positivo y abajo es negativo.")

    st.subheader("Palabras sospechosas")
    lista_palabras = ""
    if inf["claves"]:
        top = pd.Series(inf["claves"]).value_counts().head(10)
        st.bar_chart(top)
        lista_palabras = "\n".join(f"- {p}: {n}" for p, n in top.items())
    else:
        st.write("No hay palabras clave en este texto.")

    pol = inf["polaridades"]
    mejor = pol.index(max(pol))
    peor = pol.index(min(pol))
    st.subheader("Frases clave")
    st.write(f"**La más positiva** ({pol[mejor]:.2f}): {inf['frases'][mejor]}")
    st.write(f"**La más negativa** ({pol[peor]:.2f}): {inf['frases'][peor]}")

    informe_txt = (
        f"INFORME DEL CASO\n\n"
        f"Veredicto: {etiqueta}\n"
        f"Ánimo: {inf['sentimiento']:.2f}\n"
        f"Subjetividad: {inf['subjetividad']:.2f}\n"
        f"Palabras: {total}\n"
        f"Frases: {len(inf['frases'])}\n\n"
        f"Palabras sospechosas:\n{lista_palabras}\n"
    )
    st.download_button("Descargar informe", informe_txt, file_name="informe.txt")

with st.expander("¿Cómo trabaja el detective?"):
    st.write("**Ánimo:** va de -1 (muy negativo) a 1 (muy positivo).")
    st.write("**Subjetividad:** va de 0 (solo hechos) a 1 (pura opinión).")
    st.write("**Riqueza:** porcentaje de palabras distintas sobre el total. Más alto significa vocabulario más variado.")
