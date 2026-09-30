@echo off
chcp 65001 > nul
title SnakeDonuts - ADS Unimar
color 0B

set TF_CPP_MIN_LOG_LEVEL=3
set TF_ENABLE_ONEDNN_OPTS=0
set GLOG_minloglevel=3
set PYTHONWARNINGS=ignore

echo =====================================================================
echo                     SNAKEDONUTS - STAND UNIMAR
echo =====================================================================
echo  Inicializando o jogo por visao computacional...
echo  Controle a cobrinha com a ponta do seu dedo indicador!
echo =====================================================================
echo.

cd /d "%~dp0"

REM 1. Verifica se existe ambiente virtual local
if exist ".venv\Scripts\python.exe" (
    echo [AMBIENTE] Utilizando Python do ambiente virtual local (.venv)...
    .venv\Scripts\python.exe main.py
    goto FINISH
)

REM 2. Verifica se existe ambiente virtual no diretorio pai (projeto OpenCV completo)
if exist "..\.venv\Scripts\python.exe" (
    echo [AMBIENTE] Utilizando Python do ambiente virtual principal (..\.venv)...
    ..\.venv\Scripts\python.exe main.py
    goto FINISH
)

REM 3. Fallback para Python global do sistema
echo [AMBIENTE] Utilizando Python padrao do sistema...
python main.py

:FINISH
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] Ocorreu uma falha na execucao ou o jogo foi fechado de forma inesperada.
    echo Verifique se a webcam esta conectada e as dependencias foram instaladas:
    echo     pip install -r requirements.txt
    echo.
    pause
)
