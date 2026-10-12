@echo off
rem MyDroidDeck - report whether the server is running and its version.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\control.ps1" -Action status
