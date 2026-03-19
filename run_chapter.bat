@echo off
setlocal EnableDelayedExpansion

REM Configuration
set "PROJECT_DIR=%~dp0"
set "CHAPTER_DIR=%PROJECT_DIR%chapters"
if not exist "%CHAPTER_DIR%" mkdir "%CHAPTER_DIR%"

REM User Input
set /p CHAPTER="Enter Chapter Number: "
set /p URLS="Enter Comma-Separated Image URLs (no spaces): "

REM Step 1: Download Images
echo.
echo [1/4] Downloading Images for Chapter %CHAPTER%...
python "%PROJECT_DIR%download_images.py" --chapter %CHAPTER% --urls "%URLS%" --output-dir "%CHAPTER_DIR%"
if %ERRORLEVEL% NEQ 0 (
    echo Error downloading images. Exiting.
    pause
    exit /b %ERRORLEVEL%
)

REM Step 2: Generate Narration (Placeholder for now, user needs to provide audio or use TTS script if available)
REM For now, we will create a dummy audio file if one doesn't exist, just to make the render work for testing.
REM In a real scenario, you'd use the Gemini/TTS part here.
set "AUDIO_PATH=%CHAPTER_DIR%\chapter_%CHAPTER:~-3%\narration.mp3"

if not exist "!AUDIO_PATH!" (
    echo.
    echo [WARNING] No narration.mp3 found in chapter folder!
    echo Please place a 'narration.mp3' file in: !CHAPTER_DIR!\chapter_%CHAPTER:~-3%
    echo OR press any key to generate a silent dummy audio for testing...
    pause
    
    REM Create 10s silent MP3 using ffmpeg if available, or just copy a dummy if present. 
    REM Since we don't know if ffmpeg is installed, we can't easily generate mp3 on the fly without it.
    REM Let's ask the user to provide it.
    echo.
    echo Please copy your narration audio file to:
    echo "!AUDIO_PATH!"
    echo.
    echo Once you have done that, press any key to continue...
    pause
)

REM Step 3: Render Video
echo.
echo [3/4] Rendering Video...
set "OUTPUT_VIDEO=%CHAPTER_DIR%\chapter_%CHAPTER:~-3%\final_video.mp4"
python "%PROJECT_DIR%render.py" --chapter %CHAPTER% --chapter-dir "%CHAPTER_DIR%\chapter_%CHAPTER:~-3%" --audio "!AUDIO_PATH!" --output "!OUTPUT_VIDEO!"
if %ERRORLEVEL% NEQ 0 (
    echo Error rendering video. Exiting.
    pause
    exit /b %ERRORLEVEL%
)

REM Step 4: Upload to YouTube
echo.
echo [4/4] Uploading to YouTube...
python "%PROJECT_DIR%upload.py" --video "!OUTPUT_VIDEO!" --title "ORV Chapter %CHAPTER%" --description "Omniscient Reader's Viewpoint Chapter %CHAPTER% Recap" --tags "ORV,Omniscient Reader,Manhwa" --privacy "private"
if %ERRORLEVEL% NEQ 0 (
    echo Error uploading video.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo DONE! Chapter %CHAPTER% processed and uploaded.
echo ===================================================
pause
