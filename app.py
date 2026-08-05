import html
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlunsplit

import streamlit as st
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Offsave — Descargador",
    page_icon="⏻",
    layout="centered",
)

MAX_FILE_SIZE_MB = 450


# =========================================================
# ESTILO RETRO INSPIRADO EN WEBS DE DESCARGA DE 2011
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --retro-black: #050505;
        --retro-paper: #dbe3e3;
        --retro-light: #f1f4f3;
        --retro-yellow: #f1ff00;
        --retro-muted: #667171;
    }

    html,
    body,
    [class*="css"] {
        font-family: Arial, Helvetica, sans-serif;
    }

    .stApp {
        color: var(--retro-black);
        background-color: var(--retro-paper);
        background-image:
            radial-gradient(
                circle at 15% 20%,
                rgba(255, 255, 255, 0.45),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 70%,
                rgba(0, 0, 0, 0.045),
                transparent 28%
            ),
            repeating-linear-gradient(
                0deg,
                rgba(255, 255, 255, 0.04) 0,
                rgba(255, 255, 255, 0.04) 1px,
                transparent 1px,
                transparent 4px
            );
    }

    header[data-testid="stHeader"],
    #MainMenu,
    footer {
        display: none;
    }

    .block-container {
        width: 100%;
        max-width: 800px;
        padding-top: 54px;
        padding-bottom: 80px;
    }

    .retro-brand {
        margin: 0 auto 34px;
        text-align: center;
        user-select: none;
    }

    .retro-wordmark {
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--retro-black);
        font-family: "Trebuchet MS", Arial, sans-serif;
        font-size: clamp(54px, 10vw, 88px);
        font-weight: 700;
        line-height: 0.95;
        letter-spacing: -7px;
    }

    .retro-power {
        display: inline-flex;
        width: 0.93em;
        height: 0.93em;
        margin-right: 5px;
        align-items: center;
        justify-content: center;
        color: var(--retro-paper);
        background: var(--retro-black);
        border-radius: 50%;
        font-size: 0.72em;
        letter-spacing: 0;
    }

    .retro-tagline {
        margin-top: 12px;
        padding-left: 18px;
        color: var(--retro-black);
        font-size: clamp(11px, 2.4vw, 17px);
        font-weight: 700;
        letter-spacing: 7px;
        text-transform: lowercase;
    }

    .retro-intro {
        max-width: 620px;
        margin: -8px auto 28px;
        color: #222;
        font-size: 14px;
        line-height: 1.55;
        text-align: center;
    }

    .retro-section-title {
        margin: 34px 0 5px;
        color: var(--retro-black);
        font-size: 27px;
        font-weight: 900;
        text-align: center;
    }

    .retro-subtitle {
        margin: 4px 0 22px;
        color: #344041;
        font-size: 13px;
        text-align: center;
    }

    .video-title {
        margin: 18px 0 7px;
        color: var(--retro-black);
        font-size: 24px;
        font-weight: 900;
        line-height: 1.2;
        text-align: center;
    }

    .video-author {
        margin-bottom: 20px;
        color: var(--retro-muted);
        font-size: 13px;
        text-align: center;
    }

    /* Tarjetas propias: no dependen del tema oscuro de Streamlit */
    .retro-stat-card {
        box-sizing: border-box;
        width: 100%;
        min-height: 104px;
        padding: 16px 18px;
        color: #050505 !important;
        background: #eef2f1 !important;
        border: 3px solid #050505;
        border-radius: 10px;
        text-align: left;
    }

    .retro-stat-label {
        margin-bottom: 5px;
        color: #4d595a !important;
        font-size: 13px;
        font-weight: 800;
        line-height: 1.2;
        opacity: 1 !important;
        -webkit-text-fill-color: #4d595a !important;
    }

    .retro-stat-value {
        color: #050505 !important;
        font-size: clamp(28px, 5vw, 38px);
        font-weight: 900;
        line-height: 1.25;
        text-align: center;
        opacity: 1 !important;
        -webkit-text-fill-color: #050505 !important;
    }

    div[data-testid="stForm"] {
        padding: 0;
        background: transparent;
        border: none;
    }

    div[data-testid="stTextInput"] label {
        color: var(--retro-black) !important;
        font-weight: 800 !important;
    }

    div[data-testid="stTextInput"] input {
        min-height: 64px;
        padding: 0 18px;
        color: var(--retro-black) !important;
        background: var(--retro-light) !important;
        border: 4px solid var(--retro-black) !important;
        border-radius: 10px !important;
        box-shadow:
            inset 0 2px 4px rgba(0, 0, 0, 0.18),
            0 2px 0 rgba(255, 255, 255, 0.55);
        font-size: 16px;
        font-weight: 700;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--retro-black) !important;
        box-shadow:
            inset 0 2px 4px rgba(0, 0, 0, 0.18),
            0 0 0 2px var(--retro-yellow) !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #7e8889;
        font-weight: 400;
    }

    div[data-testid="stFormSubmitButton"] button {
        width: 100%;
        min-height: 64px;
        padding: 0;
        color: white !important;
        background: var(--retro-black) !important;
        border: 4px solid var(--retro-black) !important;
        border-radius: 11px !important;
        box-shadow: 0 3px 0 rgba(255, 255, 255, 0.5);
        font-size: 19px;
        font-weight: 900;
        letter-spacing: 1px;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        color: var(--retro-yellow) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stFormSubmitButton"] button:active {
        transform: translateY(2px);
    }

    /* Contenedores de opciones */
    div[data-testid="stRadio"],
    div[data-testid="stSelectbox"] {
        padding: 13px 16px;
        margin-bottom: 10px;
        color: var(--retro-black) !important;
        background: rgba(241, 244, 243, 0.92) !important;
        border: 2px solid var(--retro-black);
        border-radius: 8px;
    }

    /* Fuerza contraste en títulos y opciones MP4 / MP3 */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] p,
    div[data-testid="stRadio"] span,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] p,
    div[role="radiogroup"] label,
    div[role="radiogroup"] label p {
        color: var(--retro-black) !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    /* Mantiene visible el texto del selector */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        color: #ffffff !important;
        background: #252832 !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] span,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] input {
        color: #ffffff !important;
        opacity: 1 !important;
    }

    /* Tarjetas de duración y tipo */
    div[data-testid="stMetric"] {
        min-height: 102px;
        padding: 14px 17px;
        color: var(--retro-black) !important;
        background: #eef2f1 !important;
        border: 3px solid var(--retro-black) !important;
        border-radius: 9px;
        text-align: center;
    }

    /* Etiquetas: Duración / Tipo */
    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p,
    div[data-testid="stMetricLabel"] div,
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] label p {
        color: #525e5f !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }

    /* Valores: 01:18:52 / Youtube */
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div,
    div[data-testid="stMetricValue"] p {
        color: var(--retro-black) !important;
        opacity: 1 !important;
        font-weight: 900 !important;
    }

    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] * {
        color: var(--retro-black) !important;
        opacity: 1 !important;
    }

    .retro-subtitle,
    .video-author {
        color: #344041 !important;
        opacity: 1 !important;
    }

    div[data-testid="stButton"] button {
        width: 100%;
        min-height: 54px;
        color: white !important;
        background: var(--retro-black) !important;
        border: 3px solid var(--retro-black) !important;
        border-radius: 9px !important;
        font-size: 16px;
        font-weight: 900;
    }

    div[data-testid="stButton"] button:hover {
        color: var(--retro-yellow) !important;
    }

    div[data-testid="stDownloadButton"] button {
        width: 100%;
        min-height: 72px;
        color: var(--retro-black) !important;
        background: var(--retro-yellow) !important;
        border: 4px solid var(--retro-black) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 0 rgba(0, 0, 0, 0.2);
        font-size: 19px;
        font-weight: 900;
    }

    div[data-testid="stDownloadButton"] button:hover {
        color: var(--retro-black) !important;
        background: #fbff4d !important;
        transform: translateY(-2px);
    }

    div[data-testid="stAlert"] {
        color: var(--retro-black);
        background: rgba(241, 244, 243, 0.95);
        border: 3px solid var(--retro-black);
        border-radius: 9px;
    }

    div[data-testid="stProgress"] > div > div {
        background: var(--retro-yellow);
    }

    div[data-testid="stImage"] img,
    video,
    audio {
        border: 4px solid var(--retro-black);
        border-radius: 9px;
        background: black;
    }

    hr {
        margin: 35px 0;
        border: none;
        border-top: 4px solid var(--retro-black);
    }

    .retro-footer {
        margin-top: 55px;
        padding-top: 20px;
        border-top: 2px solid rgba(0, 0, 0, 0.35);
        color: #354041;
        font-size: 12px;
        line-height: 1.6;
        text-align: center;
    }

    @media (max-width: 600px) {
        .block-container {
            padding: 30px 14px 55px;
        }

        .retro-wordmark {
            letter-spacing: -4px;
        }

        .retro-tagline {
            padding-left: 6px;
            letter-spacing: 4px;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stFormSubmitButton"] button {
            min-height: 58px;
        }
    }

    /*
     * ÚLTIMA CAPA DE CONTRASTE
     * Corrige instalaciones que siguen heredando el tema oscuro.
     */
    .stApp div[data-testid="stRadio"],
    .stApp div[data-testid="stRadio"] *,
    .stApp div[role="radiogroup"],
    .stApp div[role="radiogroup"] * {
        color: #050505 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #050505 !important;
    }

    .stApp div[data-testid="stRadio"] p,
    .stApp div[role="radiogroup"] p {
        color: #050505 !important;
        font-weight: 800 !important;
    }

    .stApp div[data-testid="stSelectbox"] > label,
    .stApp div[data-testid="stSelectbox"] > label *,
    .stApp div[data-testid="stTextInput"] > label,
    .stApp div[data-testid="stTextInput"] > label * {
        color: #050505 !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #050505 !important;
    }

    /* El campo cerrado del selector permanece oscuro con texto blanco */
    .stApp div[data-testid="stSelectbox"]
    div[data-baseweb="select"] > div,
    .stApp div[data-testid="stSelectbox"]
    div[data-baseweb="select"] > div * {
        color: #ffffff !important;
        opacity: 1 !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    /* No permitir que una regla del tema vuelva blancos los textos propios */
    .stApp .retro-stat-card,
    .stApp .retro-stat-card *,
    .stApp .retro-section-title,
    .stApp .retro-subtitle {
        opacity: 1 !important;
    }
    </style>

    <div class="retro-brand">
        <div class="retro-wordmark">
            <span class="retro-power">⏻</span>ffsave
        </div>
        <div class="retro-tagline">evidence of offline life</div>
    </div>

    <div class="retro-intro">
        Guarda contenido para verlo o escucharlo sin conexión.
        Elige MP4, MP3, calidad y el fragmento exacto que necesitas.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def segundos_a_tiempo(segundos: int | float | None) -> str:
    """Convierte segundos a HH:MM:SS o MM:SS."""
    if segundos is None:
        return "Desconocida"

    segundos = max(0, int(segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)

    if horas:
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    return f"{minutos:02d}:{segundos:02d}"


def tiempo_a_segundos(valor: str) -> int:
    """Acepta segundos, MM:SS o HH:MM:SS."""
    valor = valor.strip()

    if not valor:
        raise ValueError("El tiempo está vacío.")

    if re.fullmatch(r"\d+", valor):
        return int(valor)

    partes = valor.split(":")

    if len(partes) == 2:
        minutos, segundos = partes

        if not minutos.isdigit() or not segundos.isdigit():
            raise ValueError("Usa el formato MM:SS.")

        minutos = int(minutos)
        segundos = int(segundos)

        if segundos >= 60:
            raise ValueError("Los segundos deben ser menores de 60.")

        return minutos * 60 + segundos

    if len(partes) == 3:
        horas, minutos, segundos = partes

        if not all(parte.isdigit() for parte in partes):
            raise ValueError("Usa el formato HH:MM:SS.")

        horas = int(horas)
        minutos = int(minutos)
        segundos = int(segundos)

        if minutos >= 60 or segundos >= 60:
            raise ValueError(
                "Los minutos y segundos deben ser menores de 60."
            )

        return horas * 3600 + minutos * 60 + segundos

    raise ValueError(
        "Formato incorrecto. Ejemplos válidos: 01:30 o 1:02:30."
    )


def nombre_seguro(nombre: str) -> str:
    """Limpia el nombre para la descarga."""
    nombre = re.sub(r'[<>:"/\\|?*]', "", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre[:150] or "archivo"


FACEBOOK_DOMINIOS = {
    "facebook.com",
    "www.facebook.com",
    "m.facebook.com",
    "mobile.facebook.com",
    "web.facebook.com",
    "fb.watch",
    "www.fb.watch",
}


def es_enlace_facebook(enlace: str) -> bool:
    """Indica si el enlace pertenece a Facebook o fb.watch."""
    try:
        host = (urlsplit(enlace).hostname or "").lower()
    except ValueError:
        return False

    return host in FACEBOOK_DOMINIOS or host.endswith(".facebook.com")


def nombre_sitio(enlace: str | None) -> str:
    """Devuelve un nombre legible sin limitar los sitios compatibles."""
    if not enlace:
        return "El sitio"

    try:
        host = (urlsplit(enlace).hostname or "").lower()
    except ValueError:
        return "El sitio"

    host = host.removeprefix("www.")

    nombres = {
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
        "m.youtube.com": "YouTube",
        "music.youtube.com": "YouTube",
        "x.com": "X",
        "mobile.x.com": "X",
        "twitter.com": "X/Twitter",
        "mobile.twitter.com": "X/Twitter",
        "facebook.com": "Facebook",
        "m.facebook.com": "Facebook",
        "mobile.facebook.com": "Facebook",
        "fb.watch": "Facebook",
        "instagram.com": "Instagram",
        "tiktok.com": "TikTok",
        "vimeo.com": "Vimeo",
        "reddit.com": "Reddit",
    }

    if host in nombres:
        return nombres[host]

    for dominio, nombre in nombres.items():
        if host.endswith(f".{dominio}"):
            return nombre

    return host or "El sitio"


def extraer_id_facebook(enlace: str) -> str | None:
    """Extrae el identificador numérico de un Reel o video de Facebook."""
    partes = urlsplit(enlace)
    ruta = partes.path

    patrones = (
        r"/(?:reel|reels)/(\d+)",
        r"/videos/(\d+)",
        r"/watch/(?:live/)?(?:\?v=)?(\d+)",
    )

    for patron in patrones:
        coincidencia = re.search(patron, ruta, flags=re.IGNORECASE)
        if coincidencia:
            return coincidencia.group(1)

    consulta = parse_qs(partes.query)
    valor = (consulta.get("v") or consulta.get("video_id") or [None])[0]

    if valor and str(valor).isdigit():
        return str(valor)

    return None


def limpiar_enlace(enlace: str) -> str:
    """Normaliza enlaces y elimina rastreadores de Facebook."""
    enlace = enlace.strip().strip('\"\'<>')

    if not enlace:
        return enlace

    partes = urlsplit(enlace)
    host = (partes.hostname or "").lower()

    if not es_enlace_facebook(enlace):
        return enlace

    # fb.watch necesita conservar su ruta corta para poder redirigir.
    if host.endswith("fb.watch"):
        return urlunsplit(("https", host, partes.path, "", ""))

    video_id = extraer_id_facebook(enlace)

    if re.search(r"/(?:reel|reels)/", partes.path, flags=re.IGNORECASE) and video_id:
        return f"https://www.facebook.com/reel/{video_id}/"

    if video_id:
        return f"https://www.facebook.com/watch/?v={video_id}"

    ruta = re.sub(r"/+", "/", partes.path)
    return urlunsplit(("https", "www.facebook.com", ruta, "", ""))


def candidatos_de_enlace(enlace: str) -> list[str]:
    """Genera variantes seguras para intentar la extracción."""
    limpio = limpiar_enlace(enlace)
    candidatos = [limpio]

    if es_enlace_facebook(limpio):
        video_id = extraer_id_facebook(limpio)

        if video_id:
            candidatos.extend(
                [
                    f"https://www.facebook.com/reel/{video_id}/",
                    f"https://www.facebook.com/watch/?v={video_id}",
                    f"https://m.facebook.com/watch/?v={video_id}",
                ]
            )

    # Elimina duplicados sin alterar el orden.
    return list(dict.fromkeys(candidatos))


def ocultar_datos_sensibles(mensaje: str) -> str:
    """Oculta credenciales de proxy antes de mostrar detalles técnicos."""
    proxy_url, _ = obtener_configuracion_red()

    if proxy_url:
        mensaje = mensaje.replace(proxy_url, "[PROXY OCULTO]")

    mensaje = re.sub(
        r"(https?://)([^\s/@:]+):([^\s/@]+)@",
        r"\1***:***@",
        mensaje,
    )
    return mensaje



def obtener_configuracion_red() -> tuple[str | None, str]:
    """
    Obtiene el proxy privado y el país preferido.

    Prioridad:
    1. Variables de entorno OFFSAVE_PROXY_URL / OFFSAVE_COUNTRY_CODE.
    2. .streamlit/secrets.toml, sección [network].
    """
    proxy_url = os.getenv("OFFSAVE_PROXY_URL", "").strip()
    country_code = os.getenv("OFFSAVE_COUNTRY_CODE", "MX").strip().upper()

    try:
        network = st.secrets.get("network", {})
        proxy_url = str(
            network.get("proxy_url", proxy_url)
        ).strip()
        country_code = str(
            network.get("country_code", country_code)
        ).strip().upper()
    except Exception:
        # Streamlit puede lanzar una excepción cuando no existe secrets.toml.
        pass

    if len(country_code) != 2 or not country_code.isalpha():
        country_code = "MX"

    return proxy_url or None, country_code


def mostrar_error_yt_dlp(
    error: Exception,
    accion: str,
    enlace: str | None = None,
) -> None:
    """Muestra errores de yt-dlp sin exponer credenciales privadas."""
    mensaje = ocultar_datos_sensibles(str(error))
    mensaje_minusculas = mensaje.lower()

    if "ffmpeg is not installed" in mensaje_minusculas or (
        "ffmpeg" in mensaje_minusculas
        and "not found" in mensaje_minusculas
    ):
        st.error(
            "FFmpeg no está instalado en el servidor. Por eso OFFSAVE "
            "no puede recortar, convertir a MP3 ni unir video y audio."
        )
        st.info(
            "En Streamlit Community Cloud, el archivo packages.txt debe "
            "estar en la raíz del repositorio y contener una sola línea: "
            "ffmpeg. Después hay que reiniciar o volver a desplegar la app."
        )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1200:], language=None)

        return

    if "ffmpeg exited with code" in mensaje_minusculas:
        st.error(
            "FFmpeg sí está instalado, pero falló al procesar el archivo."
        )
        st.info(
            "OFFSAVE ya no intenta recortar directamente desde la URL del "
            "sitio: primero descarga el archivo completo y después lo "
            "recorta localmente. Si este mensaje persiste, abre el detalle "
            "técnico para identificar si falló la unión o la conversión."
        )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1600:], language=None)

        return

    es_error_facebook = bool(enlace and es_enlace_facebook(enlace)) and any(
        pista in mensaje_minusculas
        for pista in (
            "cannot parse data",
            "no video formats found",
            "login required",
            "requested content is not available",
        )
    )

    if "impersonate target" in mensaje_minusculas:
        st.error(
            "OFFSAVE no pudo activar la compatibilidad de navegador "
            "necesaria para Facebook."
        )
        st.info(
            "Vuelve a desplegar la aplicación para que Streamlit instale "
            "yt-dlp con curl-cffi desde requirements.txt."
        )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1200:], language=None)

        return

    if es_error_facebook:
        st.error(
            "Facebook no entregó los datos del video a OFFSAVE. "
            "La aplicación ya probó el enlace limpio y varias rutas "
            "compatibles, pero Facebook bloqueó o cambió la respuesta."
        )
        st.info(
            "Comprueba que la publicación sea pública y que pueda abrirse "
            "en una ventana privada. Si Facebook exige iniciar sesión, "
            "OFFSAVE necesitará un cookies.txt válido de tu propia cuenta."
        )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1200:], language=None)

        return

    es_error_403 = (
        "http error 403" in mensaje_minusculas
        or "403: forbidden" in mensaje_minusculas
    )

    if es_error_403 and enlace and es_enlace_facebook(enlace):
        st.error(
            "Facebook permitió analizar el video, pero bloqueó la descarga "
            "del archivo desde la IP del servidor."
        )
        st.info(
            "OFFSAVE ya probó formatos progresivos, bloques pequeños y "
            "variantes del enlace. Si continúa, el bloqueo pertenece a la "
            "CDN de Facebook y no a FFmpeg. Prueba otro video público; para "
            "ese enlace puede ser necesario ejecutar OFFSAVE localmente o "
            "usar una salida de red residencial autorizada."
        )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1600:], language=None)

        return

    if es_error_403:
        sitio = nombre_sitio(enlace)
        st.error(
            f"{sitio} rechazó la descarga desde el servidor con un error 403."
        )
        st.info(
            "OFFSAVE conservó el extractor universal de yt-dlp y probó "
            "formatos alternativos. Revisa que el contenido sea público. "
            "Algunos sitios, entre ellos YouTube, X/Twitter e Instagram, "
            "pueden exigir cookies de una sesión válida o bloquear IP de "
            "centros de datos."
        )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1600:], language=None)

        return

    es_bloqueo_geografico = any(
        pista in mensaje_minusculas
        for pista in (
            "not made this video available in your country",
            "not available in your country",
            "geo-restricted",
            "geo restricted",
            "geographic restriction",
        )
    )

    if es_bloqueo_geografico:
        proxy_url, country_code = obtener_configuracion_red()

        st.error(
            "El contenido está permitido en México, pero la IP del "
            "servidor que ejecuta OFFSAVE está siendo detectada en "
            "otro país."
        )

        if proxy_url:
            st.warning(
                "OFFSAVE encontró un proxy configurado, pero el sitio "
                "sigue rechazando su ubicación. Verifica que el proxy "
                f"tenga una IP activa de {country_code} y que permita "
                "tráfico HTTPS."
            )
        else:
            st.info(
                "Para una aplicación publicada en Streamlit Cloud "
                "necesitas configurar un proxy privado con salida en "
                f"{country_code}. Si ejecutas la aplicación localmente "
                "desde México, normalmente no necesitas proxy."
            )

            with st.expander("Cómo configurar el proxy privado"):
                st.markdown(
                    "En Streamlit Community Cloud abre **App settings → "
                    "Secrets** y agrega:"
                )
                st.code(
                    '[network]\n'
                    'proxy_url = "http://USUARIO:CONTRASEÑA@HOST:PUERTO"\n'
                    f'country_code = "{country_code}"',
                    language="toml",
                )
                st.caption(
                    "No escribas el proxy directamente en app.py ni lo "
                    "subas a GitHub."
                )

        with st.expander("Detalle técnico"):
            st.code(mensaje[-1200:], language=None)

        return

    st.error(f"No fue posible {accion} el contenido.")
    st.code(mensaje[-1200:], language=None)
    st.info(
        "Revisa que el enlace sea público, que yt-dlp esté actualizado, "
        "que FFmpeg esté instalado y que cookies.txt siga siendo válido."
    )


