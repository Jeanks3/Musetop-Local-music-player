@echo off
python packaging\build.py
if errorlevel 1 exit /b 1
echo.
echo Ejecutable: dist\musetop\musetop.exe
