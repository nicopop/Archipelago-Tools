@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Default target number of parallel processes
set TARGET=3

REM If a command line argument is provided, use that as target
if not "%~1"=="" (
    set TARGET=%~1
)

REM The executable name
REM set EXE_NAME=ArchipelagoGenerate.exe
set EXE_NAME=Generate-Tweaked.py

REM The output directory where .zip files are generated
set OUTPUT_DIR=output-Async

REM The output directory where .zip files are generated
set PLAYER_DIR=Players-Async

set venv=.\.venv
rem if using a virtual enviroment use it
if exist "%venv%" (
    call %venv%\scripts\activate
)

set /p TARGET="Enter number of games to generate (default 3): "
set num_players=1
set /p num_players="Enter number of worlds to generate (default 1): "
set spoiler_lvl=1
set /p spoiler_lvl="Enter Spoiler level (default 1): "
set skip_balancing=0
set /p skip_balancing="Skip prog balancing? (default 0): "
set skip_prompt=1
set /p skip_prompt="Skip generation failure promp?(doesnt skip missing apworlds) (default 1): "
set end_loop=1
set /p end_loop="Loop until all the gens are done or dead? (default 1): "
set /p variant="folderVariant (default null): "
set OUTPUT_DIR=%OUTPUT_DIR%\%variant%
set PLAYER_DIR=%PLAYER_DIR%\%variant%
set WindowName=AP Async Generate -%variant%
title CMD: %WindowName%

if NOT %skip_balancing% == 0 (
  set skip_progbal=--skip_prog_balancing
)
if %skip_prompt% == 1 (
  set skip_fail_prompt=--skip_prompt
)

REM Ensure output directory exists
if not exist "%OUTPUT_DIR%" (
    echo Creating output directory "%OUTPUT_DIR%"
    mkdir "%OUTPUT_DIR%"
)

:MAIN_LOOP

REM Check if there's any ZIP file in the output directory as a success indicator
dir /b "%OUTPUT_DIR%\*.zip" >nul 2>nul
if %ERRORLEVEL%==0 (
    echo A .zip file was found in the output directory at %TIME%. Generation succeeded.
    if !end_loop! == 1 (
        goto End_loop_Prep
    )
    echo Terminating all remaining processes...
    taskkill /F /FI "WINDOWTITLE eq %WindowName%" >nul 2>nul
    echo Done. Exiting.
    exit /b 0
)
rem tasklist /fi "WINDOWTITLE eq APGenerate" "IMAGENAME eq py.exe"
REM Count how many ArchipelagoGenerate.exe are currently running
set COUNT=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "py.exe"') do (
    set COUNT=%%C
)


if !COUNT! LSS %TARGET% (
    set /a NEEDED=%TARGET%-!COUNT!
    echo Currently running: !COUNT!. Need !NEEDED! more. At %TIME%.
    for /l %%j in (1,1,!NEEDED!) do (
        echo Starting new %EXE_NAME% process...
        start "%WindowName%" "%EXE_NAME%" !skip_fail_prompt! !skip_progbal! --spoiler %spoiler_lvl% --multi %num_players% --outputpath .\%OUTPUT_DIR% --player_files_path .\%PLAYER_DIR%
        rem start "%WindowName%" "%EXE_NAME%" --spoiler %spoiler_lvl% --multi %num_players% --outputpath .\%OUTPUT_DIR% --player_files_path .\%PLAYER_DIR%
    )
) else (
    rem echo Currently running: !COUNT!. Waiting for results...
)

REM Short wait before checking again
timeout /t 2 /nobreak >nul
goto MAIN_LOOP

:End_loop_Prep
Set GenCOUNT=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "py.exe"') do (
    set GenCOUNT=%%C
)
Set GenFile=0
for /F %%i in ('dir /b "%OUTPUT_DIR%\*.zip" 2>nul ^| find /c /v ""') do set "GenFile=%%i"

:End_loop
set COUNT=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "py.exe"') do (
    set COUNT=%%C
)
Set FileCount=0
rem TODO FIX: 2>nul somehow crash
for /F %%i in ('dir /A:-D /B "%OUTPUT_DIR%\*.zip" 2>nul | find /c /v ""') do set "GenFile=%%i"

if !COUNT! LSS !GenCOUNT! (
    if !FileCount! GTR !GenFile! (
        echo A Gen finished at %TIME%.
    ) else (
        echo A Gen died at %TIME%.
    )
        set GenFile=!FileCount!
    if !COUNT! GTR 0 (
        echo there are now !COUNT! gens running
        set GenLeft=!COUNT!
    ) else (
        echo Done. Exiting.
        exit /b 0
    )
) else (
    if !COUNT! == 0(
        echo Done. Exiting.
        exit /b 0
    )
    rem echo Currently running: !COUNT!. Waiting for results...
)


timeout /t 2 /nobreak >nul
goto End_loop