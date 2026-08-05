# OFFSAVE

Aplicación Streamlit con estética retro para guardar contenido compatible con
los extractores de `yt-dlp`.

## Compatibilidad

OFFSAVE no está limitado a Facebook. Conserva el flujo universal de `yt-dlp`
para enlaces de sitios como:

- YouTube y YouTube Shorts.
- X/Twitter.
- Facebook y Facebook Reels.
- Instagram.
- TikTok.
- Vimeo, Reddit y muchos otros sitios compatibles con `yt-dlp`.

La compatibilidad real depende de que el contenido sea accesible, de los
cambios que haga cada plataforma y de si el sitio exige inicio de sesión.

## Funciones

- Descarga en MP4.
- Extracción en MP3.
- Selección de calidad.
- Descarga completa del contenido.
- Descarga universal mediante `yt-dlp`.
- Reintentos especiales para Facebook sin afectar los demás sitios.
- Cookies opcionales mediante `cookies.txt`.
- Conversión y unión de pistas con FFmpeg cuando es necesario.

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

## Estructura para Streamlit

Sube los archivos directamente a la raíz del repositorio:

```text
TU_REPOSITORIO/
├── app.py
├── requirements.txt
├── packages.txt
├── README.md
└── .streamlit/
    └── config.toml
```

`packages.txt` debe contener:

```text
ffmpeg
```

## Cómo funciona la descarga

1. `yt-dlp` analiza el enlace con su extractor correspondiente.
2. OFFSAVE prueba el formato solicitado y formatos de respaldo.
3. El archivo completo se guarda temporalmente en el servidor.
4. FFmpeg solo interviene si hay que unir pistas o convertir a MP3/MP4.
5. El archivo temporal se elimina al terminar la solicitud.

La selección de punto inicial y final fue retirada para reducir fallos y hacer
el flujo de descarga más estable entre plataformas.

## Ajustes especiales de Facebook

Solo cuando el dominio es Facebook, OFFSAVE:

- Limpia parámetros de rastreo.
- Prueba variantes de Reel y Watch.
- Usa compatibilidad de navegador mediante `curl-cffi`.
- Reduce la concurrencia y el tamaño de bloques.
- Prioriza formatos progresivos antes de probar DASH.

Estos ajustes son adicionales. No reemplazan ni eliminan el soporte universal
para YouTube, X/Twitter u otros sitios.

## Cookies

`cookies.txt` es opcional y funciona para cualquier sitio compatible con
`yt-dlp`, no solo Facebook. Debe estar en formato Netscape.

No lo subas a GitHub, no lo compartas y no incluyas una sesión ajena. El archivo
`.gitignore` ya evita que se publique accidentalmente.

## Errores 403

Un error 403 significa que la plataforma o su CDN rechazó la descarga desde la
IP del servidor. OFFSAVE prueba formatos alternativos antes de detenerse.

- En Facebook también prueba variantes del enlace y bloques pequeños.
- En YouTube, X/Twitter, Instagram y otros sitios mantiene el extractor normal
  y prueba formatos universales de respaldo.
- Algunos contenidos requieren cookies válidas.
- Algunas plataformas bloquean IP de centros de datos aunque el enlace sea
  público.

## Restricciones geográficas

`source_address = "0.0.0.0"` fuerza IPv4, pero no cambia el país de la IP.
Para usar una salida privada autorizada, configura Streamlit Secrets:

```toml
[network]
proxy_url = "http://USUARIO:CONTRASEÑA@HOST:PUERTO"
country_code = "MX"
```

También se admiten las variables de entorno:

```text
OFFSAVE_PROXY_URL=http://USUARIO:CONTRASEÑA@HOST:PUERTO
OFFSAVE_COUNTRY_CODE=MX
```

No publiques credenciales de proxy en el repositorio.
