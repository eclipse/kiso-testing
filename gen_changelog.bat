@echo off
where npx >nul 2>&1

if %ERRORLEVEL% EQU 0 ( npx auto-changelog -p --sort-commits date --starting-version 0.15.0
) else (
    echo ERROR: Update changelog failed.
    echo npx not available on your system. Install nodejs -^> https://nodejs.org/en/download/
)
