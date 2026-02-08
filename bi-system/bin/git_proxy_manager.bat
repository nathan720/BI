@echo off
setlocal
cd /d "%~dp0.."

:menu
cls
echo ==========================================
echo       Git Network/Proxy Manager
echo ==========================================
echo This tool helps resolve "Connection was reset" or timeout errors
echo by configuring Git to use your local proxy (VPN).
echo.
echo Current Repository Proxy Settings:
git config --local --get http.proxy
git config --local --get https.proxy
echo.
echo 1. Set Proxy to 127.0.0.1:7890 (Common for Clash/v2ray)
echo 2. Set Proxy to 127.0.0.1:10809 (Common for v2rayN)
echo 3. Enter Custom Proxy Address
echo 4. Clear/Unset Proxy (Direct Connection)
echo 5. Test Connection to GitHub
echo 6. Return to Main Menu / Exit
echo.
set /p choice="Enter choice (1-6): "

if "%choice%"=="1" call :set_proxy 127.0.0.1:7890
if "%choice%"=="2" call :set_proxy 127.0.0.1:10809
if "%choice%"=="3" goto custom
if "%choice%"=="4" call :clear_proxy
if "%choice%"=="5" goto test
if "%choice%"=="6" exit /b

goto menu

:set_proxy
git config --local http.proxy http://%1
git config --local https.proxy http://%1
echo.
echo [OK] Proxy set to %1 for this repository.
echo You can now try running bin\setup_github.bat or bin\git_auto_push.bat again.
pause
goto menu

:custom
set /p custom_proxy="Enter proxy (e.g., 127.0.0.1:8888): "
if "%custom_proxy%"=="" goto menu
call :set_proxy %custom_proxy%
goto menu

:clear_proxy
git config --local --unset http.proxy
git config --local --unset https.proxy
echo.
echo [OK] Proxy settings cleared. Git will try to connect directly.
pause
goto menu

:test
echo.
echo Testing connection to github.com (via curl)...
curl -I https://github.com
if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Connection successful!
) else (
    echo.
    echo [FAIL] Connection failed. Please try a different proxy port.
)
pause
goto menu
