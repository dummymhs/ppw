@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo =========================================
echo    Menjalankan Crawler + PageRank
echo =========================================
echo.

set "PY=..\enwebmining\Scripts\python.exe"

if not exist "%PY%" (
    echo [X] Python environment enwebmining tidak ditemukan.
    echo     Pastikan folder aplikasi ini ada di dalam folder Webmining.
    echo.
    pause
    exit /b 1
)

"%PY%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo [!] Streamlit belum terpasang, menginstall dulu...
    "%PY%" -m pip install -r requirements.txt
    echo.
)

echo Aplikasi akan terbuka otomatis di browser.
echo Tutup jendela ini kalau mau mematikan aplikasinya.
echo.

"%PY%" -m streamlit run "app\streamlit_app.py" %*

echo.
echo Aplikasi berhenti.
pause
