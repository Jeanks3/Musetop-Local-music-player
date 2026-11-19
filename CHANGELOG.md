# Changelog

Todas las fechas usan el formato AAAA-MM-DD.

## [0.1.0a1] - En desarrollo

### Hito 1 - Esqueleto y cimientos

- Estructura de paquetes `app`, `core`, `ui`, `resources` y pruebas.
- Rutas multiplataforma basadas en `pathlib` (APPDATA en Windows, XDG en Linux).
- Preferencias JSON con validacion, escritura atomica y restablecimiento.
- Logging rotativo en el directorio de datos del usuario.
- Prueba de arquitectura que prohibe imports de red y caracteres emoji.

### Hito 2 - Motor de audio

- Motor libmpv independiente de la vista, con carga diferida de la biblioteca.
- Reproduccion, pausa, parada, siguiente, anterior, seek y volumen 0-100.
- Modos secuencial y repetir todo, con avance automatico al terminar una pista.
- Pruebas de integracion con archivos MP3, FLAC, WAV, OGG, OPUS y M4A
  generados con ffmpeg.

### Hito 3 - Carga y lista de reproduccion

- Dialogos del sistema para abrir archivos y carpetas, ademas de arrastrar y
  soltar sobre la ventana o la lista.
- Escaneo no recursivo de carpetas y rechazo explicado de formatos no admitidos.
- Metadatos con mutagen: titulo, artista, album y duracion, con respaldo para
  archivos sin etiquetas.
- Lista con numero, titulo, artista, album y duracion; doble clic para
  reproducir, seleccion multiple, eliminacion y reordenacion por arrastre.
- Barra inferior con metadatos, progreso, transporte y volumen.

### Hito 4 - Temas y accesibilidad visual

- Temas Claro, Oscuro y Seguir al sistema, con deteccion de cambios del sistema.
- Selector de color de acento aplicado a botones activos, progreso y seleccion.
- Paletas ajustadas para contraste WCAG 2.1 AA y pruebas de contraste.
- Persistencia JSON de tema y acento, y boton para restablecer la apariencia.
- Prueba en vivo que recorre los textos de la interfaz y rechaza emojis.