def opciones_comunes(enlace: str | None = None) -> dict:
    """Configuración común de yt-dlp."""
    proxy_url, country_code = obtener_configuracion_red()

    opciones = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,

        # Fuerza IPv4, pero NO cambia el país de la IP pública.
        "source_address": "0.0.0.0",

        "retries": 10,
        "fragment_retries": 10,
        "extractor_retries": 5,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,

        # Solicita a yt-dlp usar México cuando el sitio admite XFF.
        # En YouTube un bloqueo real normalmente exige un proxy.
        "geo_bypass": True,
        "geo_bypass_country": country_code,

        "http_headers": {
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.7",
        },
    }

    if enlace and es_enlace_facebook(enlace):
        # Facebook usa detección de huella TLS. curl_cffi, instalado desde
        # requirements.txt, permite que yt-dlp imite una solicitud de Chrome.
        # No se fija aquí un User-Agent global porque debe coincidir con la
        # huella durante la extracción. El extractor actual asigna a cada
        # formato el User-Agent especial que requiere la CDN de Facebook.
        opciones["impersonate"] = ImpersonateTarget.from_str("chrome")

        # Las CDN de Facebook pueden devolver 403 con descargas paralelas o
        # bloques grandes, especialmente desde IP de centros de datos.
        opciones["concurrent_fragment_downloads"] = 1
        opciones["http_chunk_size"] = 10 * 1024 * 1024
        opciones["http_headers"].update(
            {
                "Referer": "https://www.facebook.com/",
                "Origin": "https://www.facebook.com",
            }
        )

    # El proxy se conserva en Secrets o variables de entorno;
    # nunca se muestra en pantalla ni se escribe en los errores.
    if proxy_url:
        opciones["proxy"] = proxy_url
        opciones["geo_verification_proxy"] = proxy_url

    cookie_path = Path("cookies.txt")

    if cookie_path.is_file():
        opciones["cookiefile"] = str(cookie_path)

    return opciones


