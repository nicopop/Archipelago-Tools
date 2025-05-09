@echo off
setlocal ENABLEDELAYEDEXPANSION
REM The output directory where .zip files are generated
set OUTPUT_DIR=output

REM The player directory where .yaml files are found
set PLAYER_DIR=Players

set Extra_Args=GenerateTweaked -- --cache_modified_player_yamls

rem A Custom executable called to generate, by default will detect AP's launcher and use it.
rem Remove the [] if you want to set this to something.
set EXE_NAME=[]
rem If you use a custom exe the script might not find the process name you can set it manually here
set Finder=[]

set venv=.\.venv
rem if using a virtual environment use it
if exist "%venv%" (
    call %venv%\scripts\activate
)
REM The executable name and the string to find the process
if %EXE_NAME% EQU [] (
    if exist Launcher.py (
        set EXE_NAME=Launcher.py
    ) else (
        set EXE_NAME=ArchipelagoLauncherDebug.exe
    )
)

if %Finder% EQU [] (
    if /I [!EXE_NAME:~-3!] EQU [.py] (
        set Finder=py.exe
    ) else (
        set Finder=!EXE_NAME:~0,-4!
    )
)
echo Executable used for generations: !EXE_NAME!
echo Proccess name used to find still alive generations: !Finder!

set TARGET=3
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
echo Subfolder name for player/output folder
echo AKA where to get the yamls in the %PLAYER_DIR% folder
echo AND where to put the zip in the %OUTPUT_DIR% folder
echo EX: using '8th' will check files in %PLAYER_DIR%\8th\
set /p subfolder="Default to just using %PLAYER_DIR%/%OUTPUT_DIR% directly: "
set OUTPUT_DIR=%OUTPUT_DIR%\%subfolder%
set PLAYER_DIR=%PLAYER_DIR%\%subfolder%

set WindowName=AP Async Generate
if [%subfolder%] NEQ [] (
    set WindowName=AP Async Generate %subfolder%
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
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "!Finder!"') do (
    set ProcessCount=%%C
)


if !ProcessCount! LSS %TARGET% (
    set /a NEEDED=%TARGET%-!ProcessCount!
    echo Currently running: !ProcessCount!. Need !NEEDED! more. At %TIME%.
    for /l %%j in (1,1,!NEEDED!) do (
        echo Starting new %EXE_NAME% process...
        start "%WindowName%" "!EXE_NAME!" %Extra_Args% !skip_fail_prompt! !skip_progbal! --spoiler %spoiler_lvl% --multi %num_players% --outputpath .\%OUTPUT_DIR% --player_files_path .\%PLAYER_DIR%
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
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "!Finder!"') do (
    set KnownProcessCount=%%C
)

Set KnownFileCount=0
for /F %%i in ('dir /A:-D /B "%OUTPUT_DIR%\*.zip" 2^>nul ^| find /c /v ""') do set "KnownFileCount=%%i"

:End_loop
set ProcessCount=0
for /f "delims=" %%C in ('tasklist /FI "WINDOWTITLE eq %WindowName%" ^| find /I /C "!Finder!"') do (
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