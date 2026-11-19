# Pruebas

## Ejecución

```bash
python -m pytest
```

Cobertura:

```bash
python -m pytest \
  --cov=musetop/core \
  --cov=musetop/app \
  --cov-report=term-missing \
  --cov-fail-under=50
```

La suite usa `QT_QPA_PLATFORM=offscreen`, definido en `tests/conftest.py`. No
requiere servidor gráfico.

## Grupos de pruebas

| Archivo | Cobertura |
| --- | --- |
| `test_architecture.py` | imports de red prohibidos, core sin UI, emojis |
| `test_ui_strings.py` | textos reales de la ventana sin emojis |
| `test_paths.py` | APPDATA, XDG, archivos de configuración |
| `test_config.py` | JSON válido, inválido, escritura atómica, reset |
| `test_logging.py` | archivo rotativo e idempotencia |
| `test_formats.py` | extensiones, carpetas no recursivas, 500 archivos |
| `test_tags_reader.py` | etiquetas y duración en los seis formatos |
| `test_playlist.py` | alta, deduplicación, eliminación y movimiento |
| `test_audio_engine.py` | libmpv, transporte, modos y seek |
| `test_ui_widgets.py` | modelo, barra, formato e iconos |
| `test_main_window.py` | carga, doble clic, borrado, DnD y 500 archivos |
| `test_theme.py` | contraste AA, sistema, persistencia y velocidad |

## Archivos de audio de prueba

No se versionan archivos de audio. `tests/audio_factory.py` genera tonos con
ffmpeg en directorios temporales. Si ffmpeg no está disponible, los módulos de
integración se omiten; las pruebas unitarias siguen ejecutándose. Del mismo
modo, la reproducción real se omite si libmpv no puede cargarse.

## Guardia offline

`test_package_does_not_import_network_libraries` analiza el AST de todos los
archivos de `musetop/` y falla ante cualquier import de `requests`, `httpx`,
`urllib`, `socket`, `http` y equivalentes, además de módulos Qt de red o web.