def analizar_video(enlace: str) -> dict:
    """Obtiene información sin descargar y prueba variantes de Facebook."""
    ultimo_error: Exception | None = None

    for candidato in candidatos_de_enlace(enlace):
        opciones = opciones_comunes(candidato)
        opciones["skip_download"] = True

        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                informacion = ydl.extract_info(candidato, download=False)
                resultado = ydl.sanitize_info(informacion)
                resultado["_offsave_url"] = candidato
                return resultado
        except yt_dlp.utils.YoutubeDLError as error:
            ultimo_error = error

    if ultimo_error:
        raise ultimo_error

    raise RuntimeError("No fue posible generar una variante válida del enlace.")


def selector_mp4(calidad: str, facebook: bool = False) -> str:
    """Construye un selector de calidad para MP4.

    En Facebook priorizamos formatos progresivos (video + audio en un solo
    archivo). Los formatos DASH separados son más propensos a devolver 403
    desde las CDN de Facebook cuando la app corre en un centro de datos.
    """
    alturas = {
        "Máxima disponible": None,
        "2160p (4K)": 2160,
        "1440p": 1440,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
    }

    altura = alturas[calidad]

    if facebook:
        if altura is None:
            return "b[ext=mp4]/b/best"
        return (
            f"b[height<={altura}][ext=mp4]/"
            f"b[height<={altura}]/"
            f"best[height<={altura}]/best"
        )

    if altura is None:
        return (
            "bv[ext=mp4]+ba[ext=m4a]/"
            "b[ext=mp4]/"
            "bv+ba/b"
        )

    return (
        f"bv[height<={altura}][ext=mp4]+ba[ext=m4a]/"
        f"b[height<={altura}][ext=mp4]/"
        f"bv[height<={altura}]+ba/"
        f"b[height<={altura}]/best"
    )


