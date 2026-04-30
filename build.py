"""
构建脚本 — 用 PyInstaller 打包为单个 exe
"""

import subprocess
import sys

args = [
    "pyinstaller",
    "--onefile",
    "--windowed",
    "--name", "贪吃蛇",
    "--distpath", "dist",
    "--workpath", "build_temp",
    "--specpath", ".",
    "--clean",
    "--noconfirm",
    "launcher.py",
]

result = subprocess.run(args, cwd=r"C:/Users/12673/Desktop/test")
sys.exit(result.returncode)
