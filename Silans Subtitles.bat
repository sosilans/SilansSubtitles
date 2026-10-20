@echo off
cd /d "%~dp0"
set "PYW="
if exist "C:\Python314\pythonw.exe" set "PYW=C:\Python314\pythonw.exe"
if not defined PYW (
  for /f "delims=" %%I in ('where pythonw 2^>nul') do (
    set "PYW=%%I"
    goto run
  )
)
:run
if not defined PYW (
  echo Не найден Python. Нужен pythonw.exe.
  pause
  exit /b 1
)
start "" "%PYW%" "%~dp0SilansSubtitles.pyw"
