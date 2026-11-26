@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 goto fallback
py -3 -c "import tkinter" >nul 2>&1
if errorlevel 1 goto fallback
py -3 main.py
if errorlevel 1 pause
exit /b %errorlevel%
:fallback
where python >nul 2>&1
if errorlevel 1 goto missing
python -c "import tkinter" >nul 2>&1
if errorlevel 1 goto missing
python main.py
if errorlevel 1 pause
exit /b %errorlevel%
:missing
echo Instale Python 3.12 ou 3.13 com Tcl/Tk e tente novamente.
pause
exit /b 1
