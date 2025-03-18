@echo off
setlocal ENABLEDELAYEDEXPANSION

REM Default target number of parallel processes
set TARGET=3

REM If a command line argument is provided, use that as target
if not "%~1" EQU "" (
    set TARGET=%~1
)

REM The output directory where .zip files are generated
set OUTPUT_DIR=output-Async

REM The player directory where .yaml files are found
set PLAYER_DIR=Players-Async

set Extra_Args=--cache_modified_player_yamls
set venv=.\.venv
rem if using a virtual environment use it
if exist "%venv%" (
    call %venv%\scripts\activate
)

REM The executable name and the string to find the process
if exist Launcher.py (
    set EXE_NAME=Launcher.py
    set Finder=py.exe
) else (
    set EXE_NAME=ArchipelagoLauncherDebug.exe
    set Finder=ArchipelagoLauncherDebug
)

set /p TARGET="Enter number of games to generate (default 3): "
set num_players=1
echo Enter number of worlds to generate
echo Only changes things if this number is bigger than the total player yamls count
set /p num_players="Unless you use a weights.yaml you can leave this as default (default 1):"
set spoiler_lvl=1
set /p spoiler_lvl="Enter Spoiler level (default 1): "
set skip_balancing=0
set /p skip_balancing="Skip prog balancing? (default 0): "
set skip_prompt=1
set /p skip_prompt="Skip generation failure prompt?(doesn't skip missing apworlds) (default 1): "
set end_loop=1
set /p end_loop="Loop until all the gens are done or dead? (default 1): "
set /p variant="folderVariant (default null): "
set OUTPUT_DIR=%OUTPUT_DIR%\%variant%
set PLAYER_DIR=%PLAYER_DIR%\%variant%

set WindowName=AP Async Generate
if [%variant%] NEQ [] (
    set WindowName=AP Async Generate %variant%
)

title CMD: %WindowName%

if NOT %skip_balancing% EQU 0 (
    set skip_progbal=--skip_prog_balancing
)
if %skip_prompt% EQU 1 (
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
if %ERRORLEVEL% EQU 0 (
    echo A .zip file was found in the output directory at %TIME%. Generation succeeded.
    if !end_loop! EQU 1 (
        goto End_loop_Prep
    )
    echo Terminating all remaining processes...
    taskkill /F /FI "WINDOWTITLE eq %WindowName%" >nul 2>nul
    echo Done. Exiting.
    exit /b 0
)
rem tasklist /fi "WINDOWTITLE eq APGenerate" "IMAGENAME eq py.exe"
REM Count how many ArchipelagoGenerate.exe are currently running
set ProcessCount=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "%Finder%"') do (
    set ProcessCount=%%C
)


if !ProcessCount! LSS %TARGET% (
    set /a NEEDED=%TARGET%-!ProcessCount!
    echo Currently running: !ProcessCount!. Need !NEEDED! more. At %TIME%.
    for /l %%j in (1,1,!NEEDED!) do (
        echo Starting new %EXE_NAME% process...
        start "%WindowName%" "%EXE_NAME%" GenerateTweaked -- !skip_fail_prompt! !skip_progbal! --spoiler %spoiler_lvl% --multi %num_players% --outputpath .\%OUTPUT_DIR% --player_files_path .\%PLAYER_DIR% %Extra_Args%
        timeout /t 1 /nobreak >nul
    )
) else (
    rem echo Currently running: !ProcessCount!. Waiting for results...
)

REM Short wait before checking again
timeout /t 2 /nobreak >nul
goto MAIN_LOOP

:End_loop_Prep
rem give time for the process to be killed
timeout /t 2 /nobreak >nul
Set KnownProcessCount=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "%Finder%"') do (
    set KnownProcessCount=%%C
)

Set KnownFileCount=0
for /F %%i in ('dir /A:-D /B "%OUTPUT_DIR%\*.zip" 2^>nul ^| find /c /v ""') do set "KnownFileCount=%%i"

:End_loop
set ProcessCount=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "%Finder%"') do (
    set ProcessCount=%%C
)

Set FileCount=0
for /F %%i in ('dir /A:-D /B "%OUTPUT_DIR%\*.zip" 2^>nul ^| find /c /v ""') do set "FileCount=%%i"

if !ProcessCount! LSS !KnownProcessCount! (
    if !FileCount! GTR !KnownFileCount! (
        echo A Gen finished at %TIME%.
    ) else (
        echo A Gen died at %TIME%.
    )
        set KnownFileCount=!FileCount!
    if !ProcessCount! GTR 0 (
        echo there are now !ProcessCount! gens running
        set KnownProcessCount=!ProcessCount!
    ) else (
        echo Done. Exiting.
        exit /b 0
    )
) else (
    if !ProcessCount! EQU 0 (
        echo Done. Exiting.
        exit /b 0
    )
    rem echo Currently running: !ProcessCount!. Waiting for results...
)

timeout /t 2 /nobreak >nul
goto End_loop