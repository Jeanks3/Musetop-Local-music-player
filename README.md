# Musetop

Reproductor de musica de escritorio minimalista, offline y multiplataforma.
Pre-alpha construida con Python 3.11+, PySide6, libmpv y mutagen.

## Estado

El proyecto se desarrolla por hitos. Consulta `CHANGELOG.md` para el detalle.

- Hito 1: esqueleto, configuracion, rutas, logging y pruebas de arquitectura.
- Hito 2: motor de audio.
- Hito 3: carga de archivos y lista de reproduccion.
- Hito 4: temas y color de acento.
- Hito 5: empaquetado.

## Desarrollo

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m musetop
```

La aplicacion no realiza ninguna conexion de red. libmpv se carga desde
`vendor/lib` cuando el sistema no expone la biblioteca compartida.

## Estructura

```text
musetop/        paquete principal
  app/          configuracion, rutas y logging
  core/         formatos, etiquetas y motor de audio
  ui/           ventana, widgets, temas e iconos SVG
resources/      recursos de la aplicacion
tests/          pruebas automatizadas
docs/           documentacion tecnica
vendor/lib/     libmpv empaquetada para desarrollo y pruebas
```