def encontrar_archivo(directorio: Path, extension: str) -> Path:
    """Localiza el archivo final creado por yt-dlp/FFmpeg."""
    archivos = list(directorio.glob(f"*.{extension}"))

    if not archivos:
        archivos = [
            archivo
            for archivo in directorio.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower()
            not in {
                ".part",
                ".ytdl",
                ".temp",
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            }
        ]

    if not archivos:
        raise FileNotFoundError(
            "La descarga terminó, pero no se encontró el archivo final."
        )

    return max(archivos, key=lambda archivo: archivo.stat().st_mtime)



def ejecutar_ffmpeg(comando: list[str], descripcion: str) -> None:
    """Ejecuta FFmpeg y conserva el detalle útil cuando falla."""
    try:
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=1800,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError(
            f"FFmpeg tardó demasiado al {descripcion}. "
            "Prueba un fragmento más corto o una calidad menor."
        ) from error

    if resultado.returncode != 0:
        detalle = (resultado.stderr or resultado.stdout or "").strip()
        if len(detalle) > 2400:
            detalle = detalle[-2400:]

        raise RuntimeError(
            f"FFmpeg no pudo {descripcion} "
            f"(código {resultado.returncode}).\n{detalle}"
        )


def recortar_archivo_local(
    archivo_entrada: Path,
    archivo_salida: Path,
    formato_salida: str,
    inicio: int,
    final: int,
    bitrate: str,
) -> None:
    """
    Recorta un archivo ya descargado.

    No usamos download_ranges de yt-dlp porque ese modo obliga a FFmpeg a
    abrir directamente la URL temporal del sitio. En Facebook esas URLs pueden
    rechazar a FFmpeg aunque yt-dlp sí haya podido descargar el archivo.
    """
    duracion = final - inicio

    if duracion <= 0:
        raise ValueError("El final del fragmento debe ser mayor que el inicio.")

    base = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-ss",
        str(inicio),
        "-i",
        str(archivo_entrada),
        "-t",
        str(duracion),
    ]

    if formato_salida == "MP4":
        comando = base + [
            "-map",
            "0:v:0?",
            "-map",
            "0:a:0?",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(archivo_salida),
        ]
        ejecutar_ffmpeg(comando, "recortar el video")
    else:
        bitrate_numero = bitrate.replace(" kbps", "")
        comando = base + [
            "-vn",
            "-c:a",
            "libmp3lame",
            "-b:a",
            f"{bitrate_numero}k",
            str(archivo_salida),
        ]
        ejecutar_ffmpeg(comando, "recortar el audio")


