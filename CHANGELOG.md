# Changelog

Todas las fechas usan el formato AAAA-MM-DD.

## [0.1.0a1] - En desarrollo

### Hito 1 - Esqueleto y cimientos

- Estructura de paquetes `app`, `core`, `ui`, `resources` y pruebas.
- Rutas multiplataforma basadas en `pathlib` (APPDATA en Windows, XDG en Linux).
- Preferencias JSON con validacion, escritura atomica y restablecimiento.
- Logging rotativo en el directorio de datos del usuario.
- Prueba de arquitectura que prohibe imports de red y caracteres emoji.
