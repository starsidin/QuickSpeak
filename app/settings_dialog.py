import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QFileDialog, QGroupBox,
    QMessageBox, QProgressBar, QTabWidget, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from config import APP_NAME, APP_DISPLAY_NAME, APP_VERSION, APP_AUTHOR


class MicTestThread(QThread):
    """后台线程测试麦克风是否有声音"""
    level_updated = Signal(int)  # 音量级别 0-100
    finished_signal = Signal(bool, str)  # (成功, 消息)

    def __init__(self, device_index=None, duration=3.0, parent=None):
        super().__init__(parent)
        self.device_index = device_index
        self.duration = duration
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def run(self):
        try:
            import sounddevice as sd
            import numpy as np

            samplerate = 16000
            channels = 1
            blocksize = 1024
            max_amplitude = 0.0
            found_sound = False

            def callback(indata, frames, time_info, status):
                nonlocal max_amplitude, found_sound
                if self._stop_flag:
                    raise sd.CallbackStop()
                amp = np.abs(indata).mean() * 100
                level = min(int(amp * 5), 100)
                self.level_updated.emit(level)
                if amp > 0.01:
                    found_sound = True

            with sd.InputStream(
                samplerate=samplerate,
                channels=channels,
                blocksize=blocksize,
                callback=callback,
                device=self.device_index
            ):
                import time
                start = time.time()
                while time.time() - start < self.duration and not self._stop_flag:
                    QThread.msleep(50)

            if found_sound:
                self.finished_signal.emit(True, "麦克风测试完成，检测到声音输入")
            else:
                self.finished_signal.emit(False, "未检测到声音输入，请检查麦克风")
        except Exception as e:
            self.finished_signal.emit(False, f"麦克风测试失败: {str(e)}")


