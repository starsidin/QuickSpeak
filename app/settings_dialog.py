import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QFileDialog, QGroupBox,
    QMessageBox
)
from PySide6.QtCore import Qt


class SettingsDialog(QDialog):
    """设置对话框：默认保存目录、录音快捷键、ASR 引擎切换"""

    def __init__(self, parent=None, current_settings=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setMinimumSize(420, 380)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f9ff;
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
        """)

        self.settings = current_settings or {}
        self._recording_hotkey = False
        self._captured_key = self.settings.get("hotkey_key", "")

        self.init_ui()
        self.adjustSize()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

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
        self.combo_asr.addItem("本地 Whisper", "whisper")

        # 设置当前选项
        current_provider = self.settings.get("asr_provider", "doubao")
        current_model = self.settings.get("local_model", "qwen")
        if current_provider == "local":
            if current_model == "whisper":
                self.combo_asr.setCurrentIndex(2)
            else:
                self.combo_asr.setCurrentIndex(1)
        else:
            self.combo_asr.setCurrentIndex(0)

        asr_row.addWidget(self.combo_asr)
        asr_row.addStretch()
        asr_layout.addLayout(asr_row)

        layout.addWidget(asr_group)

        # --- 底部按钮 ---
        layout.addStretch()
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
        }

        # ASR provider
        asr_data = self.combo_asr.currentData()
        if asr_data == "doubao":
            self.result_settings["asr_provider"] = "doubao"
            self.result_settings["local_model"] = "qwen"
        elif asr_data == "qwen":
            self.result_settings["asr_provider"] = "local"
            self.result_settings["local_model"] = "qwen"
        elif asr_data == "whisper":
            self.result_settings["asr_provider"] = "local"
            self.result_settings["local_model"] = "whisper"

        self.accept()

    def get_settings(self):
        return getattr(self, 'result_settings', {})
