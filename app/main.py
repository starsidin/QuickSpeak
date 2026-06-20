import sys
import os
import atexit
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSharedMemory
from main_window import MainWindow
from config import TEMP_DIR, APP_NAME, APP_VERSION, APP_AUTHOR

def _get_icon_path():
    """获取图标文件路径"""
    if getattr(sys, 'frozen', False):
        base = Path(os.path.dirname(sys.executable))
    else:
        base = Path(__file__).parent
    # 优先用 .ico，其次 .png
    for ext in ('.ico', '.png'):
        p = base / f'icon{ext}'
        if p.exists():
            return str(p)
    return None

def cleanup_temp_files():
    """清理临时文件（异常退出时也会执行）"""
    import glob
    try:
        if os.path.exists(TEMP_DIR):
            for pattern in ['*.wav', '*.mp3', '*.m4a', '*.flac']:
                for f in glob.glob(os.path.join(TEMP_DIR, pattern)):
                    try:
                        os.remove(f)
                    except:
                        pass
    except Exception as e:
        print(f"清理临时文件失败: {e}")

# 注册退出时的清理函数
atexit.register(cleanup_temp_files)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_AUTHOR)
    
    # 防止程序重复启动（单实例锁）
    shared_memory = QSharedMemory(APP_NAME)
    if shared_memory.attach():
        # 已有实例在运行
        QMessageBox.warning(
            None,
            f"{APP_NAME} 已在运行",
            f"{APP_NAME} 已经在运行中。\n请勿重复启动多个实例。"
        )
        sys.exit(0)
    
    if not shared_memory.create(1):
        QMessageBox.critical(
            None,
            "启动失败",
            f"无法创建单实例锁：{shared_memory.errorString()}"
        )
        sys.exit(1)
    
    # 设置应用图标
    icon_path = _get_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    
    # 防止关闭最后一个窗口时程序退出，因为我们要保留系统托盘
    app.setQuitOnLastWindowClosed(False)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
