# OFFSAVE

Aplicación Streamlit con estética retro inspirada en sitios de descarga de 2011.

## Funciones

- Descarga en MP4.
- Extracción en MP3.
- Selección de calidad.
- Descarga completa o por fragmento.
- Limpieza automática de enlaces de Facebook.
- Suplantación de navegador con `curl_cffi` para Facebook.
- Cookies opcionales mediante `cookies.txt`.
- Procesamiento con FFmpeg.

## Instalación

```bash
python -m pip install -r requirements.txt
```

En Streamlit Community Cloud, `packages.txt` instala FFmpeg automáticamente.
Para uso local, instala FFmpeg y FFprobe y agrégalos al PATH.

## Ejecutar

```bash
streamlit run app.py
```

## Cookies

`cookies.txt` es opcional. No lo subas a GitHub ni lo compartas.


## Videos restringidos por país

`source_address = "0.0.0.0"` únicamente fuerza IPv4. No convierte la IP del
servidor en una IP mexicana.

Cuando OFFSAVE está desplegado en un servidor de otro país, algunos videos que
sí están disponibles en México requieren un proxy privado con salida mexicana.

En Streamlit Community Cloud abre **App settings → Secrets** y agrega:

```toml
[network]
proxy_url = "http://USUARIO:CONTRASEÑA@HOST:PUERTO"
country_code = "MX"
```

También puedes usar variables de entorno:

```text
OFFSAVE_PROXY_URL=http://USUARIO:CONTRASEÑA@HOST:PUERTO
OFFSAVE_COUNTRY_CODE=MX
```

No publiques el proxy ni sus credenciales. El archivo
`.streamlit/secrets.toml.example` sirve como plantilla.


## Apariencia y contraste

El archivo `.streamlit/config.toml` fuerza el tema claro para evitar que
Streamlit herede letras blancas del modo oscuro. Las tarjetas de duración y
tipo usan HTML/CSS propio, por lo que mantienen texto negro en cualquier
navegador.

## Facebook y el error “Cannot parse data”

OFFSAVE limpia los parámetros de rastreo del enlace, prueba variantes de Reel y
Watch, y usa la suplantación de Chrome proporcionada por `curl_cffi`.

Facebook cambia su respuesta con frecuencia. Algunas publicaciones pueden seguir
requiriendo una sesión iniciada mediante un archivo `cookies.txt` válido, aunque
sean visibles en el navegador. El archivo debe estar en formato Netscape y nunca
debe publicarse ni compartirse.

El detalle técnico queda dentro de un desplegable para que no invada la interfaz.

## Importante al subir a GitHub

Sube **los archivos que están dentro de esta carpeta directamente a la raíz del repositorio**. La estructura correcta debe verse así:

```text
TU_REPOSITORIO/
├── app.py
├── requirements.txt
├── packages.txt
└── .streamlit/
    └── config.toml
```

No dejes `packages.txt` dentro de una carpeta secundaria como
`offsave-main/packages.txt`, porque Streamlit Community Cloud solo instala las
dependencias externas declaradas en el `packages.txt` ubicado en la raíz del
repositorio.

## Corrección del error “ffmpeg exited with code 8”

La aplicación no usa `download_ranges` para recortar directamente desde la URL
temporal del sitio. Ese método puede fallar en Facebook porque FFmpeg intenta
abrir por su cuenta una URL de CDN que requiere encabezados, cookies o una firma
temporal.

OFFSAVE ahora sigue este flujo:

1. `yt-dlp` descarga y prepara el archivo completo.
2. FFmpeg abre el archivo local ya descargado.
3. El fragmento se recorta localmente y se entrega en MP4 o MP3.

Esto consume más tráfico y espacio temporal, pero evita el fallo más común al
recortar publicaciones de Facebook.
