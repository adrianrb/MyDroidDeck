@echo off
rem MyDroidDeck - stop the running server.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\control.ps1" -Action stop
