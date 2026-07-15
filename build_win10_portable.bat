@echo off
setlocal EnableExtensions
chcp 65001 >nul 2>&1
cd /d "%~dp0"
if not defined BUILD_TAG set "BUILD_TAG=build_win10_portable"
set "PIPY="
set "PATH=C:\Program Files\Go\bin;C:\Program Files (x86)\Go\bin;%USERPROFILE%\.cargo\bin;%APPDATA%\npm;C:\Program Files\nodejs;%PATH%"

echo [%BUILD_TAG%] Build portable -^> dist_portable\

taskkill /F /IM "bm-ok-nte.exe" /T >nul 2>&1
taskkill /F /IM "ok-nte.exe" /T >nul 2>&1

if not exist "dist_portable" mkdir "dist_portable" 2>nul

call :find_python
if errorlevel 1 goto :end_fail

%PIPY% build.py win10_portable
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
echo [build_win10_portable] FAIL: no Python 3.12 in PATH (use py -3.12 or python 3.12)
exit /b 1

:find_ok
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
