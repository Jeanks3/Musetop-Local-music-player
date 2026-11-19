# Empaquetado

## Estrategia

Se usa PyInstaller en modo `onedir`. El arranque es más rápido que en `onefile`
porque no se descomprime todo el entorno Qt en cada inicio. La carpeta
`dist/musetop` contiene el ejecutable, `_internal` y los recursos.

La especificación `packaging/musetop.spec`:

- incluye todos los iconos SVG en `musetop/ui/icons`;
- incluye el icono de aplicación en `resources`;
- recopila los submódulos de mutagen;
- copia libmpv a `_internal/vendor/lib` cuando existe en `vendor/lib`;
- usa `console=False`, por lo que no abre una consola en Windows.

La carga nativa usa las rutas de `musetop/app/paths.py`. En una aplicación
congelada, `vendor_lib_dir()` apunta a `_MEIPASS/vendor/lib`, que corresponde a
`dist/musetop/_internal/vendor/lib`.

## Linux

Requisitos de compilación:

```bash
sudo apt install libmpv1 ffmpeg python3.11-venv
python -m pip install -e ".[dev]"
```

Compilación:

```bash
python packaging/build.py
# o
packaging/build-linux.sh
```

Resultado:

```text
dist/musetop/
  musetop
  musetop.desktop
  musetop.svg
  _internal/
```

Comprobación de humo sin pantalla:

```bash
QT_QPA_PLATFORM=offscreen timeout 5 ./dist/musetop/musetop
```

El código de salida 124 significa que la ventana permaneció abierta hasta el
tiempo límite.

La biblioteca libmpv incluida en `vendor/lib` está compilada para la familia de
distribución del entorno de desarrollo. Para distribuir en otra versión de
Ubuntu, compila en esa versión o elimina la copia local y usa la libmpv del
sistema.

## Windows 10+

Requisitos:

1. Python 3.11+ de 64 bits.
2. Dependencias instaladas con `pip install -e ".[dev]"`.
3. `vendor\lib\mpv-2.dll` o `vendor\lib\libmpv-2.dll`.

Compilación:

```powershell
python packaging\build.py
# o
packaging\build.bat
```

Resultado:

```text
dist\musetop\
  musetop.exe
  _internal\
```

Distribuye la carpeta completa. El `.exe` no funciona si se copia solo, porque
las DLL de Qt y libmpv viven en `_internal`.

## Limitaciones conocidas

- PyInstaller no compila para Windows desde Linux ni viceversa. Cada binario se
  genera en su sistema operativo.
- El binario Linux no es portable entre distribuciones con versiones de glibc
  incompatibles. Compílalo en la versión mínima que quieras soportar.
- No se incluye instalador MSI ni AppImage; esta pre-alpha entrega una carpeta
  ejecutable y un archivo `.desktop`.
