# Musetop

Reproductor de música de escritorio minimalista, offline y multiplataforma.
Esta pre-alpha reproduce MP3, FLAC, WAV, OGG Vorbis, OPUS y M4A/AAC, muestra los
metadatos con mutagen y ofrece personalización visual básica.

- Interfaz en español, código y docstrings en inglés técnico.
- Sin conexiones de red. La aplicación no importa librerías de red y libmpv se
  configura sin ytdl.
- Sin emojis. Todos los iconos son SVG monocromáticos que heredan el tema.
- Windows 10+ y Linux (Ubuntu 22.04+).

## Funciones incluidas

- Reproducción con play, pausa, parada, siguiente, anterior, seek y volumen.
- Progreso con posición y duración; modos secuencial y repetir todo.
- Apertura de archivos, apertura de carpeta sin recursión, y arrastrar y soltar.
- Lista con número, título, artista, álbum y duración.
- Doble clic para reproducir, selección múltiple, eliminación y reordenación.
- Temas Claro, Oscuro y Seguir al sistema.
- Color de acento para botones activos, progreso y selección.
- Preferencias visuales persistidas en JSON y restablecimiento a valores por
  defecto.
- Contraste WCAG 2.1 AA en textos y controles principales.

Fuera de alcance en esta versión: portadas, letras, edición de metadatos, tempo,
pitch, estadísticas, biblioteca por artistas o álbumes, fusión o división de
entidades. No se implementó ninguna de esas funciones.

## Requisitos

- Python 3.11 o superior.
- PySide6 6.6 o superior.
- libmpv (python-mpv 1.0.8 o superior).
- mutagen 1.47 o superior.
- Para pruebas de integración: ffmpeg, pytest y pytest-qt.
- Para empaquetar: PyInstaller 6 o superior.

El repositorio incluye una copia de libmpv en `vendor/lib` para Linux x86_64.
Si el sistema ya expone libmpv, la aplicación también puede usarla. En Windows
hay que colocar la DLL de libmpv en `vendor\lib` antes de ejecutar o empaquetar.

## Instalación y ejecución en Linux

Ubuntu 22.04 distribuye Python 3.10; instala Python 3.11 o superior con el
gestor de tu preferencia. En Ubuntu 24.04 o Debian recientes el paquete del
sistema puede ser `libmpv2`; en Ubuntu 22.04 suele ser `libmpv1`.

```bash
sudo apt update
sudo apt install libmpv1 ffmpeg
# En distribuciones nuevas: sudo apt install libmpv2 ffmpeg

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

python -m musetop
```

Si libmpv está instalada pero no se localiza, indica la ruta:

```bash
MUSETOP_LIBMPV=/usr/lib/x86_64-linux-gnu/libmpv.so.2 python -m musetop
```

## Instalación y ejecución en Windows 10+

1. Instala Python 3.11+ desde python.org y marca la opción de agregar Python al
   PATH.
2. Abre PowerShell en la raiz del repositorio.
3. Crea el entorno e instala dependencias:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

4. Copia la biblioteca de libmpv en `vendor\lib`. Los nombres admitidos son
   `mpv-2.dll` y `libmpv-2.dll`. Puedes obtenerla de una distribución de
   desarrollo de mpv para Windows.
5. Ejecuta:

```powershell
python -m musetop
```

`python-mpv` necesita esa DLL; sin ella la interfaz abre pero muestra un mensaje
claro al intentar reproducir.

## Pruebas

```bash
python -m pytest
```

Las pruebas de integración generan archivos temporales con ffmpeg y se omiten si
ffmpeg o libmpv no están disponibles. La cobertura se calcula sobre `core` y
`app`:

```bash
python -m pytest \
  --cov=musetop/core \
  --cov=musetop/app \
  --cov-report=term-missing \
  --cov-fail-under=50
```

Guardias automatizadas incluidas:

- `tests/test_architecture.py`: prohibe imports de `requests`, `httpx`,
  `urllib`, `socket`, `http` y módulos equivalentes en el paquete, y detecta
  caracteres emoji en las fuentes.
- `tests/test_ui_strings.py`: recorre los textos, tooltips y acciones de la
  ventana real y falla si aparece un emoji.
- `tests/test_theme.py`: comprueba contraste AA para paletas claras y oscuras,
  persistencia JSON y cambio de tema sin tocar la reproducción.

Resultados medidos en el entorno de desarrollo:

| Requisito | Medición |
| --- | --- |
| Arranque en frio | 0.53 s (fuente) / 0.70 s (empaquetado) |
| Cambio de tema | alrededor de 30 ms por cambio |
| Memoria en reposo | 80.5 MB RSS |
| Carpeta con 500 archivos | menos de 5 s, con prueba automatizada |
| Cobertura `core` + `app` | 83 % |

## Empaquetado

### Linux

```bash
python packaging/build.py
./dist/musetop/musetop
```

El script copia `musetop.desktop` junto al binario. Para integrarlo en el menu:

```bash
mkdir -p ~/.local/bin ~/.local/share/applications
mkdir -p ~/.local/share/icons/hicolor/scalable/apps
cp -r dist/musetop ~/.local/lib/musetop
ln -sf ~/.local/lib/musetop/musetop ~/.local/bin/musetop
cp packaging/musetop.desktop ~/.local/share/applications/musetop.desktop
cp packaging/musetop.svg ~/.local/share/icons/hicolor/scalable/apps/musetop.svg
```

También puedes usar `packaging/build-linux.sh`.

### Windows

```powershell
python packaging\build.py
```

El resultado es `dist\musetop\musetop.exe` junto a la carpeta `_internal`. Para
distribuirlo, comprime la carpeta completa `dist\musetop`. También existe
`packaging\build.bat`.

Windows no permite compilar un `.exe` desde Linux con PyInstaller; el
empaquetado debe ejecutarse en Windows. La misma especificación
`packaging/musetop.spec` sirve para ambos sistemas.

## Uso

- `Ctrl+O`: abrir archivos.
- `Ctrl+Shift+O`: abrir carpeta.
- `Supr`: quitar las pistas seleccionadas.
- Arrastra archivos o carpetas sobre la ventana para agregarlos.
- Arrastra filas dentro de la lista para reordenarlas.
- Doble clic en una fila para reproducirla.

## Datos de usuario

- Windows: `%APPDATA%\Musetop\settings.json`
- Linux: `$XDG_CONFIG_HOME/musetop/settings.json` o
  `~/.config/musetop/settings.json`
- Registros: subdirectorio `logs` del mismo directorio de datos.

El JSON solo guarda tema y color de acento. No se guarda ninguna ruta de audio ni
historial de reproducción.

## Estructura

```text
musetop/
  main.py            punto de entrada
  app/               configuración, rutas y logging
  core/              formatos, etiquetas, lista y motor libmpv
  ui/                ventana, widgets, temas, iconos SVG
  resources/         iconos de aplicación
tests/               pruebas unitarias, de integración y de arquitectura
docs/                arquitectura, pruebas y empaquetado
packaging/           especificación PyInstaller y archivos de escritorio
vendor/lib/          libmpv para desarrollo y empaquetado
```

## Licencia

MIT. Consulta `LICENSE`.
