@echo off
echo ========================================
echo HivisionIDPhotos Windows 打包脚本
echo ========================================
echo.

REM 检查 Python 是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM 检查是否已下载模型
if not exist "hivision\creator\weights\hivision_modnet.onnx" (
    echo [警告] 未检测到模型文件，正在下载...
    python scripts\download_model.py --models hivision_modnet
)

REM 安装打包依赖
echo [1/4] 安装打包依赖...
pip install pyinstaller onnxruntime opencv-python-headless >nul 2>&1

REM 检查依赖是否安装完成
if errorlevel 1 (
    echo [警告] 依赖安装可能有问题，继续尝试打包...
)

REM 清理旧的构建文件
echo [2/4] 清理旧构建文件...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM 开始打包
echo [3/4] 开始打包 (这可能需要 5-15 分钟)...
pyinstaller app.spec

REM 检查打包结果
if exist "dist\HivisionIDPhotos.exe" (
    echo.
    echo ========================================
    echo [成功] 打包完成！
    echo ========================================
    echo.
    echo 可执行文件位置: dist\HivisionIDPhotos.exe
    echo.
    echo 注意事项:
    echo 1. 首次运行会自动打开浏览器访问 http://127.0.0.1:7860
    echo 2. 模型文件已内置在 exe 中，无需额外下载
    echo 3. 建议使用命令行运行以查看日志: HivisionIDPhotos.exe
    echo.
) else (
    echo [错误] 打包失败，请检查上面的错误信息
    echo.
    echo 常见问题:
    echo - 缺少依赖: 运行 pip install -r requirements.txt
    echo - 模型文件缺失: 运行 python scripts/download_model.py --models all
    echo - 杀毒软件拦截: 请临时关闭杀毒软件后重试
    echo.
)

pause
