import os
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QCheckBox,
    QSystemTrayIcon, QMenu, QFileDialog, QMessageBox, QSizeGrip,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QStyle
)
from PySide6.QtCore import Qt, QPoint, QTimer, QSettings
from PySide6.QtGui import QIcon, QAction

from config import ASR_BASE_URL, TEMP_WAV_FILE
from clipboard_util import copy_to_clipboard
from audio_recorder import AudioRecorder
from asr_client import ASRClient

class SettingsDialog(QDialog):
    def __init__(self, current_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(350, 120)
        layout = QFormLayout(self)
        self.url_input = QLineEdit(current_url)
        self.url_input.setPlaceholderText("例如: http://localhost:8000/v1")
        layout.addRow("后端 API 地址:", self.url_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_url(self):
        return self.url_input.text().strip()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("快说")
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
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

        # 初始化模块
        self.recorder = AudioRecorder(TEMP_WAV_FILE)
        self.asr = ASRClient(saved_url)

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
        btn_layout = QHBoxLayout()
        self.btn_record_start = QPushButton("开始录音")
        self.btn_record_stop = QPushButton("停止录音")
        self.btn_record_stop.setEnabled(False)
        self.btn_import = QPushButton("导入音频")
        self.btn_save_audio = QPushButton("保存录音")
        self.btn_save_audio.setEnabled(False)  # 刚开始没有录音文件时置灰
        
        btn_layout.addWidget(self.btn_record_start)
        btn_layout.addWidget(self.btn_record_stop)
        btn_layout.addWidget(self.btn_import)
        btn_layout.addWidget(self.btn_save_audio)
        
        btn_container = QWidget()
        btn_container.setLayout(btn_layout)
        btn_container.setContentsMargins(0, 0, 15, 0)
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
        
        # 为了让文本框右边也有边距，套一层
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 15, 0)
        text_layout.addWidget(self.text_asr)
        main_layout.addWidget(text_container)

        # 底部操作与设置区
        bottom_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton("复制")
        self.btn_copy.setStyleSheet("background-color: #607D8B;")
        self.btn_save = QPushButton("保存为 TXT")
        self.btn_save.setStyleSheet("background-color: #607D8B;")
        
        self.chk_auto_copy = QCheckBox("自动复制")
        self.chk_auto_copy.setChecked(True)
        
        self.chk_keep_history = QCheckBox("保留历史")
        self.chk_keep_history.setChecked(True)
        
        bottom_layout.addWidget(self.btn_copy)
        bottom_layout.addWidget(self.btn_save)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.chk_keep_history)
        bottom_layout.addWidget(self.chk_auto_copy)
        
        bottom_container = QWidget()
        bottom_container.setLayout(bottom_layout)
        bottom_container.setContentsMargins(0, 0, 15, 15)
        main_layout.addWidget(bottom_container)
        
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
        self.btn_import.clicked.connect(self.on_import_audio)
        self.btn_save_audio.clicked.connect(self.on_save_audio)
        self.btn_clear.clicked.connect(self.on_clear)
        self.btn_copy.clicked.connect(self.on_copy)
        self.btn_save.clicked.connect(self.on_save)

        # 录音信号
        self.recorder.recording_started.connect(self.handle_recording_started)
        self.recorder.recording_stopped.connect(self.handle_recording_stopped)
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
        dialog = SettingsDialog(self.asr.base_url, self)
        if dialog.exec() == QDialog.Accepted:
            new_url = dialog.get_url()
            if new_url:
                self.settings.setValue("asr_base_url", new_url)
                self.asr.base_url = new_url.rstrip("/")
                self.status_label.setText("检查后端连接...")
                self.asr.check_health()

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

    def on_save(self):
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
                self.status_label.setText("已保存")
                self.status_label.setStyleSheet("color: #4CAF50;")
            except Exception as e:
                self.handle_error(f"保存失败: {str(e)}")

    # --- 录音回调 ---
    def handle_recording_started(self):
        self.status_label.setText("正在录音...")
        self.status_label.setStyleSheet("color: #ff9800;")
        self.btn_record_start.setEnabled(False)
        self.btn_record_stop.setEnabled(True)

    def handle_recording_stopped(self, wav_path):
        self.status_label.setText("录音结束，准备识别...")
        self.btn_record_start.setEnabled(True)
        self.btn_record_stop.setEnabled(False)
        self.asr.transcribe(wav_path)

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
        
        # 判断是否保留历史
        if self.chk_keep_history.isChecked():
            current_text = self.text_asr.toPlainText()
            if current_text:
                self.text_asr.setText(f"{current_text}\n{text}")
            else:
                self.text_asr.setText(text)
        else:
            # 不保留历史，直接替换
            self.text_asr.setText(text)
        
        # 将滚动条移动到最下方
        scrollbar = self.text_asr.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        if self.chk_auto_copy.isChecked():
            # 复制时，如果勾选了保留历史，就复制所有内容；
            # 如果没勾选，上面已经被替换为只有最新的内容，也是复制当前所有。
            # 为了符合直觉：“自动复制”往往期望复制“刚刚识别出”的那句话。
            # 但既然界面上是整个文本框，我们如果自动复制，且保留历史时，
            # 用户可能只想复制“新”的那句，或者全部。
            # 这里的实现：直接调用 on_copy_latest(text) 复制最新，或者维持复制全部。
            # 按照你的描述“如果保留历史，就是保持现在状态；如果不保留历史，就在新复制开始前清空内容”
            # 意味着如果不保留历史，框里只有新内容，复制就只复制新内容。
            # 下面调用普通复制，它会复制文本框里的所有内容。
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
        self.tray_icon.hide()
        # 清理临时文件
        if os.path.exists(TEMP_WAV_FILE):
            try:
                os.remove(TEMP_WAV_FILE)
            except:
                pass
        QApplication.quit()
