import os
import time
import base64
import tempfile
from typing import List, Dict, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import torch

# 获取当前文件所在目录，指向本地模型目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_MODEL_DIR = os.path.join(BASE_DIR, "models", "Qwen3-ASR-1.7B")
qwen_model_instance = None

def load_qwen_model():
    """
    Load the Qwen3-ASR-1.7B model.
    """
    global qwen_model_instance
    if qwen_model_instance is not None:
        return qwen_model_instance
        
    if not os.path.exists(LOCAL_MODEL_DIR):
        raise RuntimeError(
            f"未找到本地模型目录 {LOCAL_MODEL_DIR}。\n"
            "请先执行 `python download_model.py` 下载模型！"
        )

    print(f"Loading Qwen model from local path: {LOCAL_MODEL_DIR}...")
    try:
        from qwen_asr import Qwen3ASRModel
    except ImportError:
        raise RuntimeError("qwen_asr is not installed. Please run `pip install -U qwen-asr`")
        
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        dtype = torch.bfloat16
    elif torch.cuda.is_available():
        dtype = torch.float16
    else:
        dtype = torch.float32
        
    print(f"Initializing Qwen model on {device} with dtype {dtype}...")
    qwen_model_instance = Qwen3ASRModel.from_pretrained(
        LOCAL_MODEL_DIR,
        dtype=dtype,
        device_map=device
    )
    print(f"Qwen model loaded successfully on {qwen_model_instance.device}!")
    return qwen_model_instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting QuickSpeak backend and loading Qwen ASR model...")

    try:
        load_qwen_model()
    except Exception as e:
        print(f"Error loading Qwen model: {e}")

    yield
    print("Shutting down...")

app = FastAPI(title="QuickSpeak Backend (Qwen3-ASR)", version="1.0.2", lifespan=lifespan)

class ModelData(BaseModel):
    id: str

class ModelListResponse(BaseModel):
    data: List[ModelData]

@app.get("/v1/models", response_model=ModelListResponse)
@app.get("/models", response_model=ModelListResponse)
async def list_models():
    return {
        "data": [
            {"id": "Qwen3-ASR-1.7B"},
        ]
    }

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]

def extract_qwen_text(results):
    if not results:
        return ""

    first = results[0] if isinstance(results, (list, tuple)) else results
    if isinstance(first, dict):
        text = first.get("text") or first.get("content") or first.get("transcription") or ""
    else:
        text = getattr(first, "text", None) or getattr(first, "content", None) or str(first)

    if not text:
        return ""

    try:
        from qwen_asr import parse_asr_output
        _language, parsed_text = parse_asr_output(text)
        return parsed_text or text
    except Exception:
        return text

@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """
    Qwen ASR: OpenAI /v1/chat/completions format.
    """
    try:
        asr_model = load_qwen_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load Qwen model: {str(e)}")

    try:
        content = req.messages[0].get('content', [])
        audio_url = None
        for item in content:
            if item.get('type') == 'audio_url':
                audio_url = item.get('audio_url', {}).get('url')
                break

        if not audio_url:
            raise ValueError("No audio_url found in the user messages")

        transcription_text = ""

        if audio_url.startswith("data:audio/"):
            parts = audio_url.split(",", 1)
            if len(parts) < 2:
                raise ValueError("Invalid Base64 audio_url format")

            encoded = parts[1]
            audio_data = base64.b64decode(encoded)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                print(f"Processing audio chunk: {tmp_path}")
                results = asr_model.transcribe(
                    audio=tmp_path,
                    language=None
                )
                transcription_text = extract_qwen_text(results)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
            print(f"Processing audio URL: {audio_url}")
            results = asr_model.transcribe(
                audio=audio_url,
                language=None
            )
            transcription_text = extract_qwen_text(results)

        print(f"Qwen transcription: {transcription_text}")

        return {
            "id": f"chatcmpl-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": req.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": transcription_text
                    },
                    "finish_reason": "stop"
                }
            ]
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")


if __name__ == "__main__":
    print("Starting QuickSpeak backend on http://localhost:8000")
    print("Available model: Qwen3-ASR-1.7B")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