class SettingsDialog(QDialog):
    """设置对话框：默认保存目录、录音快捷键、ASR 引擎切换、麦克风选择、关于"""

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f9ff;
            }
            QTabWidget::pane {
                border: 1px solid #dcdcdc;
                background-color: white;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e8f0fe;
                color: #4A90E2;
                padding: 8px 20px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4A90E2;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #357ABD;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dcdcdc;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #555555;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:pressed { background-color: #285A8C; }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QCheckBox {
                color: #555555;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QProgressBar {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                text-align: center;
                background-color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #4A90E2;
                border-radius: 3px;
            }
        """)

        self.settings = current_settings or {}
        self._recording_hotkey = False
        self._captured_key = self.settings.get("hotkey_key", "")
        self._mic_test_thread = None

        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 创建标签页控件
        self.tab_widget = QTabWidget()
        
        # 创建设置页面
        settings_page = QWidget()
        self.init_settings_page(settings_page)
        
        # 创建关于页面
        about_page = QWidget()
        self.init_about_page(about_page)
        
        # 添加标签页
        self.tab_widget.addTab(settings_page, "设置")
        self.tab_widget.addTab(about_page, "关于")
        
        layout.addWidget(self.tab_widget)

        # --- 底部按钮 ---
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #cccccc;
                color: #333333;
            }
            QPushButton:hover { background-color: #bbbbbb; }
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def init_settings_page(self, page):
        """初始化设置页面"""
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- 麦克风设备选择 ---
        mic_group = QGroupBox("麦克风设备")
        mic_layout = QVBoxLayout(mic_group)

        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel("输入设备:"))
        self.combo_mic = QComboBox()
        self.combo_mic.setMinimumWidth(200)
        mic_row.addWidget(self.combo_mic, 1)

        self.btn_refresh_mic = QPushButton("刷新")
        self.btn_refresh_mic.setFixedWidth(60)
        self.btn_refresh_mic.clicked.connect(self._refresh_mic_devices)
        mic_row.addWidget(self.btn_refresh_mic)
        mic_layout.addLayout(mic_row)

        # 测试区域
        test_row = QHBoxLayout()
        self.btn_test_mic = QPushButton("测试麦克风")
        self.btn_test_mic.setFixedWidth(100)
        self.btn_test_mic.clicked.connect(self._test_mic)
        test_row.addWidget(self.btn_test_mic)

        self.progress_mic = QProgressBar()
        self.progress_mic.setRange(0, 100)
        self.progress_mic.setValue(0)
        self.progress_mic.setTextVisible(False)
        self.progress_mic.setFixedHeight(16)
        test_row.addWidget(self.progress_mic, 1)

        self.lbl_mic_status = QLabel("")
        self.lbl_mic_status.setStyleSheet("font-size: 11px; color: #999999;")
        test_row.addWidget(self.lbl_mic_status)
        mic_layout.addLayout(test_row)

        hint_mic = QLabel("提示：选择要使用的麦克风，点击测试验证是否有声音输入")
        hint_mic.setStyleSheet("font-size: 11px; color: #999999;")
        mic_layout.addWidget(hint_mic)

        layout.addWidget(mic_group)

        # --- 保存目录设置 ---
        save_group = QGroupBox("默认保存目录")
        save_layout = QVBoxLayout(save_group)

        save_row = QHBoxLayout()
        self.txt_save_folder = QLineEdit()
        self.txt_save_folder.setPlaceholderText("留空则使用系统文档目录")
        self.txt_save_folder.setText(self.settings.get("save_folder", ""))
        self.txt_save_folder.setReadOnly(True)

        btn_browse = QPushButton("浏览...")
        btn_browse.setFixedWidth(70)
        btn_browse.clicked.connect(self._browse_save_folder)

        save_row.addWidget(self.txt_save_folder)
        save_row.addWidget(btn_browse)
        save_layout.addLayout(save_row)

        hint = QLabel("提示：保存 TXT、Word、录音文件时默认打开此目录")
        hint.setStyleSheet("font-size: 11px; color: #999999;")
        save_layout.addWidget(hint)

        layout.addWidget(save_group)

        # --- 录音快捷键设置 ---
        hotkey_group = QGroupBox("录音快捷键（按住说话）")
        hotkey_layout = QVBoxLayout(hotkey_group)

        hotkey_row1 = QHBoxLayout()
        self.chk_hotkey = QCheckBox("启用全局快捷键录音")
        self.chk_hotkey.setChecked(self.settings.get("hotkey_enabled", False))
        hotkey_row1.addWidget(self.chk_hotkey)
        hotkey_layout.addLayout(hotkey_row1)

        hotkey_row2 = QHBoxLayout()
        hotkey_row2.addWidget(QLabel("快捷键："))
        self.lbl_hotkey = QPushButton(self._captured_key if self._captured_key else "未设置")
        self.lbl_hotkey.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: normal;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #e8f0fe; }
            QPushButton:pressed { background-color: #d0e0f8; }
        """)
        self.lbl_hotkey.setCheckable(True)
        self.lbl_hotkey.clicked.connect(self._toggle_capture_hotkey)
        hotkey_row2.addWidget(self.lbl_hotkey)
        hotkey_row2.addStretch()
        hotkey_layout.addLayout(hotkey_row2)

        hint2 = QLabel("提示：点击按钮后按下想要设置的键，按住该键开始录音，松开停止")
        hint2.setStyleSheet("font-size: 11px; color: #999999;")
        hint2.setWordWrap(True)
        hotkey_layout.addWidget(hint2)

        layout.addWidget(hotkey_group)

        # --- ASR 引擎切换 ---
        asr_group = QGroupBox("识别引擎")
        asr_layout = QVBoxLayout(asr_group)

        asr_row = QHBoxLayout()
        asr_row.addWidget(QLabel("当前引擎："))
        self.combo_asr = QComboBox()
        self.combo_asr.addItem("豆包 API", "doubao")
        self.combo_asr.addItem("本地千问 (Qwen)", "qwen")
        self.combo_asr.addItem("本地 Whisper（已舍弃）", "whisper_disabled")
        whisper_item = self.combo_asr.model().item(2)
        if whisper_item is not None:
            whisper_item.setEnabled(False)

        # 设置当前选项
        current_provider = self.settings.get("asr_provider", "doubao")
        if current_provider == "local":
            self.combo_asr.setCurrentIndex(1)
        else:
            self.combo_asr.setCurrentIndex(0)

        asr_row.addWidget(self.combo_asr)
        asr_row.addStretch()
        asr_layout.addLayout(asr_row)

        layout.addWidget(asr_group)
        layout.addStretch()

        # 初始化麦克风列表
        self._refresh_mic_devices()

    def init_about_page(self, page):
        """初始化关于页面"""
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignCenter)

        # 应用名称
        title_label = QLabel(f"{APP_DISPLAY_NAME} QuickSpeak")
        title_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: #4A90E2;
            margin-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 版本号
        version_label = QLabel(f"版本 {APP_VERSION}")
        version_label.setStyleSheet("""
            font-size: 14px;
            color: #666666;
            margin-bottom: 20px;
        """)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # 作者信息
        author_label = QLabel(f"作者: {APP_AUTHOR}")
        author_label.setStyleSheet("""
            font-size: 13px;
            color: #555555;
            margin-bottom: 30px;
        """)
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        # 分隔线
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #dcdcdc;")
        layout.addWidget(line)

        # 链接区域
        links_layout = QVBoxLayout()
        links_layout.setSpacing(15)
        links_layout.setContentsMargins(0, 20, 0, 0)

        # 主页链接
        homepage_btn = QPushButton("项目主页")
        homepage_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A90E2;
                border: none;
                font-size: 13px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #285A8C;
            }
        """)
        homepage_btn.clicked.connect(lambda: self._open_url("https://github.com/yourusername/writervoicedown"))
        links_layout.addWidget(homepage_btn, alignment=Qt.AlignCenter)

        # 隐私政策
        privacy_btn = QPushButton("隐私政策")
        privacy_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A90E2;
                border: none;
                font-size: 13px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #285A8C;
            }
        """)
        privacy_btn.clicked.connect(lambda: self._show_privacy_policy())
        links_layout.addWidget(privacy_btn, alignment=Qt.AlignCenter)

        # 许可证
        license_btn = QPushButton("许可证 (MIT)")
        license_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #4A90E2;
                border: none;
                font-size: 13px;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #285A8C;
            }
        """)
        license_btn.clicked.connect(lambda: self._show_license())
        links_layout.addWidget(license_btn, alignment=Qt.AlignCenter)

        layout.addLayout(links_layout)
        layout.addStretch()

    def _open_url(self, url):
        """打开 URL"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl(url))

    def _show_privacy_policy(self):
        """显示隐私政策"""
        QMessageBox.information(
            self,
            "隐私政策",
            f"""{APP_NAME} 隐私政策

1. 数据收集
   - 本地模式：所有录音和识别均在本地完成，不会上传任何数据
   - 云端模式：使用豆包 API 时，音频数据会上传至字节跳动服务器进行识别

2. 数据存储
   - 配置文件保存在 data/config.json
   - 临时录音文件保存在 data/temp/ 目录
   - 程序退出时会自动清理临时文件

3. 第三方服务
   - 豆包 API：仅在云端模式下使用，遵循字节跳动的隐私政策
   - 本地后端：完全本地运行，无外部依赖

4. 用户权利
   - 您可以随时在设置中切换本地/云端模式
   - 您可以删除 data/ 目录中的所有数据

如有隐私相关问题，请联系项目维护者。"""
        )

    def _show_license(self):
        """显示许可证"""
        QMessageBox.information(
            self,
            "许可证",
            f"""{APP_NAME} - MIT 许可证

Copyright (c) 2026 {APP_AUTHOR}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
        )

    def _refresh_mic_devices(self):
        """刷新麦克风设备列表"""
        from audio_recorder import AudioRecorder
        devices = AudioRecorder.get_input_devices()
        self.combo_mic.clear()
        self.combo_mic.addItem("系统默认", "")
        for dev in devices:
            self.combo_mic.addItem(dev['name'], dev['index'])

        # 恢复之前选择的设备
        saved_device = self.settings.get("microphone_device", "")
        if saved_device:
            for i in range(self.combo_mic.count()):
                if str(self.combo_mic.itemData(i)) == str(saved_device):
                    self.combo_mic.setCurrentIndex(i)
                    break

    def _test_mic(self):
        """测试麦克风"""
        if self._mic_test_thread and self._mic_test_thread.isRunning():
            self._mic_test_thread.stop()
            self._mic_test_thread.wait()
            self.btn_test_mic.setText("测试麦克风")
            self.progress_mic.setValue(0)
            return

        device_data = self.combo_mic.currentData()
        device_index = int(device_data) if device_data != "" else None

        self.btn_test_mic.setText("停止测试")
        self.lbl_mic_status.setText("正在测试...")
        self.lbl_mic_status.setStyleSheet("font-size: 11px; color: #2196F3;")
        self.progress_mic.setValue(0)

        self._mic_test_thread = MicTestThread(device_index=device_index, duration=5.0, parent=self)
        self._mic_test_thread.level_updated.connect(self.progress_mic.setValue)
        self._mic_test_thread.finished_signal.connect(self._on_mic_test_finished)
        self._mic_test_thread.start()

    def _on_mic_test_finished(self, success, message):
        """麦克风测试完成"""
        self.btn_test_mic.setText("测试麦克风")
        if success:
            self.lbl_mic_status.setText("✓ " + message)
            self.lbl_mic_status.setStyleSheet("font-size: 11px; color: #4CAF50;")
        else:
            self.lbl_mic_status.setText("✗ " + message)
            self.lbl_mic_status.setStyleSheet("font-size: 11px; color: #f44336;")

    def _browse_save_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择默认保存目录",
            self.txt_save_folder.text() or os.path.expanduser("~/Documents")
        )
        if folder:
            self.txt_save_folder.setText(folder)

    def _toggle_capture_hotkey(self):
        if self._recording_hotkey:
            # 停止捕获
            self._recording_hotkey = False
            self.lbl_hotkey.setChecked(False)
            self.lbl_hotkey.setText(self._captured_key if self._captured_key else "未设置")
        else:
            # 开始捕获
            self._recording_hotkey = True
            self.lbl_hotkey.setText("请按键...")
            self.lbl_hotkey.setChecked(True)
            self._start_key_capture()

    def _start_key_capture(self):
        """使用 pynput 捕获单个按键"""
        import threading

        def _capture():
            from pynput import keyboard

            def on_press(key):
                key_name = self._key_to_str(key)
                if key_name:
                    self._captured_key = key_name
                # 停止监听
                return False

            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()

            # 回到主线程更新 UI
            from PySide6.QtCore import QTimer
            QTimer.singleShot(0, self._finish_capture)

        threading.Thread(target=_capture, daemon=True).start()

    def _finish_capture(self):
        self._recording_hotkey = False
        self.lbl_hotkey.setChecked(False)
        self.lbl_hotkey.setText(self._captured_key if self._captured_key else "未设置")

    @staticmethod
    def _key_to_str(key):
        """将 pynput key 对象转换为可读字符串"""
        from pynput import keyboard
        if isinstance(key, keyboard.Key):
            # 特殊键
            name = key.name
            special_map = {
                "ctrl_l": "Ctrl(左)", "ctrl_r": "Ctrl(右)",
                "alt_l": "Alt(左)", "alt_r": "Alt(右)",
                "shift_l": "Shift(左)", "shift_r": "Shift(右)",
                "space": "空格", "tab": "Tab",
                "enter": "Enter", "backspace": "退格",
                "caps_lock": "CapsLock", "esc": "Esc",
                "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
                "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
                "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",
                "insert": "Insert", "delete": "Delete",
                "home": "Home", "end": "End",
                "page_up": "PageUp", "page_down": "PageDown",
                "up": "上", "down": "下", "left": "左", "right": "右",
            }
            return special_map.get(name, name.upper())
        elif isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.upper()
            elif key.vk:
                return f"VK{key.vk}"
        return None

    def _on_save(self):
        """收集设置并返回"""
        self.result_settings = {
            "save_folder": self.txt_save_folder.text().strip(),
            "hotkey_enabled": self.chk_hotkey.isChecked(),
            "hotkey_key": self._captured_key,
            "microphone_device": self.combo_mic.currentData(),
        }

        # ASR provider
        asr_data = self.combo_asr.currentData()
        if asr_data == "doubao":
            self.result_settings["asr_provider"] = "doubao"
            self.result_settings["local_model"] = "qwen"
        elif asr_data == "qwen":
            self.result_settings["asr_provider"] = "local"
            self.result_settings["local_model"] = "qwen"

        self.accept()

    def get_settings(self):
        return getattr(self, 'result_settings', {})

    def closeEvent(self, event):
        """关闭时停止麦克风测试"""
        if self._mic_test_thread and self._mic_test_thread.isRunning():
            self._mic_test_thread.stop()
            self._mic_test_thread.wait()
        super().closeEvent(event)
