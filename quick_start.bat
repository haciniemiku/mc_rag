@echo off
echo ========================================
echo 鸣潮剧情RAG助手 - 快速启动
echo ========================================
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    echo.
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate

REM 检查 .env 文件
if not exist ".env" (
    echo.
    echo ========================================
    echo 警告：未找到 .env 文件
    echo ========================================
    echo.
    echo 请创建 .env 文件并添加以下内容：
    echo.
    echo MOONSHOT_API_KEY=你的Moonshot API密钥
    echo.
    pause
)

REM 安装依赖
echo.
echo 安装依赖...
pip install -r requirements.txt

REM 启动 Streamlit
echo.
echo ========================================
echo 启动 Streamlit 前端界面...
echo ========================================
echo.
streamlit run streamlit_app.py

REM 恢复环境
deactivate

pause
