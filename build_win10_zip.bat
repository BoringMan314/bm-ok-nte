@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set "SRC_DIR=dist_portable"
set "ZIP_DIR=dist_zip"
set "PIPY="

echo [build_win10_zip] Build Win10 portable + zip -^> %ZIP_DIR%\bm-ok-nte-win32-global-portable-^<version^>.zip
echo [build_win10_zip] cleaning %ZIP_DIR% contents
set "BUILD_TAG=build_win10_zip"

if not exist "%ZIP_DIR%" mkdir "%ZIP_DIR%" 2>nul
call :clean_dir_contents "%ZIP_DIR%"

call build_win10_portable.bat nopause
if errorlevel 1 goto :end_fail

if not exist "%SRC_DIR%" (
  echo [build_win10_zip] FAIL: missing %SRC_DIR%\
  goto :end_fail
)

call :find_python
if errorlevel 1 goto :end_fail

%PIPY% tools/zip_portable.py
if errorlevel 1 goto :end_fail

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
echo [build_win10_zip] FAIL: no Python 3.12 in PATH
exit /b 1

:find_ok
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
