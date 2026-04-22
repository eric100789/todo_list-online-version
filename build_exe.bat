@echo off
chcp 65001 >nul
echo ============================================
echo   Todo List - 打包為 EXE 執行檔
echo ============================================
echo.

REM 檢查 PyInstaller 是否已安裝
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] 正在安裝 PyInstaller ...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] PyInstaller 安裝失敗，請手動執行: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo [INFO] 開始打包...
echo.

pyinstaller --noconfirm --onefile --windowed ^
    --name "TodoList" ^
    --icon "fish.ico" ^
    --hidden-import PyQt6 ^
    --hidden-import PyQt6.sip ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import i18n ^
    --hidden-import styles ^
    --hidden-import database ^
    --hidden-import date_utils ^
    --hidden-import task_card ^
    --hidden-import dialogs ^
    --hidden-import history_view ^
    --hidden-import settings_panel ^
    --hidden-import mini_mode ^
    --hidden-import main_window ^
    --hidden-import notes_view ^
    --hidden-import pkgutil ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] 打包失敗！請檢查上方錯誤訊息。
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包完成！
echo   EXE 檔案位於: dist\TodoList.exe
echo ============================================
echo.
pause