def _es_error_403(error: Exception) -> bool:
    mensaje = str(error).lower()
    return "http error 403" in mensaje or "403: forbidden" in mensaje


def _es_error_de_formato(error: Exception) -> bool:
    """Detecta fallos que pueden resolverse probando otro formato."""
    mensaje = str(error).lower()
    return any(
        pista in mensaje
        for pista in (
            "requested format is not available",
            "requested format not available",
            "no suitable formats",
            "format selection failed",
        )
    )


def _limpiar_intento(directorio: Path) -> None:
    """Elimina restos de un intento fallido antes de probar otra estrategia."""
    for archivo in directorio.iterdir():
        if archivo.is_file():
            try:
                archivo.unlink()
            except OSError:
                pass
        elif archivo.is_dir():
            shutil.rmtree(archivo, ignore_errors=True)


def _estrategias_descarga(
    enlace: str,
    formato_salida: str,
    calidad: str,
) -> list[dict]:
    """Devuelve estrategias universales y ajustes especiales por sitio."""
    facebook = es_enlace_facebook(enlace)

    if formato_salida == "MP4":
        if facebook:
            return [
                {
                    "nombre": "Facebook progresivo",
                    "format": selector_mp4(calidad, facebook=True),
                },
                {
                    "nombre": "Facebook MP4 combinado",
                    "format": "b[ext=mp4]/best[ext=mp4]/best",
                },
                {
                    "nombre": "Facebook respaldo DASH",
                    "format": selector_mp4(calidad, facebook=False),
                },
            ]

        # La ruta normal sigue siendo universal: YouTube, X/Twitter,
        # Instagram, TikTok, Vimeo y los demás extractores de yt-dlp.
        return [
            {
                "nombre": "Mejor calidad compatible",
                "format": selector_mp4(calidad, facebook=False),
            },
            {
                "nombre": "MP4 progresivo",
                "format": "b[ext=mp4]/best[ext=mp4]/best",
            },
            {
                "nombre": "Formato universal de respaldo",
                "format": "bv*+ba/b",
            },
        ]

    if facebook:
        return [
            {
                "nombre": "Audio directo",
                "format": "bestaudio[ext=m4a]/bestaudio/best",
            },
            {
                "nombre": "Audio desde MP4 progresivo",
                "format": "b[ext=mp4]/best[ext=mp4]/best",
            },
        ]

    return [
        {"nombre": "Mejor audio", "format": "bestaudio/best"},
        {
            "nombre": "Audio desde formato combinado",
            "format": "b[ext=mp4]/best",
        },
    ]


