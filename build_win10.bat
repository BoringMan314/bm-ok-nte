@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "BUILD_TAG=build_win10"
set "OUT_DIR=dist"
set "SRC_DIR=dist_portable"
set "ZIP_DIR=dist_zip"
set "VER_SRC=src\config.py"
set "PIPY="
set "PATH=C:\Program Files\Go\bin;C:\Program Files (x86)\Go\bin;%USERPROFILE%\.cargo\bin;%APPDATA%\npm;C:\Program Files\nodejs;C:\Program Files (x86)\NSIS;C:\Program Files (x86)\NSIS\Bin;%LOCALAPPDATA%\tauri\NSIS;%LOCALAPPDATA%\tauri\NSIS\Bin;%PATH%"

call :read_version
if errorlevel 1 goto :end_fail

call :find_python
if errorlevel 1 goto :end_fail

echo [build_win10] One-click build: setup + portable + zip
echo [build_win10] version %VER_RAW%

taskkill /F /IM "bm-ok-nte.exe" /T >nul 2>&1
taskkill /F /IM "ok-nte.exe" /T >nul 2>&1

echo.
echo ===== [1/3] Win10 setup installer -^> %OUT_DIR%\%OUT_NAME% =====
echo [build_win10] cleaning %OUT_DIR% contents
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%" 2>nul
call :clean_dir_contents "%OUT_DIR%"

%PIPY% build.py win10
if errorlevel 1 goto :end_fail

echo.
echo ===== [2/3] Win10 portable -^> %SRC_DIR%\ =====
set "BUILD_TAG=build_win10_portable"
call build_win10_portable.bat nopause
if errorlevel 1 goto :end_fail

echo.
echo ===== [3/3] Win10 portable zip -^> %ZIP_DIR%\bm-ok-nte-win32-global-portable-%VER_RAW%.zip =====
echo [build_win10] cleaning %ZIP_DIR% contents
if not exist "%ZIP_DIR%" mkdir "%ZIP_DIR%" 2>nul
call :clean_dir_contents "%ZIP_DIR%"

if not exist "%SRC_DIR%" (
  echo [build_win10] FAIL: missing %SRC_DIR%\
  goto :end_fail
)

%PIPY% tools/zip_portable.py
if errorlevel 1 goto :end_fail

echo.
echo [build_win10] All done:
echo   - %OUT_DIR%\%OUT_NAME%
echo   - %SRC_DIR%\
echo   - %ZIP_DIR%\bm-ok-nte-win32-global-portable-%VER_RAW%.zip
goto :end_ok

:find_python
set "PIPY="
for %%V in (3.12) do (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -%%V -c "import sys; assert sys.version_info[:2]==(3,12)" 2>nul
    if not errorlevel 1 (
      set "PIPY=py -%%V"
      goto :find_ok
    )
  )
)
where python >nul 2>&1
if not errorlevel 1 (
  python -c "import sys; assert sys.version_info[:2]==(3,12)" 2>nul
  if not errorlevel 1 (
    set "PIPY=python"
    goto :find_ok
  )
)
where py >nul 2>&1
if not errorlevel 1 (
  py -c "import sys; assert sys.version_info[:2]==(3,12)" 2>nul
  if not errorlevel 1 (
    set "PIPY=py"
    goto :find_ok
  )
)
echo [build_win10] FAIL: no Python 3.12 in PATH (use py -3.12 or python 3.12)
exit /b 1

:find_ok
exit /b 0

:read_version
set "OUT_NAME="
if not exist "%VER_SRC%" (
  echo [build_win10] FAIL: missing %VER_SRC%
  exit /b 1
)
for /f "usebackq tokens=2 delims==" %%A in (`findstr /C:"version = " "%VER_SRC%"`) do set "VER_RAW=%%A"
if not defined VER_RAW (
  echo [build_win10] FAIL: could not read version from %VER_SRC%
  exit /b 1
)
set "VER_RAW=%VER_RAW: =%"
set "VER_RAW=%VER_RAW:"=%"
if "%VER_RAW%"=="" (
  echo [build_win10] FAIL: invalid version in %VER_SRC%
  exit /b 1
)
set "OUT_NAME=bm-ok-nte-win32-global-setup-%VER_RAW%.exe"
exit /b 0

:clean_dir_contents
set "TGT=%~1"
if not exist "%TGT%" exit /b 0
for /f "delims=" %%D in ('dir /b /ad "%TGT%" 2^>nul') do rd /s /q "%TGT%\%%D" 2>nul
del /f /q "%TGT%\*" 2>nul
exit /b 0

:end_fail
if /i "%~1"=="nopause" exit /b 1
echo.
pause
exit /b 1

:end_ok
if /i "%~1"=="nopause" exit /b 0
echo.
pause
exit /b 0
