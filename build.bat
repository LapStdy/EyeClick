@echo off
chcp 65001 >nul
echo ===== EyeClick 打包脚本 =====

pyinstaller --onefile --windowed ^
    --name "EyeClick_v2.0" ^
    --icon=favicon.ico ^
    --add-data "templates;templates" ^
    --hidden-import=cv2 ^
    --hidden-import=mss ^
    --hidden-import=PIL ^
    --hidden-import=numpy ^
    --hidden-import=pynput ^
    --hidden-import=win32gui ^
    --hidden-import=win32api ^
    --hidden-import=win32con ^
    main.py

echo ===== 打包完成 =====
pause