def descargar_archivo(
    enlace: str,
    formato_salida: str,
    calidad: str,
    bitrate: str,
    inicio: int | None,
    final: int | None,
    titulo: str,
) -> tuple[bytes, str, str]:
    """Descarga desde cualquier extractor compatible con yt-dlp.

    La ruta general conserva soporte para YouTube, X/Twitter y los demás
    sitios. Facebook recibe reintentos adicionales sin sustituir el flujo
    universal del descargador.
    """

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise RuntimeError(
            "FFmpeg/FFprobe no está instalado. En Streamlit Community "
            "Cloud, coloca packages.txt en la raíz del repositorio con "
            "la línea: ffmpeg, y vuelve a desplegar la aplicación."
        )

    with tempfile.TemporaryDirectory() as carpeta_temporal:
        directorio = Path(carpeta_temporal)
        barra = st.progress(0)
        estado = st.empty()
        ultimo_error: Exception | None = None

        enlaces = candidatos_de_enlace(enlace) if es_enlace_facebook(enlace) else [enlace]

        def progreso(datos: dict) -> None:
            if datos.get("status") == "downloading":
                descargado = datos.get("downloaded_bytes", 0)
                total = datos.get("total_bytes") or datos.get("total_bytes_estimate")

                if total:
                    porcentaje = min(descargado / total, 1.0)
                    barra.progress(porcentaje)
                    estado.caption(f"Descargando: {porcentaje * 100:.1f}%")
                else:
                    estado.caption("Descargando contenido...")

            elif datos.get("status") == "finished":
                barra.progress(1.0)
                estado.caption("Descarga terminada. Procesando con FFmpeg...")

        for candidato in enlaces:
            for estrategia in _estrategias_descarga(candidato, formato_salida, calidad):
                _limpiar_intento(directorio)
                barra.progress(0)
                estado.caption(f"Probando: {estrategia['nombre']}...")

                opciones = opciones_comunes(candidato)
                opciones.update(
                    {
                        "outtmpl": str(directorio / "descarga.%(ext)s"),
                        "overwrites": True,
                        "format": estrategia["format"],
                        "progress_hooks": [progreso],
                    }
                )

                if formato_salida == "MP4":
                    extension = "mp4"
                    mime = "video/mp4"
                    opciones.update(
                        {
                            "merge_output_format": "mp4",
                            "postprocessors": [
                                {
                                    "key": "FFmpegVideoConvertor",
                                    "preferedformat": "mp4",
                                }
                            ],
                        }
                    )
                else:
                    extension = "mp3"
                    mime = "audio/mpeg"
                    bitrate_numero = bitrate.replace(" kbps", "")
                    opciones.update(
                        {
                            "postprocessors": [
                                {
                                    "key": "FFmpegExtractAudio",
                                    "preferredcodec": "mp3",
                                    "preferredquality": bitrate_numero,
                                },
                                {
                                    "key": "FFmpegMetadata",
                                    "add_metadata": True,
                                },
                            ],
                        }
                    )

                try:
                    with yt_dlp.YoutubeDL(opciones) as ydl:
                        ydl.download([candidato])

                    archivo_final = encontrar_archivo(directorio, extension)
                    break
                except yt_dlp.utils.YoutubeDLError as error:
                    ultimo_error = error

                    # Un 403 o un formato no disponible puede afectar
                    # solo a una estrategia. Se prueba la siguiente en
                    # cualquier sitio, no únicamente en Facebook.
                    if _es_error_403(error) or _es_error_de_formato(error):
                        continue

                    raise
            else:
                continue
            break
        else:
            if ultimo_error:
                raise ultimo_error
            raise RuntimeError("No fue posible completar ninguna estrategia de descarga.")

        if inicio is not None and final is not None:
            estado.caption("Descarga terminada. Recortando el archivo localmente...")
            archivo_recortado = directorio / f"recorte.{extension}"
            recortar_archivo_local(
                archivo_entrada=archivo_final,
                archivo_salida=archivo_recortado,
                formato_salida=formato_salida,
                inicio=inicio,
                final=final,
                bitrate=bitrate,
            )
            archivo_final = archivo_recortado

        tamaño_mb = archivo_final.stat().st_size / (1024 * 1024)

        if tamaño_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"El archivo pesa {tamaño_mb:.1f} MB y supera el límite "
                f"de {MAX_FILE_SIZE_MB} MB configurado para esta aplicación."
            )

        contenido = archivo_final.read_bytes()
        titulo_limpio = nombre_seguro(titulo)

        if inicio is not None and final is not None:
            nombre_final = (
                f"{titulo_limpio}_"
                f"{segundos_a_tiempo(inicio).replace(':', '-')} _"
                f"{segundos_a_tiempo(final).replace(':', '-')}"
                f".{extension}"
            ).replace("_ ", "_")
        else:
            nombre_final = f"{titulo_limpio}.{extension}"

        estado.empty()
        barra.empty()

        return contenido, nombre_final, mime


