import requests
import json
import threading
import base64
import os
from PySide6.QtCore import QObject, Signal

from config import ASR_MODEL

def parse_asr_output(text: str):
    """
    解析 Qwen ASR 输出的格式
    去除 <|zh|> 等语言标签
    去除 "language Chinese<asr_text>" 这类特殊前缀
    """
    import re
    # 去除类似于 <|zh|> 的标签
    cleaned_text = re.sub(r'<\|.*?\|>', '', text)
    # 去除类似于 language Chinese<asr_text> 的前缀
    cleaned_text = re.sub(r'language\s+[a-zA-Z]+<asr_text>', '', cleaned_text, flags=re.IGNORECASE)
    # 额外清理可能的单独 <asr_text> 标签
    cleaned_text = re.sub(r'<asr_text>', '', cleaned_text, flags=re.IGNORECASE)
    
    return "unknown", cleaned_text.strip()

class ASRClient(QObject):
    """
    后台 ASR 客户端模块，封装 HTTP 请求不阻塞主线程
    """
    request_started = Signal()
    request_finished = Signal(str)  # 成功返回识别文本
    request_failed = Signal(str)    # 失败返回错误信息
    backend_status = Signal(bool)   # 发送后端状态检查结果

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.model_name = ASR_MODEL

    def check_health(self):
        """
        检查本地 ASR 服务健康状态
        接口：GET /v1/models
        """
        def _check():
            try:
                response = requests.get(f"{self.base_url}/models", timeout=3)
                if response.status_code == 200:
                    try:
                        # 尝试自动获取模型名称
                        if not self.model_name:
                            models_data = response.json().get("data", [])
                            if models_data:
                                self.model_name = models_data[0].get("id", "")
                    except Exception:
                        pass
                    self.backend_status.emit(True)
                else:
                    self.backend_status.emit(False)
            except Exception as e:
                self.backend_status.emit(False)

        threading.Thread(target=_check, daemon=True).start()

    def transcribe(self, wav_path: str):
        """
        调用 ASR API 进行转写
        遵循 Qwen ASR 1.7b 要求的格式: POST /v1/chat/completions
        """
        self.request_started.emit()

        def _request():
            try:
                # 把音频文件转成 base64 Data URL 格式或者直接传本地绝对路径
                # 很多 OpenAI 兼容层对于本地部署支持直接传 file:// 开头的路径
                # 或者通过 base64 传递: data:audio/wav;base64,XXXXX
                # 我们这里尝试转换为 base64 以确保兼容性，如果你的后端只认 URL 也可以改为 file:///...
                
                # 方式 1：使用 Base64 Data URL (更通用)
                with open(wav_path, "rb") as f:
                    audio_data = f.read()
                b64_encoded = base64.b64encode(audio_data).decode("utf-8")
                audio_url = f"data:audio/wav;base64,{b64_encoded}"
                
                # 方式 2：如果后端和前端在同一台机器上，有时直接传本地绝对路径也可以，比如 file:///E:/...
                # local_url = f"file:///{os.path.abspath(wav_path).replace(chr(92), '/')}"

                headers = {"Content-Type": "application/json"}
                data = {
                    "model": self.model_name or "qwen-audio",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "audio_url",
                                    "audio_url": {
                                        "url": audio_url
                                    },
                                }
                            ],
                        }
                    ]
                }
                
                # 请求 /v1/chat/completions
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=300  # Qwen ASR 比较耗时，设长一点
                )
                
                if response.status_code == 200:
                    res_json = response.json()
                    content = res_json['choices'][0]['message']['content']
                    # 解析结果
                    _, text = parse_asr_output(content)
                    self.request_finished.emit(text)
                else:
                    self.request_failed.emit(f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.request_failed.emit(f"请求失败: {str(e)}")

        threading.Thread(target=_request, daemon=True).start()
