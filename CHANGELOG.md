# Changelog

Todas las fechas usan el formato AAAA-MM-DD.

## [0.1.0a1] - En desarrollo

### Hito 1 - Esqueleto y cimientos

- Estructura de paquetes `app`, `core`, `ui`, `resources` y pruebas.
- Rutas multiplataforma basadas en `pathlib` (APPDATA en Windows, XDG en Linux).
- Preferencias JSON con validación, escritura atómica y restablecimiento.
- Logging rotativo en el directorio de datos del usuario.
- Prueba de arquitectura que prohíbe imports de red y caracteres emoji.

### Hito 2 - Motor de audio

- Motor libmpv independiente de la vista, con carga diferida de la biblioteca.
- Reproducción, pausa, parada, siguiente, anterior, seek y volumen 0-100.
- Modos secuencial y repetir todo, con avance automático al terminar una pista.
- Pruebas de integración con archivos MP3, FLAC, WAV, OGG, OPUS y M4A
  generados con ffmpeg.

### Hito 3 - Carga y lista de reproducción

- Diálogos del sistema para abrir archivos y carpetas, además de arrastrar y
  soltar sobre la ventana o la lista.
- Escaneo no recursivo de carpetas y rechazo explicado de formatos no admitidos.
- Metadatos con mutagen: título, artista, álbum y duración, con respaldo para
  archivos sin etiquetas.
- Lista con número, título, artista, álbum y duración; doble clic para
  reproducir, selección múltiple, eliminación y reordenación por arrastre.
- Barra inferior con metadatos, progreso, transporte y volumen.

### Hito 4 - Temas y accesibilidad visual

- Temas Claro, Oscuro y Seguir al sistema, con detección de cambios del sistema.
- Selector de color de acento aplicado a botones activos, progreso y selección.
- Paletas ajustadas para contraste WCAG 2.1 AA y pruebas de contraste.
- Persistencia JSON de tema y acento, y botón para restablecer la apariencia.
- Prueba en vivo que recorre los textos de la interfaz y rechaza emojis.

### Hito 5 - Empaquetado y documentación

- Especificación PyInstaller en modo onedir para Windows y Linux.
- Inclusión de iconos, recursos y libmpv empaquetada.
- Scripts de compilación y archivo `.desktop` para Linux.
- README con instalación, ejecución, pruebas y empaquetado en ambos sistemas.
- Documentación de arquitectura, pruebas y limitaciones de distribución.