# =========================================================
# ESTADO DE STREAMLIT
# =========================================================

if "informacion_video" not in st.session_state:
    st.session_state.informacion_video = None

if "url_analizada" not in st.session_state:
    st.session_state.url_analizada = ""

if "archivo_preparado" not in st.session_state:
    st.session_state.archivo_preparado = None

if "enlace_descarga" not in st.session_state:
    st.session_state.enlace_descarga = ""


# =========================================================
# FORMULARIO PRINCIPAL
# =========================================================

with st.form("formulario_principal", clear_on_submit=False):
    columna_url, columna_off = st.columns(
        [5.2, 1],
        vertical_alignment="bottom",
    )

    with columna_url:
        url = st.text_input(
            "Dirección del contenido",
            placeholder="Paste the direct URL to online content...",
            label_visibility="collapsed",
        )

    with columna_off:
        analizar = st.form_submit_button(
            "OFF",
            use_container_width=True,
        )


if analizar:
    if not url.strip():
        st.warning("Pega primero el enlace del contenido.")

    elif not url.startswith(("https://", "http://")):
        st.error("El enlace debe comenzar con http:// o https://.")

    else:
        enlace_limpio = limpiar_enlace(url)

        try:
            with st.spinner("Offliberando el enlace..."):
                informacion = analizar_video(enlace_limpio)

            st.session_state.informacion_video = informacion
            st.session_state.url_analizada = enlace_limpio
            st.session_state.enlace_descarga = informacion.get(
                "_offsave_url",
                enlace_limpio,
            )
            st.session_state.archivo_preparado = None

        except yt_dlp.utils.YoutubeDLError as error:
            mostrar_error_yt_dlp(
                error,
                accion="analizar",
                enlace=enlace_limpio,
            )

        except Exception as error:
            st.error(f"Error técnico: {error}")


# =========================================================
# OPCIONES DE DESCARGA
# =========================================================

informacion = st.session_state.informacion_video

