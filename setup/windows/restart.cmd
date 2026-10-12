@echo off
rem MyDroidDeck - restart the server (stop, then start).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\control.ps1" -Action restart
