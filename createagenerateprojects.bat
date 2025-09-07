@echo off
setlocal

printf "=== Aegis project generation ===\n"

rem Configure Qt paths; allow override via QT_DIR env var.
if "%QT_DIR%"=="" (
    set "QT_DIR=C:\\Qt\\6.6.0\\msvc2019_64"
)

if not exist "%QT_DIR%" (
    printf "Qt directory not found: %QT_DIR%\n"
    exit /b 1
)

printf "Using Qt at %QT_DIR%\n"

set "PATH=%QT_DIR%\bin;%PATH%"
set "CMAKE_PREFIX_PATH=%QT_DIR%\lib\cmake;%CMAKE_PREFIX_PATH%"
set "INCLUDE=%QT_DIR%\include;%INCLUDE%"
set "LIB=%QT_DIR%\lib;%LIB%"

set "BUILD_DIR=%~dp0build"
if not exist "%BUILD_DIR%" (
    printf "Creating build directory %BUILD_DIR%\n"
    mkdir "%BUILD_DIR%"
)

where cmake >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    printf "Generating project files with CMake...\n"
    cmake -G "Visual Studio 17 2022" -S "%~dp0" -B "%BUILD_DIR%"
) else (
    where qmake >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        printf "CMake not found; falling back to qmake...\n"
        pushd "%BUILD_DIR%"
        qmake "%~dp0Aegis.pro" -tp vc
        popd
    ) else (
        printf "Neither CMake nor qmake was found in PATH.\n"
        exit /b 1
    )
)

if exist "%BUILD_DIR%\Aegis.sln" (
    printf "Aegis.sln generated successfully in %BUILD_DIR%\n"
) else (
    printf "Failed to generate Aegis.sln\n"
    exit /b 1
)

exit /b 0
