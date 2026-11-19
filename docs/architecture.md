# Arquitectura

## Capas

- `musetop.app`: infraestructura sin dependencias de Qt.
- `musetop.core`: formatos, lectura de etiquetas y motor de audio. No importa
  `musetop.ui`.
- `musetop.ui`: presentacion Qt. Delega reproduccion y datos en `core`.

## Reglas

1. Sin red: no se importan `requests`, `httpx`, `urllib`, `socket` ni modulos
   equivalentes en el paquete. La prueba `test_architecture.py` lo verifica.
2. Sin emojis: los iconos son SVG monocromaticos y heredan el color del tema.
   La misma prueba recorre las fuentes del paquete.
3. Rutas con `pathlib` y convenciones de cada sistema operativo.
4. Interfaz en espanol; identificadores y docstrings en ingles tecnico.
5. Sin `print`: el logger configurado es el unico canal de diagnostico.

## Datos de usuario

- Windows: `%APPDATA%\Musetop\settings.json`
- Linux: `$XDG_CONFIG_HOME/musetop/settings.json` o `~/.config/musetop/settings.json`
- Registros: subdirectorio `logs` dentro del directorio de datos.
