import os
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QCheckBox,
    QSystemTrayIcon, QMenu, QFileDialog, QMessageBox, QSizeGrip,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QStyle, QComboBox
)
from PySide6.QtCore import Qt, QPoint, QTimer, QSettings
from PySide6.QtGui import QIcon, QAction

from config import ASR_BASE_URL, TEMP_WAV_FILE
from clipboard_util import copy_to_clipboard
from audio_recorder import AudioRecorder
from asr_client import ASRClient

class SettingsDialog(QDialog):
    def __init__(self, current_url, current_device_index=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(350, 160)
        layout = QFormLayout(self)
        self.url_input = QLineEdit(current_url)
        self.url_input.setPlaceholderText("例如: http://localhost:8000/v1")
        layout.addRow("后端 API 地址:", self.url_input)
        
        self.device_combo = QComboBox()
        self.devices = AudioRecorder.get_input_devices()
        
        # 默认添加一个“系统默认”的选项
        self.device_combo.addItem("系统默认", userData=None)
        
        # 填充获取到的麦克风列表
        for dev in self.devices:
            self.device_combo.addItem(dev['name'], userData=dev['index'])
            
        # 设置当前选中的设备
        if current_device_index is not None:
            # 查找 userData 匹配的索引
            index = self.device_combo.findData(current_device_index)
            if index >= 0:
                self.device_combo.setCurrentIndex(index)
                
        layout.addRow("选择麦克风:", self.device_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_url(self):
        return self.url_input.text().strip()
        
    def get_device_index(self):
        """返回选中的设备索引，如果选择系统默认则返回 None"""
        return self.device_combo.currentData()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快说")
        # 移除 Qt.Tool，这样程序就会在底部任务栏显示图标，点击 "-" 最小化时才会真正收到任务栏里
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(350, 250)  # 调小窗口高度
        self.old_pos = None

        # 录音时间相关
        self.record_start_time = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

        # 读取设置
        self.settings = QSettings("KuaiShuoApp", "Settings")
        saved_url = self.settings.value("asr_base_url", ASR_BASE_URL)
        saved_device_index = self.settings.value("mic_device_index", None)
        if saved_device_index is not None:
            try:
                saved_device_index = int(saved_device_index)
            except ValueError:
                saved_device_index = None

        # 初始化模块
        self.recorder = AudioRecorder(TEMP_WAV_FILE, device_index=saved_device_index)
        self.asr = ASRClient(saved_url)
        
        # 创作模式状态
        self.is_creative_mode = False

        # 界面初始化
        self.init_ui()
        self.init_tray()
        self.connect_signals()

        # 检查后端状态
        self.status_label.setText("检查后端连接...")
        self.asr.check_health()

    def init_ui(self):
        # 主控部件
        self.central_widget = QWidget(self)
        # 更新为浅蓝色/白色现代化主题
        self.central_widget.setStyleSheet("""
            QWidget#CentralWidget {
                background-color: #f5f9ff;
                border-radius: 12px;
            }
            QLabel { color: #555555; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 6px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:pressed { background-color: #285A8C; }
            QPushButton:disabled { background-color: #cccccc; color: #888888; }
            QTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                placeholder-text-color: #bbbbbb;
            }
            QCheckBox {
                color: #555555;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
        """)
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)

        # 这里调整布局边距，让整个布局贴紧边缘，以便 size_grip 也能贴紧右下角
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(15, 15, 0, 0)
        main_layout.setSpacing(10)

        # 顶部区域 (标题和状态)
        top_layout = QHBoxLayout()
        title_label = QLabel("快说")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #333333;")
        
        settings_btn = QPushButton("⚙")
        settings_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #999999; font-size: 16px; padding: 0; }
            QPushButton:hover { color: #4A90E2; }
        """)
        settings_btn.setFixedSize(20, 20)
        settings_btn.clicked.connect(self.open_settings)
        
        self.status_label = QLabel("正在初始化...")
        self.status_label.setStyleSheet("font-size: 12px; color: #888888;")
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #f44336;")
        self.timer_label.hide()
        
        min_btn = QPushButton("—")
        min_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #999999; font-size: 16px; padding: 0; font-weight: bold; }
            QPushButton:hover { color: #333333; }
        """)
        min_btn.setFixedSize(20, 20)
        min_btn.clicked.connect(self.showMinimized)  # 折叠到任务栏
        
        close_btn = QPushButton("×")
        close_btn.setStyleSheet("""
            QPushButton { background-color: transparent; color: #999999; font-size: 16px; padding: 0; }
            QPushButton:hover { color: #f44336; }
        """)
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide)  # 点击叉号最小化隐藏到系统托盘
        
        top_layout.addWidget(title_label)
        top_layout.addWidget(settings_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.timer_label)
        top_layout.addWidget(self.status_label)
        top_layout.addWidget(min_btn)
        top_layout.addWidget(close_btn)
        
        # 给顶部和内部内容单独加个边距，弥补 main_layout 右边距为0的问题
        top_container = QWidget()
        top_container.setLayout(top_layout)
        top_container.setContentsMargins(0, 0, 15, 0)
        main_layout.addWidget(top_container)

        # 核心操作区
        btn_container_layout = QVBoxLayout()
        btn_container_layout.setContentsMargins(0, 0, 15, 0)
        btn_container_layout.setSpacing(5)

        # 第一行按钮
        btn_layout_row1 = QHBoxLayout()
        self.btn_record_start = QPushButton("开始录音")
        self.btn_record_stop = QPushButton("停止录音")
        self.btn_record_stop.setEnabled(False)
        
        btn_layout_row1.addWidget(self.btn_record_start)
        btn_layout_row1.addWidget(self.btn_record_stop)
        
        # 第二行按钮
        btn_layout_row2 = QHBoxLayout()
        self.btn_record_cancel = QPushButton("取消录音")
        self.btn_record_cancel.setEnabled(False)
        self.btn_record_cancel.setStyleSheet("""
            QPushButton { background-color: #ff9800; }
            QPushButton:hover { background-color: #e68a00; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        
        self.btn_import = QPushButton("导入音频")
        self.btn_save_audio = QPushButton("保存录音")
        self.btn_save_audio.setEnabled(False)  # 刚开始没有录音文件时置灰
        
        btn_layout_row2.addWidget(self.btn_record_cancel)
        btn_layout_row2.addWidget(self.btn_import)
        btn_layout_row2.addWidget(self.btn_save_audio)
        
        btn_container_layout.addLayout(btn_layout_row1)
        btn_container_layout.addLayout(btn_layout_row2)
        
        btn_container = QWidget()
        btn_container.setLayout(btn_container_layout)
        main_layout.addWidget(btn_container)

        # 文本区
        self.text_asr = QTextEdit()
        self.text_asr.setPlaceholderText("识别结果将显示在这里，可直接编辑...")
        
        # 允许编辑
        self.text_asr.setReadOnly(False)
        
        # 结果标签行（带清空按钮）
        result_header_layout = QHBoxLayout()
        lbl_result = QLabel("识别结果:")
        
        self.btn_clear = QPushButton("清空")
        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                font-weight: normal;
                font-size: 12px;
                padding: 0px 5px;
            }
            QPushButton:hover { color: #f44336; }
        """)
        
        result_header_layout.addWidget(lbl_result)
        result_header_layout.addStretch()
        result_header_layout.addWidget(self.btn_clear)
        
        result_header_container = QWidget()
        result_header_container.setLayout(result_header_layout)
        result_header_container.setContentsMargins(0, 0, 15, 0)
        main_layout.addWidget(result_header_container)
        
        # 富文本编辑工具栏 (默认隐藏)
        self.format_toolbar_widget = QWidget()
        format_layout = QHBoxLayout(self.format_toolbar_widget)
        format_layout.setContentsMargins(0, 0, 0, 5)
        
        # 按钮统一样式：白色文字，稍深的蓝色背景以增加对比度，选中状态有区分
        format_btn_style = """
            QPushButton {
                font-family: serif; 
                color: #ffffff;
                background-color: #5C9FE6;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4A90E2;
            }
            QPushButton:checked {
                background-color: #285A8C;
                border: 1px solid #1a3d61;
            }
        """
        
        self.btn_bold = QPushButton("B")
        self.btn_bold.setStyleSheet(format_btn_style + "font-weight: bold;")
        self.btn_bold.setFixedSize(28, 28)
        self.btn_bold.setCheckable(True)
        
        self.btn_italic = QPushButton("I")
        self.btn_italic.setStyleSheet(format_btn_style + "font-style: italic;")
        self.btn_italic.setFixedSize(28, 28)
        self.btn_italic.setCheckable(True)
        
        self.btn_underline = QPushButton("U")
        self.btn_underline.setStyleSheet(format_btn_style + "text-decoration: underline;")
        self.btn_underline.setFixedSize(28, 28)
        self.btn_underline.setCheckable(True)
        
        # 字体大小调节器
        self.combo_font_size = QComboBox()
        # 提供常用的字体大小
        font_sizes = ["8", "9", "10", "11", "12", "13", "14", "16", "18", "20", "24", "28", "32", "36", "48", "72"]
        self.combo_font_size.addItems(font_sizes)
        self.combo_font_size.setCurrentText("13")  # 默认字体大小
        self.combo_font_size.setFixedWidth(60)
        self.combo_font_size.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 2px 5px;
            }
        """)
        
        self.btn_import_text = QPushButton("导入文本")
        self.btn_import_text.setStyleSheet("background-color: #FF9800;")
        
        self.btn_save_txt = QPushButton("保存为 TXT")
        self.btn_save_txt.setStyleSheet("background-color: #4CAF50;")
        
        self.btn_save_word = QPushButton("保存为 Word")
        self.btn_save_word.setStyleSheet("background-color: #2196F3;")
        
        self.btn_exit_creative = QPushButton("退出创作")
        self.btn_exit_creative.setStyleSheet("background-color: #f44336;")
        
        format_layout.addWidget(self.btn_bold)
        format_layout.addWidget(self.btn_italic)
        format_layout.addWidget(self.btn_underline)
        format_layout.addWidget(QLabel(" 字号:"))
        format_layout.addWidget(self.combo_font_size)
        format_layout.addStretch()
        format_layout.addWidget(self.btn_import_text)
        format_layout.addWidget(self.btn_save_txt)
        format_layout.addWidget(self.btn_save_word)
        format_layout.addWidget(self.btn_exit_creative)
        
        self.format_toolbar_widget.hide()

        # 为了让文本框右边也有边距，套一层
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 15, 0)
        text_layout.addWidget(self.format_toolbar_widget)
        text_layout.addWidget(self.text_asr)
        main_layout.addWidget(text_container)

        # 底部操作与设置区
        bottom_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton("复制")
        self.btn_copy.setStyleSheet("background-color: #607D8B;")
        self.btn_creative = QPushButton("创作模式")
        self.btn_creative.setStyleSheet("background-color: #9C27B0;")
        
        self.chk_auto_copy = QCheckBox("自动复制")
        self.chk_auto_copy.setChecked(True)
        
        bottom_layout.addWidget(self.btn_copy)
        bottom_layout.addWidget(self.btn_creative)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.chk_auto_copy)
        
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_layout)
        bottom_container.setContentsMargins(0, 0, 15, 0)
        main_layout.addWidget(bottom_container)
        
        # 提示小字
        hint_label = QLabel("提示：首次进入或长时间未用后，加载模型需要等待20s。")
        hint_label.setStyleSheet("font-size: 10px; color: #999999;")
        hint_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hint_layout = QHBoxLayout()
        hint_layout.setContentsMargins(0, 0, 15, 10)
        hint_layout.addStretch()
        hint_layout.addWidget(hint_label)
        
        hint_container = QWidget()
        hint_container.setLayout(hint_layout)
        main_layout.addWidget(hint_container)
        
        # 添加右下角的拖拽大小调整手柄
        self.size_grip = QSizeGrip(self.central_widget)
        self.size_grip.setFixedSize(15, 15)
        self.size_grip.setStyleSheet("background-color: transparent;")
        # 将手柄直接附加在主窗口右下角，而不是放在 layout 里
        self.size_grip.move(self.width() - 15, self.height() - 15)
        self.size_grip.show()
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 窗口大小改变时，手动更新右下角 size_grip 的位置，确保它始终在最边缘
        if hasattr(self, 'size_grip') and self.size_grip:
            self.size_grip.move(self.width() - 15, self.height() - 15)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # 为了防止系统托盘中没有图标而导致完全找不到程序，我们使用内置的图标或者绘制一个简单的纯色图标
        icon = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.showNormal)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()
            self.activateWindow()

    def connect_signals(self):
        # 按钮事件
        self.btn_record_start.clicked.connect(self.on_record_start)
        self.btn_record_stop.clicked.connect(self.on_record_stop)
        self.btn_record_cancel.clicked.connect(self.on_record_cancel)
        self.btn_import.clicked.connect(self.on_import_audio)
        self.btn_save_audio.clicked.connect(self.on_save_audio)
        self.btn_clear.clicked.connect(self.on_clear)
        self.btn_copy.clicked.connect(self.on_copy)
        
        self.btn_creative.clicked.connect(self.enter_creative_mode)
        self.btn_exit_creative.clicked.connect(self.exit_creative_mode)
        self.btn_import_text.clicked.connect(self.on_import_text)
        self.btn_save_txt.clicked.connect(self.on_save_txt)
        self.btn_save_word.clicked.connect(self.on_save_word)
        
        self.btn_bold.clicked.connect(self.toggle_bold)
        self.btn_italic.clicked.connect(self.toggle_italic)
        self.btn_underline.clicked.connect(self.toggle_underline)
        self.combo_font_size.currentTextChanged.connect(self.change_font_size)
        self.text_asr.cursorPositionChanged.connect(self.update_format_buttons)

        # 录音信号
        self.recorder.recording_started.connect(self.handle_recording_started)
        self.recorder.recording_stopped.connect(self.handle_recording_stopped)
        self.recorder.recording_canceled.connect(self.handle_recording_canceled)
        self.recorder.error_occurred.connect(self.handle_error)

        # ASR 信号
        self.asr.backend_status.connect(self.handle_backend_status)
        self.asr.request_started.connect(self.handle_asr_started)
        self.asr.request_finished.connect(self.handle_asr_finished)
        self.asr.request_failed.connect(self.handle_error)

    # --- 拖拽窗口逻辑 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    # --- 槽函数 ---
    def on_record_start(self):
        # 每次开始新录音前，先尝试删除旧的临时文件
        if os.path.exists(TEMP_WAV_FILE):
            try:
                os.remove(TEMP_WAV_FILE)
            except Exception as e:
                print(f"删除临时文件失败: {e}")
                
        self.btn_save_audio.setEnabled(False)
        self.record_start_time = time.time()
        self.timer_label.setText("00:00")
        self.timer_label.show()
        self.timer.start(1000)
        self.recorder.start_recording()

    def on_record_stop(self):
        self.timer.stop()
        self.timer_label.hide()
        self.recorder.stop_recording()
        self.btn_save_audio.setEnabled(True)  # 录音停止后允许保存录音

    def on_record_cancel(self):
        self.timer.stop()
        self.timer_label.hide()
        self.recorder.cancel_recording()

    def update_timer(self):
        elapsed = int(time.time() - self.record_start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def on_import_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.ogg *.m4a);;All Files (*)"
        )
        if file_path:
            self.status_label.setText("正在识别导入的音频...")
            self.status_label.setStyleSheet("color: #2196F3;")
            self.asr.transcribe(file_path)

    def open_settings(self):
        dialog = SettingsDialog(self.asr.base_url, self.recorder.device_index, self)
        if dialog.exec() == QDialog.Accepted:
            new_url = dialog.get_url()
            if new_url:
                self.settings.setValue("asr_base_url", new_url)
                self.asr.base_url = new_url.rstrip("/")
                self.status_label.setText("检查后端连接...")
                self.asr.check_health()
                
            new_device_index = dialog.get_device_index()
            if new_device_index is not None:
                self.settings.setValue("mic_device_index", new_device_index)
            else:
                self.settings.remove("mic_device_index")
            self.recorder.set_device(new_device_index)

    def on_save_audio(self):
        if not os.path.exists(TEMP_WAV_FILE):
            self.handle_error("未找到录音文件")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存录音",
            "record.wav",
            "Audio Files (*.wav);;All Files (*)"
        )
        if file_path:
            try:
                import shutil
                shutil.copy2(TEMP_WAV_FILE, file_path)
                self.status_label.setText("录音已保存")
                self.status_label.setStyleSheet("color: #4CAF50;")
            except Exception as e:
                self.handle_error(f"保存录音失败: {str(e)}")

    def on_clear(self):
        self.text_asr.clear()
        self.status_label.setText("已清空")

    def on_copy(self):
        text = self.text_asr.toPlainText()
        if copy_to_clipboard(text):
            self.status_label.setText("已复制")
            self.status_label.setStyleSheet("color: #4CAF50;")

    def enter_creative_mode(self):
        self.is_creative_mode = True
        self.format_toolbar_widget.show()
        self.btn_creative.hide()
        self.btn_copy.hide()
        self.chk_auto_copy.hide()
        self.resize(600, 450)
        
    def exit_creative_mode(self):
        reply = QMessageBox.question(
            self,
            "退出创作",
            "退出创作模式后，当前文本记录将消失，是否确认退出？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.is_creative_mode = False
            self.format_toolbar_widget.hide()
            self.btn_creative.show()
            self.btn_copy.show()
            self.chk_auto_copy.show()
            self.text_asr.clear()
            self.resize(350, 250)

    def toggle_bold(self):
        self.text_asr.setFontWeight(700 if self.btn_bold.isChecked() else 400)

    def toggle_italic(self):
        self.text_asr.setFontItalic(self.btn_italic.isChecked())

    def toggle_underline(self):
        self.text_asr.setFontUnderline(self.btn_underline.isChecked())
        
    def change_font_size(self, size_str):
        try:
            size = float(size_str)
            self.text_asr.setFontPointSize(size)
        except ValueError:
            pass

    def update_format_buttons(self):
        self.btn_bold.setChecked(self.text_asr.fontWeight() >= 700)
        self.btn_italic.setChecked(self.text_asr.fontItalic())
        self.btn_underline.setChecked(self.text_asr.fontUnderline())
        
        # 同步字体大小下拉框
        size = self.text_asr.fontPointSize()
        if size > 0:
            self.combo_font_size.blockSignals(True)
            # 找到最接近的值或者直接设置为当前值
            index = self.combo_font_size.findText(str(int(size)))
            if index >= 0:
                self.combo_font_size.setCurrentIndex(index)
            else:
                self.combo_font_size.setCurrentText(str(int(size)))
            self.combo_font_size.blockSignals(False)

    def on_import_text(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入文本文件",
            "",
            "文本文件 (*.txt *.docx);;TXT 文件 (*.txt);;Word 文件 (*.docx);;All Files (*)"
        )
        if not file_path:
            return

        cursor = self.text_asr.textCursor()
        
        try:
            if file_path.lower().endswith(".docx"):
                from docx import Document
                doc = Document(file_path)
                html_content = ""
                for para in doc.paragraphs:
                    para_html = ""
                    for run in para.runs:
                        text = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                        
                        # 处理字号 (font size)
                        pt_size = None
                        if run.font and run.font.size:
                            pt_size = run.font.size.pt
                        elif run.style and run.style.font and run.style.font.size:
                            pt_size = run.style.font.size.pt
                        
                        if pt_size:
                            text = f"<span style='font-size: {pt_size}pt;'>{text}</span>"
                            
                        # 处理基本格式
                        if run.bold:
                            text = f"<b>{text}</b>"
                        if run.italic:
                            text = f"<i>{text}</i>"
                        if run.underline:
                            text = f"<u>{text}</u>"
                        para_html += text
                        
                    # 判断段落样式 (标题、列表)
                    style_name = para.style.name if para.style else ""
                    
                    if style_name.startswith('Heading'):
                        try:
                            level = int(style_name.split(' ')[-1])
                        except:
                            level = 1
                        html_content += f"<h{level}>{para_html}</h{level}>"
                    elif 'List' in style_name:
                        # 简单处理为 HTML 的无序列表项
                        html_content += f"<ul><li>{para_html}</li></ul>"
                    else:
                        # 组装成普通段落
                        if para_html.strip() == "":
                            html_content += "<br>"
                        else:
                            html_content += f"<p>{para_html}</p>"
                
                # 插入带有格式的 HTML
                cursor.insertHtml(html_content)
                
            else:
                # 处理普通 txt 文件
                with open(file_path, "r", encoding="utf-8") as f:
                    text_content = f.read()
                cursor.insertText(text_content)
                
            self.status_label.setText("文本已导入")
            self.status_label.setStyleSheet("color: #4CAF50;")
            
            # 确保文本框获取焦点
            self.text_asr.setFocus()
            
        except Exception as e:
            self.handle_error(f"导入文本失败: {str(e)}")

    def on_save_txt(self):
        text = self.text_asr.toPlainText()
        if not text.strip():
            self.handle_error("没有可保存的内容")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存为 TXT 文件",
            "asr_result.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.status_label.setText("已保存为 TXT")
                self.status_label.setStyleSheet("color: #4CAF50;")
            except Exception as e:
                self.handle_error(f"保存 TXT 失败: {str(e)}")

    def on_save_word(self):
        text = self.text_asr.toPlainText()
        if not text.strip():
            self.handle_error("没有可保存的内容")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存为 Word 文件",
            "asr_result.docx",
            "Word Files (*.docx);;All Files (*)"
        )
        
        if file_path:
            try:
                from docx import Document
                doc = Document()
                
                # 保留富文本格式（粗体、斜体、下划线）
                text_document = self.text_asr.document()
                for i in range(text_document.blockCount()):
                    block = text_document.findBlockByNumber(i)
                    p = doc.add_paragraph()
                    it = block.begin()
                    while not it.atEnd():
                        fragment = it.fragment()
                        if fragment.isValid():
                            run = p.add_run(fragment.text())
                            char_format = fragment.charFormat()
                            if char_format.fontWeight() >= 700:
                                run.bold = True
                            if char_format.fontItalic():
                                run.italic = True
                            if char_format.fontUnderline():
                                run.underline = True
                        it += 1
                        
                doc.save(file_path)
                self.status_label.setText("已保存为 Word")
                self.status_label.setStyleSheet("color: #4CAF50;")
            except Exception as e:
                self.handle_error(f"保存 Word 失败: {str(e)}")

    # --- 录音回调 ---
    def handle_recording_started(self):
        self.status_label.setText("正在录音...")
        self.status_label.setStyleSheet("color: #ff9800;")
        self.btn_record_start.setEnabled(False)
        self.btn_record_stop.setEnabled(True)
        self.btn_record_cancel.setEnabled(True)
        # 录音时禁用“退出创作”按钮
        self.btn_exit_creative.setEnabled(False)

    def handle_recording_stopped(self, wav_path):
        self.status_label.setText("录音结束，准备识别...")
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(False)
        self.btn_record_cancel.setEnabled(False)
        # 录音停止后恢复“退出创作”按钮
        self.btn_exit_creative.setEnabled(True)
        self.asr.transcribe(wav_path)
        
    def handle_recording_canceled(self):
        self.status_label.setText("录音已取消")
        self.status_label.setStyleSheet("color: #999999;")
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(False)
        self.btn_record_cancel.setEnabled(False)
        self.btn_exit_creative.setEnabled(True)

    # --- ASR 回调 ---
    def handle_backend_status(self, is_ok):
        if is_ok:
            self.status_label.setText("后端可用")
            self.status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.status_label.setText("后端不可用")
            self.status_label.setStyleSheet("color: #f44336;")

    def handle_asr_started(self):
        self.status_label.setText("正在识别...")
        self.status_label.setStyleSheet("color: #2196F3;")

    def handle_asr_finished(self, text):
        self.status_label.setText("识别完成")
        self.status_label.setStyleSheet("color: #4CAF50;")
        
        # 创作模式：在当前光标位置插入
        if self.is_creative_mode:
            cursor = self.text_asr.textCursor()
            current_text = self.text_asr.toPlainText()
            # 如果已有内容且不是在开头，插入前加一个换行，保持段落清晰
            if current_text and cursor.position() > 0:
                cursor.insertText("\n" + text)
            else:
                cursor.insertText(text)
        else:
            # 普通模式：只显示最新
            self.text_asr.setText(text)
        
        # 确保文本框滚动到光标处
        self.text_asr.ensureCursorVisible()
        
        # 自动复制功能（仅在普通模式下生效，因为创作模式下可能有复杂的编辑）
        if self.chk_auto_copy.isChecked() and not self.is_creative_mode:
            self.on_copy()

    # --- 错误处理 ---
    def handle_error(self, err_msg):
        self.status_label.setText("错误")
        self.status_label.setStyleSheet("color: #f44336;")
        # 将错误信息显示在文本框，方便排查
        self.text_asr.setText(f"发生错误:\n{err_msg}")
        print(f"ERROR: {err_msg}")
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(False)

    def quit_app(self):
        reply = QMessageBox.question(
            self,
            "退出程序",
            "退出前请确保你需要保存的内容已进行保存。\n确认要退出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.tray_icon.hide()
            # 清理临时文件
            if os.path.exists(TEMP_WAV_FILE):
                try:
                    os.remove(TEMP_WAV_FILE)
                except:
                    pass
            QApplication.quit()
