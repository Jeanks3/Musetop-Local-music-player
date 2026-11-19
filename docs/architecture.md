# Arquitectura

## Capas

- `musetop.app`: infraestructura sin dependencias de Qt. Incluye rutas
  multiplataforma, configuración JSON y logging rotativo.
- `musetop.core`: formato de archivos, lectura de etiquetas, modelo de lista y
  motor de audio libmpv. No importa `musetop.ui`; la prueba de arquitectura lo
  verifica.
- `musetop.ui`: presentación Qt. La ventana traduce intenciones del usuario en
  llamadas al motor y escucha sus señales. No contiene reglas de reproducción.

## Flujo de reproducción

1. La ventana escanea archivos con `core.formats.scan_paths`.
2. `core.tags_reader.read_track` obtiene título, artista, álbum y duración.
3. `core.playlist.Playlist` mantiene el orden y evita rutas duplicadas.
4. `core.audio_engine.AudioEngine` recibe solo rutas, reproduce con libmpv y
   emite señales de estado, posición, duración, pista y errores.
5. Los cambios de lista se sincronizan con `set_playlist(..., preserve_current=True)`
   para no cortar la pista actual.

`AudioEngine` carga libmpv de forma diferida. `core.mpv_loader` primero intenta
la biblioteca del sistema y luego `vendor/lib`. Esto mantiene el arranque rápido
y permite ejecutar pruebas con `ao=null` sin tocar el dispositivo de audio.

## Temas

- `ui.theme.colors` contiene la matemática de contraste WCAG y las paletas.
- `ui.theme.styles` genera el QSS a partir de los tokens.
- `ui.theme.manager.ThemeManager` resuelve Claro, Oscuro o Sistema, aplica la
  paleta de Qt y el QSS, y persiste tema y acento.
- Los iconos son SVG con `currentColor`; se renderizan por color y se vuelven a
  generar al cambiar de tema.
- El acento se ajusta si no alcanza 3:1 contra fondo y superficie. El texto
  sobre el acento se elige entre negro y blanco para superar 4.5:1.

## Reglas

1. Sin red: no se importan `requests`, `httpx`, `urllib`, `socket` ni módulos
   equivalentes en el paquete. La prueba `test_architecture.py` lo verifica.
2. Sin emojis: los iconos son SVG monocromáticos. Se revisan las fuentes y los
   textos reales de la ventana.
3. Rutas con `pathlib` y convenciones de cada sistema operativo.
4. Interfaz en español; identificadores y docstrings en inglés técnico.
5. Sin `print`: el logger configurado es el único canal de diagnóstico.
6. Sin lógica de reproducción en la UI: el motor es independiente de la vista.

## Datos de usuario

- Windows: `%APPDATA%\Musetop\settings.json`
- Linux: `$XDG_CONFIG_HOME/musetop/settings.json` o
  `~/.config/musetop/settings.json`
- Registros: subdirectorio `logs` dentro del directorio de datos.

Solo se persisten `theme` y `accent_color`.
