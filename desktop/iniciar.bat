@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 goto fallback
py -3 -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if errorlevel 1 goto fallback
py -3 main.py
set "AERIS_EXIT=%errorlevel%"
goto finished
:fallback
where python >nul 2>&1
if errorlevel 1 goto missing
python -c "import sys, tkinter; sys.exit(0 if sys.version_info >= (3,12) else 1)" >nul 2>&1
if errorlevel 1 goto missing
python main.py
set "AERIS_EXIT=%errorlevel%"
:finished
if not "%AERIS_EXIT%"=="0" (
  echo Aeris terminou com codigo %AERIS_EXIT%. Consulte READY.md.
  pause
)
exit /b %AERIS_EXIT%
:missing
echo Instale Python 3.12 ou superior com Tcl/Tk. Consulte READY.md.
pause
exit /b 1
