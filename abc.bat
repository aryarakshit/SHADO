@echo off
setlocal
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%~dp0src\main.py" %*
) else (
    python "%~dp0src\main.py" %*
)
if %ERRORLEVEL% NEQ 0 pause
endlocal
