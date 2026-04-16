import os
import time
import base64
import tempfile
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import torch

# 获取当前文件所在目录，指向本地模型目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_MODEL_DIR = os.path.join(BASE_DIR, "models", "Qwen3-ASR-1.7B")

model_instance = None

def load_model():
    """
    Load the Qwen3-ASR-1.7B model.
    """
    global model_instance
    if model_instance is not None:
        return model_instance
        
    if not os.path.exists(LOCAL_MODEL_DIR):
        raise RuntimeError(
            f"未找到本地模型目录 {LOCAL_MODEL_DIR}。\n"
            "请先执行 `python download_model.py` 下载模型！"
        )

    print(f"Loading model from local path: {LOCAL_MODEL_DIR}...")
    try:
        from qwen_asr import Qwen3ASRModel
    except ImportError:
        raise RuntimeError("qwen_asr is not installed. Please run `pip install -U qwen-asr`")
        
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    # Use bfloat16 or float16 if cuda is available, else float32
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        dtype = torch.bfloat16
    elif torch.cuda.is_available():
        dtype = torch.float16
    else:
        dtype = torch.float32
        
    print(f"Initializing model on {device} with dtype {dtype}...")
    model_instance = Qwen3ASRModel.from_pretrained(
        LOCAL_MODEL_DIR,
        dtype=dtype,
        device_map=device  # 强制指定设备
    )
    print(f"Model loaded successfully on {model_instance.device}!")
    return model_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load the model
    print("Starting up and loading the ASR model...")
    try:
        load_model()
    except Exception as e:
        print(f"Error loading model during startup: {e}")
        # Depending on requirements, you might want to raise the exception to stop the server
        # raise e
    yield
    # Shutdown: clean up if necessary
    print("Shutting down...")

app = FastAPI(title="Qwen3-ASR-1.7B OpenAI-Compatible Backend", lifespan=lifespan)

class ModelData(BaseModel):
    id: str

class ModelListResponse(BaseModel):
    data: List[ModelData]

@app.get("/v1/models", response_model=ModelListResponse)
@app.get("/models", response_model=ModelListResponse)
async def list_models():
    """
    Handle the frontend's health check and model discovery request.
    """
    return {"data": [{"id": "Qwen3-ASR-1.7B"}]}

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    
@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """
    Handle the frontend's ASR inference request in OpenAI /v1/chat/completions format.
    """
    try:
        asr_model = load_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")
    
    # 1. Extract audio URL or Base64 from the messages
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
        
        # 2. Decode base64 audio to a temporary file
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
                # 3. Transcribe audio
                results = asr_model.transcribe(
                    audio=tmp_path,
                    language=None # Automatically detect language
                )
                if results and len(results) > 0:
                    transcription_text = results[0].text
            finally:
                # Clean up the temporary file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
        else:
            # Maybe it's a direct file path or a remote URL
            print(f"Processing audio URL: {audio_url}")
            results = asr_model.transcribe(
                audio=audio_url,
                language=None
            )
            if results and len(results) > 0:
                transcription_text = results[0].text

        print(f"Transcription result: {transcription_text}")

        # 4. Format and return response compatible with OpenAI
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
    # Start the uvicorn server
    print("Starting Qwen3-ASR server on http://localhost:8000")
    print("You can access the server at: http://localhost:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
