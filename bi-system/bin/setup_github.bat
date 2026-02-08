@echo off
echo ==========================================
echo       Setup GitHub Repository
echo ==========================================

:: Switch to project root directory
cd /d "%~dp0.."

echo Current Git Remote:
git remote -v
echo.

set /p remote_url="Please paste your GitHub Repository URL (e.g., https://github.com/username/repo.git): "

if "%remote_url%"=="" (
    echo Error: No URL provided.
    pause
    exit /b
)

echo.
echo Setting remote origin to: %remote_url%

:: Try to remove existing origin just in case
git remote remove origin >nul 2>&1

:: Add new origin
git remote add origin %remote_url%

echo.
echo Renaming branch to 'main'...
git branch -M main

echo.
echo Pushing local code to GitHub (this may ask for credentials)...
git push -u origin main

echo.
echo Setup complete! You can now use bin\git_auto_push.bat for automatic updates.
pause
