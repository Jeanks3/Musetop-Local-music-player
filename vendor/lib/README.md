# libmpv para desarrollo

Esta carpeta contiene una copia de libmpv usada por las pruebas de integración y
por el empaquetado en Linux x86_64.

- Versión observada con `mpv --version`: mpv 0.40.0 / libmpv 2.5.0.
- Licencia de libmpv: LGPL-2.1-or-later. El código fuente de mpv está en
  https://github.com/mpv-player/mpv y los avisos de licencia acompañan a la
  distribución original de mpv.
- La aplicación Musetop se distribuye bajo licencia MIT; este componente nativo
  conserva su propia licencia.

Windows no usa esta biblioteca. Coloca `mpv-2.dll` o `libmpv-2.dll` en esta
carpeta antes de ejecutar o empaquetar en Windows.
