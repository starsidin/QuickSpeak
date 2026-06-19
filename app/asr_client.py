import requests
import threading
import base64
import uuid
import time
import json
from PySide6.QtCore import QObject, Signal

class BaseASRClient(QObject):
    """
    ASR 客户端基类，定义统一的信号接口
    """
    request_started = Signal()
    request_finished = Signal(str)  # 成功返回识别文本
    request_failed = Signal(str)    # 失败返回错误信息
    backend_status = Signal(bool)   # 发送后端状态检查结果

    def check_health(self):
        pass

    def transcribe(self, wav_path: str):
        pass


class LocalASRClient(BaseASRClient):
    """
    本地后端 ASR 客户端，调用本地 FastAPI 服务（支持千问/Whisper）
    """
    def __init__(self, backend_url: str = "http://localhost:8000", model: str = "qwen"):
        super().__init__()
        self.backend_url = backend_url.rstrip("/")
        self.model = model

    def check_health(self):
        def _check():
            try:
                resp = requests.get(f"{self.backend_url}/models", timeout=5)
                if resp.status_code == 200:
                    self.backend_status.emit(True)
                else:
                    self.backend_status.emit(False)
            except Exception:
                self.backend_status.emit(False)
        threading.Thread(target=_check, daemon=True).start()

    def _parse_json_response(self, resp):
        try:
            return resp.json()
        except ValueError:
            text = resp.text.strip()
            if len(text) > 3 and text[:3].isdigit():
                try:
                    return json.loads(text[3:].strip())
                except ValueError:
                    pass
            preview = text[:500] if text else "<empty response>"
            raise ValueError(f"后端返回的不是标准 JSON: HTTP {resp.status_code} - {preview}")

    def _extract_error_detail(self, resp):
        try:
            data = self._parse_json_response(resp)
            return data.get("detail", resp.text)
        except ValueError:
            return resp.text[:500] if resp.text else f"HTTP {resp.status_code}"

    def _candidate_urls(self, endpoint):
        base = self.backend_url.rstrip("/")
        endpoint = endpoint.lstrip("/")
        urls = [f"{base}/{endpoint}"]
        if base.rstrip("/").split("/")[-1] != "v1" and not endpoint.startswith("v1/"):
            urls.append(f"{base}/v1/{endpoint}")
        elif endpoint.startswith("v1/"):
            urls.append(f"{base}/{endpoint[3:]}")
        seen = set()
        return [url for url in urls if not (url in seen or seen.add(url))]

    def _post_json_with_fallback(self, endpoints, payload):
        last_resp = None
        for endpoint in endpoints:
            for url in self._candidate_urls(endpoint):
                resp = requests.post(url, json=payload, timeout=300)
                last_resp = resp
                if resp.status_code not in (404, 405):
                    return resp
        return last_resp

    def transcribe(self, wav_path: str):
        self.request_started.emit()

        def _process():
            try:
                with open(wav_path, "rb") as f:
                    audio_data = base64.b64encode(f.read()).decode("utf-8")

                if self.model == "whisper":
                    # Whisper 使用 /v1/audio/transcriptions 端点
                    resp = self._post_json_with_fallback(
                        ["v1/audio/transcriptions", "audio/transcriptions"],
                        {"audio_data": audio_data, "format": "wav"}
                    )
                    if resp.status_code == 200:
                        result = self._parse_json_response(resp)
                        self.request_finished.emit(result.get("text", ""))
                    else:
                        detail = self._extract_error_detail(resp)
                        self.request_failed.emit(f"本地 Whisper 转写失败: {detail}")
                else:
                    # 千问使用 /chat/completions 端点
                    payload = {
                        "model": "Qwen3-ASR-1.7B",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "audio_url",
                                        "audio_url": {
                                            "url": f"data:audio/wav;base64,{audio_data}"
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                    resp = self._post_json_with_fallback(
                        ["chat/completions", "v1/chat/completions"],
                        payload
                    )
                    if resp.status_code == 200:
                        result = self._parse_json_response(resp)
                        choices = result.get("choices", [])
                        if choices:
                            text = choices[0].get("message", {}).get("content", "")
                            self.request_finished.emit(text)
                        else:
                            self.request_failed.emit("本地千问返回为空")
                    else:
                        detail = self._extract_error_detail(resp)
                        self.request_failed.emit(f"本地千问转写失败: {detail}")

            except Exception as e:
                self.request_failed.emit(f"本地转写失败: {str(e)}")

        threading.Thread(target=_process, daemon=True).start()


class DoubaoASRClient(BaseASRClient):
    """
    豆包 ASR 客户端模块，支持提交任务-查询结果流程
    """
    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key or ""
        self.resource_id = "volc.seedasr.auc"
        self.submit_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/submit"
        self.query_url = "https://openspeech.bytedance.com/api/v3/auc/bigmodel/query"

    def check_health(self):
        if self.api_key:
            self.backend_status.emit(True)
        else:
            self.backend_status.emit(False)

    def transcribe(self, wav_path: str):
        self.request_started.emit()
    
        def _process():
            try:
                if not self.api_key:
                    self.request_failed.emit("未配置 Doubao API Key")
                    return
    
                # 1. 准备音频数据：支持 URL 或本地文件 (Base64)
                audio_payload = {"format": "wav"}
                if wav_path.startswith(("http://", "https://")):
                    audio_payload["url"] = wav_path
                else:
                    try:
                        with open(wav_path, "rb") as f:
                            audio_payload["data"] = base64.b64encode(f.read()).decode("utf-8")
                    except Exception as e:
                        self.request_failed.emit(f"读取本地音频失败: {str(e)}")
                        return
    
                task_id = str(uuid.uuid4())
                
                # 2. 提交任务
                headers = {
                    "X-Api-Key": self.api_key,
                    "X-Api-Resource-Id": self.resource_id,
                    "X-Api-Request-Id": task_id,
                    "X-Api-Sequence": "-1",
                    "Content-Type": "application/json"
                }
                payload = {
                    "user": {
                        "uid": self.api_key[:8] or "flowagent"
                    },
                    "audio": audio_payload,
                    "request": {
                        "model_name": "bigmodel",
                        "enable_itn": True
                    }
                }
                
                submit_resp = requests.post(self.submit_url, headers=headers, json=payload, timeout=30)

                if submit_resp.status_code != 200:
                    self.request_failed.emit(f"提交任务失败: HTTP {submit_resp.status_code} - {submit_resp.text}")
                    return
    
                # 3. 轮询结果
                max_retries = 60 # 最多等待 5 分钟 (每 5 秒一次)
                for i in range(max_retries):
                    time.sleep(5)
                    query_headers = {
                        "X-Api-Key": self.api_key,
                        "X-Api-Resource-Id": self.resource_id,
                        "X-Api-Request-Id": task_id
                    }
                    query_resp = requests.post(self.query_url, headers=query_headers, json={}, timeout=30)
                    
                    if query_resp.status_code == 200:
                        res_json = query_resp.json()
                        result = res_json.get("result")
                        if result and "text" in result:
                            self.request_finished.emit(result["text"])
                            return
                    else:
                        # 如果是 404 或类似，可能是任务还在处理中，继续轮询
                        pass
                
                self.request_failed.emit("识别超时，请稍后在控制台查看结果")
    
            except Exception as e:
                self.request_failed.emit(f"豆包转写失败: {str(e)}")
    
        threading.Thread(target=_process, daemon=True).start()
