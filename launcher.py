"""PyInstaller 启动脚本 — 在包外启动, 避免相对导入问题"""
from snake_game.main import main

if __name__ == "__main__":
    main()
