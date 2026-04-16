from PySide6.QtGui import QGuiApplication

def copy_to_clipboard(text: str) -> bool:
    """
    复制文本到系统剪贴板
    """
    if not text:
        return False
    clipboard = QGuiApplication.clipboard()
    clipboard.setText(text)
    return True
