#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成应用图标"""

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QPen
from PySide6.QtCore import Qt
import sys
import os

def create_icon():
    """创建应用图标"""
    app = QApplication(sys.argv)
    
    # 创建 256x256 图标
    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    
    # 圆角矩形背景，带渐变
    gradient = QLinearGradient(0, 0, 0, size)
    gradient.setColorAt(0, QColor('#5B9FE8'))
    gradient.setColorAt(1, QColor('#2A6CB8'))
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(8, 8, size-16, size-16, 40, 40)
    
    # 白色麦克风形状（简化）
    # 麦克风头部（圆形）
    painter.setBrush(QColor('white'))
    painter.setPen(Qt.NoPen)
    cx, cy = size//2, size//2 - 20
    painter.drawRoundedRect(cx-28, cy-40, 56, 80, 28, 28)
    
    # 麦克风支架弧线
    painter.setPen(QPen(QColor('white'), 8))
    painter.setBrush(Qt.NoBrush)
    painter.drawArc(cx-45, cy-10, 90, 80, 0, -180*16)
    
    # 支架线
    painter.drawLine(cx, cy+60, cx, cy+85)
    # 底座
    painter.drawLine(cx-30, cy+85, cx+30, cy+85)
    
    # 底部文字
    painter.setPen(QColor('white'))
    font = QFont('Segoe UI', 18, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect().adjusted(0, 50, 0, 0), Qt.AlignBottom | Qt.AlignHCenter, 'QuickSpeak')
    
    painter.end()
    
    # 保存图标
    icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
    pixmap.save(icon_path)
    print(f'图标已创建: {icon_path}')
    
    # 同时保存为 .ico 格式（用于 Windows）
    ico_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    pixmap.save(ico_path)
    print(f'图标已创建: {ico_path}')

if __name__ == '__main__':
    create_icon()
