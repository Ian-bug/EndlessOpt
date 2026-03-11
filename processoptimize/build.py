import PyInstaller.__main__
import os
import shutil

APP_NAME = "WindowsProcessOptimize"
ICON_PATH = "icon.ico" if os.path.exists("icon.ico") else None

params = [
    "main.py", 
    "--name", APP_NAME,    
    "--onefile",           
    "--windowed",          
    "--noconsole",         
    "--clean",
    "--icon", ICON_PATH if ICON_PATH else "NONE",
    "--distpath", "dist"   
]


PyInstaller.__main__.run(params)

print(f"\n{APP_NAME} 已成功打包到 dist 目录!")
