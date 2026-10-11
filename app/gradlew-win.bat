@echo off
rem Build helper for this machine. JAVA_HOME is not set globally, and the Android
rem SDK / JDK live under C:\desenv; the WSL shell cannot use the Windows SDK, so
rem builds must run through Windows cmd.exe (or Android Studio).
if not defined JAVA_HOME set "JAVA_HOME=C:\desenv\JDKs\jdk-21.0.7"
set "PATH=%JAVA_HOME%\bin;%PATH%"
if not defined ANDROID_HOME set "ANDROID_HOME=C:\desenv\Android\Sdk"
if not defined ANDROID_SDK_ROOT set "ANDROID_SDK_ROOT=C:\desenv\Android\Sdk"
cd /d "%~dp0"
call "%~dp0gradlew.bat" %*
