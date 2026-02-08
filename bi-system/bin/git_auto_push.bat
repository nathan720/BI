@echo off
echo ==========================================
echo       Auto Git Commit and Push
echo ==========================================

:: Switch to project root dir@echo off
cd /d "%~dp0..\.."

echo [1/4] Pulling latest changes from remote...
git pull origin main

echo [2/4] Adding changes from repo root...
git add .

echo [3/4] Committing changes...
:: Get current date and time for commit message
set "timestamp=%date% %time%"
git commit -m "Auto update: %timestamp%"

echo [4/4] Pushing to remote...
git push origin main
pause

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Push failed. Please check your network or git configuration.
    echo Note: If this is your first time, make sure you have set up the remote origin.
) else (
    echo.
    echo [SUCCESS] Code submitted to GitHub successfully.
)

pause