if informacion and st.session_state.url_analizada == limpiar_enlace(url):
    titulo = informacion.get("title") or "Video"
    titulo_html = html.escape(str(titulo))
    duracion = informacion.get("duration")
    thumbnail = informacion.get("thumbnail")
    autor = (
        informacion.get("uploader")
        or informacion.get("channel")
        or "Autor desconocido"
    )
    autor_html = html.escape(str(autor))

    st.divider()

    if thumbnail:
        st.image(thumbnail, use_container_width=True)

    st.markdown(
        f"""
        <div class="video-title">{titulo_html}</div>
        <div class="video-author">{autor_html}</div>
        """,
        unsafe_allow_html=True,
    )

    columna_1, columna_2 = st.columns(2)

    with columna_1:
        st.markdown(
            f"""
            <div class="retro-stat-card">
                <div class="retro-stat-label">Duración</div>
                <div class="retro-stat-value">
                    {segundos_a_tiempo(duracion)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with columna_2:
        tipo_contenido = (
            informacion.get("extractor_key")
            or "Contenido web"
        )
        tipo_contenido_html = html.escape(str(tipo_contenido))

        st.markdown(
            f"""
            <div class="retro-stat-card">
                <div class="retro-stat-label">Tipo</div>
                <div class="retro-stat-value">
                    {tipo_contenido_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="retro-section-title">Elige tu descarga</div>
        <div class="retro-subtitle">
            Selecciona formato, calidad y duración.
        </div>
        """,
        unsafe_allow_html=True,
    )

    formato_salida = st.radio(
        "Formato de descarga:",
        ["MP4", "MP3"],
        horizontal=True,
    )

    if formato_salida == "MP4":
        calidad = st.selectbox(
            "Calidad del video:",
            [
                "Máxima disponible",
                "2160p (4K)",
                "1440p",
                "1080p",
                "720p",
                "480p",
                "360p",
            ],
            index=4,
        )
        bitrate = "192 kbps"

    else:
        bitrate = st.selectbox(
            "Calidad del audio:",
            [
                "320 kbps",
                "256 kbps",
                "192 kbps",
                "128 kbps",
            ],
            index=2,
        )
        calidad = "Solo audio"

    tipo_descarga = st.radio(
        "¿Qué parte deseas descargar?",
        [
            "Contenido completo",
            "Seleccionar fragmento",
        ],
    )

    inicio_segundos = None
    final_segundos = None
    tiempos_validos = True

    if tipo_descarga == "Seleccionar fragmento":
        st.info(
            "Escribe el punto inicial y final. "
            "Ejemplo: 01:30 hasta 03:45."
        )

        columna_inicio, columna_final = st.columns(2)

        with columna_inicio:
            tiempo_inicio = st.text_input(
                "Comenzar en:",
                value="00:00",
                placeholder="MM:SS",
            )

        with columna_final:
            tiempo_final = st.text_input(
                "Terminar en:",
                value=(
                    segundos_a_tiempo(duracion)
                    if duracion
                    else "01:00"
                ),
                placeholder="MM:SS",
            )

        try:
            inicio_segundos = tiempo_a_segundos(tiempo_inicio)
            final_segundos = tiempo_a_segundos(tiempo_final)

            if final_segundos <= inicio_segundos:
                st.error(
                    "El tiempo final debe ser mayor que el inicial."
                )
                tiempos_validos = False

            elif duracion and final_segundos > int(duracion):
                st.error(
                    "El tiempo final supera la duración del contenido."
                )
                tiempos_validos = False

            else:
                duracion_fragmento = (
                    final_segundos - inicio_segundos
                )

                st.success(
                    "Fragmento seleccionado: "
                    f"{segundos_a_tiempo(duracion_fragmento)}"
                )

        except ValueError as error:
            st.error(str(error))
            tiempos_validos = False

    preparar = st.button(
        f"PREPARAR DESCARGA {formato_salida}",
        type="primary",
        use_container_width=True,
        disabled=not tiempos_validos,
    )

    if preparar:
        try:
            st.session_state.archivo_preparado = None

            with st.spinner(
                "Descargando y procesando el archivo..."
            ):
                datos, nombre, mime = descargar_archivo(
                    enlace=(
                        st.session_state.enlace_descarga
                        or limpiar_enlace(url)
                    ),
                    formato_salida=formato_salida,
                    calidad=calidad,
                    bitrate=bitrate,
                    inicio=inicio_segundos,
                    final=final_segundos,
                    titulo=titulo,
                )

            st.session_state.archivo_preparado = {
                "datos": datos,
                "nombre": nombre,
                "mime": mime,
                "formato": formato_salida,
            }

        except yt_dlp.utils.YoutubeDLError as error:
            mostrar_error_yt_dlp(
                error,
                accion="descargar",
                enlace=st.session_state.enlace_descarga or limpiar_enlace(url),
            )

        except Exception as error:
            mensaje = str(error)
            if "FFmpeg/FFprobe no está instalado" in mensaje:
                st.error(mensaje)
                st.info(
                    "No basta con agregar ffmpeg a requirements.txt: "
                    "packages.txt debe estar en la raíz de GitHub."
                )
            else:
                st.error(f"Error técnico: {mensaje}")

    archivo = st.session_state.archivo_preparado

    if archivo:
        st.success(
            f"Archivo {archivo['formato']} preparado correctamente."
        )

        tamaño_mb = len(archivo["datos"]) / (1024 * 1024)
        st.caption(f"Tamaño aproximado: {tamaño_mb:.2f} MB")

        if archivo["formato"] == "MP4":
            st.video(archivo["datos"])
            etiqueta = "DESCARGAR ARCHIVO DE VIDEO"
        else:
            st.audio(archivo["datos"])
            etiqueta = "DESCARGAR ARCHIVO DE AUDIO"

        st.download_button(
            label=etiqueta,
            data=archivo["datos"],
            file_name=archivo["nombre"],
            mime=archivo["mime"],
            type="primary",
            use_container_width=True,
            on_click="ignore",
        )


st.markdown(
    """
    <div class="retro-footer">
        Descarga únicamente contenido propio, de dominio público
        o para el que tengas autorización.<br>
        OFFSAVE procesa los archivos de forma temporal.
    </div>
    """,
    unsafe_allow_html=True,
)
