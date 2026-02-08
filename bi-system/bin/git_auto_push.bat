@echo off
echo ==========================================
echo       Auto Git Commit and Push
echo ==========================================

:: Switch to project root directory
cd /d "%~dp0.."

echo [1/3] Adding changes...
git add .

echo [2/3] Committing changes...
:: Get current date and time for commit message
set "timestamp=%date% %time%"
git commit -m "Auto update: %timestamp%"

echo [3/3] Pushing to remote...
git push origin main

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed. Please check your network or git configuration.
    echo Note: If this is your first time, make sure you have set up the remote origin.
) else (
    echo.
    echo [SUCCESS] Code submitted to GitHub successfully.
)

pause
