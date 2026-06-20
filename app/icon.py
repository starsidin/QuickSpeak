from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt

def create_app_icon():
    """创建应用图标"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))  # 透明背景
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # 绘制圆形背景
    painter.setBrush(QColor("#4A90E2"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 60, 60)
    
    # 绘制麦克风图标（简化的文字）
    painter.setPen(QColor("white"))
    font = QFont("Arial", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "W")
    
    painter.end()
    return pixmap
