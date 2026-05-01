# WriteSpeakDown - ASR Desktop Floating Window v1.0.1

[中文版](README.md)

A modern, lightweight desktop floating window application built with Python + PySide6.
It includes a compact **frontend UI** and a **simple backend service example**, designed to work with Alibaba's open-source **Qwen3-ASR-1.7B** speech recognition model.

## 🌟 Latest Updates (v1.0.1)

- **Rich Text Editor (Creative Mode)**:
  - Click the "Creative Mode" button to expand the floating window into a spacious editing area.
  - In creative mode, transcribed text is **automatically appended** to preserve history.
  - Rich text editing toolbar: supports **Bold**, *Italic*, <u>Underline</u>, and **font size** adjustment.
  - Save formatted text directly as **Word (`.docx`)** or plain TXT files.
  - To prevent accidental operations, the "Exit Creative" button is disabled during recording; exiting creative mode prompts a confirmation dialog.
- **Normal Mode Optimization**: No longer accumulates history by default — only the latest transcribed sentence is displayed, keeping the interface minimal.

## 💻 System Requirements

### Frontend Only (Connecting to Remote Backend)

If you only run the frontend window and the backend service is deployed on another machine, the frontend itself is very lightweight:

- **RAM**: **500MB** is sufficient
- **VRAM**: **Not required**
- **OS**: Windows / macOS / Linux

### Frontend + Backend on the Same Machine

If both frontend and backend run on the same device (loading the Qwen3-ASR-1.7B model locally for inference), your device should meet:

- **RAM**: At least **4GB** available
- **VRAM**: At least **2GB** (GPU recommended; CPU inference is possible but slower)
- **Environment Recommendations**:
  - **Linux (Recommended)**: Deploy the backend on Linux or Docker with **vLLM** for significantly faster inference.
  - **Windows**: Running local model inference on Windows is relatively slow and only suitable for testing.

---

## Core Features

### 🎤 Recording & Transcription
- **One-Click Recording**: Start/stop recording with a real-time timer (`MM:SS`)
- **Cancel Recording**: Cancel recording at any time without triggering transcription
- **Multi-Microphone Support**: Switch input devices freely in Settings
- **Auto Transcription**: Automatically calls the Qwen3-ASR API after recording ends
- **Import Audio**: Import local audio files (`.wav` `.mp3` `.flac` `.ogg` `.m4a`) for transcription

### ✏️ Text Editing & Management
- **Editable Text Area**: Transcribed text can be edited directly in the interface
- **Clear**: One-click clear of the current text
- **Copy**: Manually copy transcribed text to the system clipboard
- **Auto Copy**: Automatically copy results to clipboard after each transcription (in normal mode)
- **Save Recording**: Save the current recording as a `.wav` file
- **Save as TXT**: Save edited text as a `.txt` file

### 🎨 Creative Mode (Rich Text Editor)
- **Expanded Window**: The floating window automatically enlarges when entering creative mode
- **History Accumulation**: Transcribed text is automatically appended to the end, preserving context
- **Rich Text Formatting**:
  - **Bold** / *Italic* / <u>Underline</u>
  - Font size adjustment (8pt – 72pt)
- **Import Text**: Import `.txt` and `.docx` (Word) files, preserving original formatting
- **Export as Word**: Save formatted text as a `.docx` file
- **Export as TXT**: Save plain text as a `.txt` file
- **Accident Prevention**: "Exit Creative" button is disabled during recording; exiting prompts a confirmation dialog

### 🖥️ UI & Interaction
- **Always on Top**: Stays above all other windows
- **Frameless Drag**: Drag the window by holding anywhere on its surface
- **Resize Handle**: Drag the bottom-right corner grip to resize freely
- **Minimize to Taskbar**: Click `—` to minimize to the taskbar
- **System Tray**: Click `×` to hide to the system tray (bottom-right tray icon); double-click to restore, right-click to quit
- **Settings Panel**: Click the ⚙ gear button to modify the backend API URL and select a microphone device — changes are automatically saved
- **Backend Health Monitoring**: Automatically checks the backend connection status on startup, shown in real time

---

## 🚀 Backend Setup Guide (Qwen3-ASR-1.7B)

The project includes a simple backend example in the `backend/` directory, built with FastAPI, providing an OpenAI-compatible API interface powered by the `qwen-asr` library.

> ⚠️ **Important**: This backend is intended for **demonstration and local testing only** — **not recommended for production use**. Running on Windows may be noticeably slow due to limited inference efficiency. For production or high-performance scenarios, please refer to the recommended deployment solutions below.

