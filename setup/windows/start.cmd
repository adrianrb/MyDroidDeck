@echo off
rem MyDroidDeck - start the server (hidden) if it is not already running.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\control.ps1" -Action start