### 🌍 Platform Recommendations by Region

Due to differences in network access speed, we recommend different platforms for model downloading and deployment:

| Region | Recommended Platform | Notes |
|--------|---------------------|-------|
| 🇨🇳 **Users in China** | [**ModelScope**](https://modelscope.cn) | Fast domestic access, stable downloads — recommended |
| 🌐 **International Users** | [**Hugging Face**](https://huggingface.co) | Wide global CDN coverage, better download speed |

### 1. Install Dependencies

From the project root directory, install all required environments (frontend UI and backend model dependencies):

```bash
pip install -r requirements.txt
```

### 2. Download Model (~3.4 GB)

Choose based on your region:

#### 🇨🇳 Users in China — Download via ModelScope

Use the built-in download script, which pulls the model from the [ModelScope Repository](https://modelscope.cn/models/qwen/Qwen3-ASR-1.7B) to `backend/models/Qwen3-ASR-1.7B`:

```bash
python backend/download_model.py
```

#### 🌐 International Users — Download via Hugging Face

Use the `huggingface-cli` tool to download from the [Hugging Face Repository](https://huggingface.co/Qwen/Qwen3-ASR-1.7B):

```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen3-ASR-1.7B --local-dir backend/models/Qwen3-ASR-1.7B
```

### 3. Start Backend Service

After the model is downloaded, start the backend:

```bash
python backend/main.py
```

> **Tip**: The service starts at `http://localhost:8000` by default. The model is loaded automatically (to GPU if available, otherwise CPU). You should see `Model loaded successfully!` when ready.

### 4. API Reference

The backend provides an **OpenAI-compatible** API, making it easy to integrate with various frontends and tools.

#### Endpoint Format

When connecting the frontend to the backend, the **API URL** in Settings should include the `/v1` path, e.g.:

```
http://localhost:8000/v1
```

Actual request paths are constructed automatically by the frontend:

| Function | Method | Full Path |
|----------|--------|-----------|
| Model List (Health Check) | `GET` | `{base_url}/models` → `http://localhost:8000/v1/models` |
| Speech Transcription | `POST` | `{base_url}/chat/completions` → `http://localhost:8000/v1/chat/completions` |

#### Transcription Request Format

The request body follows the OpenAI Chat Completions specification, with audio transmitted as a Base64 Data URL:

```json
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "Qwen3-ASR-1.7B",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "audio_url",
          "audio_url": {
            "url": "data:audio/wav;base64,<BASE64_ENCODED_AUDIO>"
          }
        }
      ]
    }
  ]
}
```

Response format:

```json
{
  "id": "chatcmpl-xxxxx",
  "object": "chat.completion",
  "model": "Qwen3-ASR-1.7B",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Transcribed text content"
      },
      "finish_reason": "stop"
    }
  ]
}
```

---

## 🚀 Frontend Usage Guide

### Running the Frontend Window

(All environments are already installed, so you can run directly)

```bash
python app/main.py
```

> **Tip**: After launching, click the ⚙ (gear) button to verify or modify the backend API URL (default: `http://localhost:8000/v1`).
>
> - Click `—`: Minimize to the taskbar.
> - Click `×`: Hide to system tray (bottom-right icon). Double-click to restore, right-click to quit completely.

---

## 📦 Packaging the Frontend as a Standalone EXE

To package the frontend UI into a standalone executable without requiring a Python environment, use the automated packaging script.

**On Windows, simply double-click in the project root:**

> **`build_exe.bat`**

The script will automatically clean caches and use `PyInstaller` to package the project. After successful packaging, find **`ASR_Floating_App.exe`** in the **`dist/ASR_Floating_App/`** directory.

---

## 📚 References

The backend speech recognition capability is powered by Alibaba Tongyi Lab's open-source **Qwen3-ASR** model. Qwen3-ASR is a multilingual speech recognition system supporting 52 languages and dialects.

- **Official Tech Blog / Paper**: [Qwen3-ASR: Alibaba's Open-Source Speech Recognition System](https://qwen-ai.com/qwen-asr/)
- **HuggingFace Repository**: [Qwen/Qwen3-ASR-1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B)
- **ModelScope Repository**: [Qwen/Qwen3-ASR-1.7B](https://modelscope.cn/models/qwen/qwen3-asr-1.7b)
- **GitHub Source Code**: [QwenLM/Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)
