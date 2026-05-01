# WriteSpeakDown - ASR 桌面悬浮窗 v1.0.1 

[English Version](README_EN.md)

这是一个基于 Python + PySide6 的现代化、轻量级桌面悬浮窗应用。
不仅包含了一个小巧方便的**前端界面**，还附带了一个**简单的后端服务使用案例**，专门适配并调用阿里开源的 **Qwen3-ASR-1.7B** 语音识别模型。

## 🌟 最新版本更新 (v1.0.1)

- **新增富文本编辑器（创作模式）**：
  - 点击“创作模式”按钮，悬浮窗将自动放大，为您提供宽敞的编辑区域。
  - 在创作模式下，识别的文本将**自动保留历史记录**并追加到末尾。
  - 提供富文本编辑工具栏：支持修改**加粗**、*斜体*、<ins>下划线</ins>以及**调节字体大小**。
  - 支持将带有格式的文本直接**保存为 Word (`.docx`)** 文件或普通的 TXT 文件。
  - 为防止误操作，在开始录音时会自动禁用“退出创作”按钮，退出创作模式时会弹出确认清空提示。
- **普通模式优化**：不再默认堆叠历史记录，每次识别只显示最新的一句话，保持界面极简。

## 💻 推荐设备与系统要求

### 仅前端（连接远程后端）

如果仅运行前端悬浮窗界面，而后端服务部署在其他机器上，前端本身非常轻量：

- **系统内存 (RAM)**：**4g** 即可
- **显存 (VRAM)**：**无要求**
- **操作系统**：Windows / macOS / Linux 均可

### 前后端同机部署

如果**前后端都在同一台设备上运行**（即本地加载 Qwen3-ASR-1.7B 模型进行推理），设备需要满足以下要求：

- **系统内存 (RAM)**：至少需要 **4GB** 可用内存
- **显存 (VRAM)**：至少需要 **4GB** 显存（推荐使用 GPU，CPU 推理亦可但较慢）
- **运行环境建议**：
  - **Linux 环境（推荐）**：强烈建议将后端部署在 Linux 或 Docker 上，并使用 **vLLM** 进行推理，速度显著优于 Windows
  - **Windows 环境**：在 Windows 上运行本地模型推理速度相对较慢，仅适合测试体验

***

## 核心功能

### 🎤 录音与识别
- **一键录音**：点击开始/停止录音，带实时计时器显示（`MM:SS`）
- **取消录音**：录音过程中可随时取消，不触发识别
- **多麦克风支持**：在设置中可自由切换输入设备
- **自动转写**：录音结束后自动调用 Qwen3-ASR 接口进行语音识别
- **导入音频**：支持导入本地音频文件（`.wav` `.mp3` `.flac` `.ogg` `.m4a`）进行识别

### ✏️ 结果编辑与管理
- **可编辑文本框**：识别结果可直接在界面中编辑修改
- **清空**：一键清空当前文本
- **复制**：手动复制识别结果到系统剪贴板
- **自动复制**：开启后每次识别完成自动将结果复制到剪贴板（普通模式下生效）
- **保存录音**：将当前录音保存为 `.wav` 文件
- **保存文本**：将编辑后的文本保存为 `.txt` 文件

### 🎨 创作模式（富文本编辑器）
- **窗口放大**：进入创作模式后悬浮窗自动扩展为更大的编辑区域
- **历史记录累积**：创作模式下每次识别的文本自动追加到末尾（保留历史）
- **富文本格式**：
  - **加粗** / *斜体* / <u>下划线</u>
  - 字号调节（8pt ~ 72pt）
- **导入文本**：支持导入 `.txt` 和 `.docx`（Word）文件，保留原格式
- **导出 Word**：将带格式的文本保存为 `.docx` 文件
- **导出 TXT**：将纯文本保存为 `.txt` 文件
- **防误操作**：录音期间自动禁用"退出创作"按钮；退出创作模式时弹出确认提示

### 🖥️ 界面交互
- **悬浮窗置顶**：始终保持在所有窗口之上，不掉落
- **无边框拖拽**：任意位置按住鼠标拖拽移动窗口
- **右下角缩放**：右下角拖拽手柄自由调整窗口大小
- **折叠到任务栏**：点击 `—` 最小化到任务栏
- **系统托盘驻留**：点击 `×` 隐藏到系统托盘（右下角图标），双击托盘图标恢复，右键彻底退出
- **设置面板**：点击 ⚙ 齿轮按钮，可修改后端 API 地址和选择麦克风设备，修改后自动保存并持久化
- **后端健康监测**：启动时自动检测后端连接状态，界面实时显示

***

## 🚀 后端服务使用指南 (Qwen3-ASR-1.7B)

本项目在 `backend/` 目录下附带了一个基于 FastAPI 构建的**简单后端服务使用案例**，提供兼容 OpenAI 格式的 API 接口，底层使用 `qwen-asr` 官方库进行推理。

> ⚠️ **重要提示**：此后端仅为演示和本地测试用途，**不建议直接用于生产环境**。在 Windows 上运行时，由于推理效率较低，速度可能会明显偏慢。如需在生产环境或高性能场景下使用，建议参考下方推荐方案自行部署。

### 🌍 国内/国外用户的部署推荐

由于网络环境和访问速度的差异，针对不同地区的用户，我们推荐不同的模型下载与部署方式：

| 用户地区 | 推荐平台 | 说明 |
|---------|---------|------|
| 🇨🇳 **国内用户** | [**ModelScope（魔搭社区）**](https://modelscope.cn) | 国内访问速度快，下载稳定，推荐优先使用 |
| 🌐 **国外用户** | [**Hugging Face**](https://huggingface.co) | 海外节点覆盖广，下载速度更优 |

### 1. 安装依赖

进入项目根目录，安装项目所需的全部环境（前端界面与后端模型依赖）：

```bash
pip install -r requirements.txt
```

### 2. 下载模型（约 3.4GB）

根据你所在的地区，选择以下其中一种方式：

#### 🇨🇳 国内用户 — 通过 ModelScope 下载

使用项目内置的下载脚本，该脚本会从 [ModelScope 仓库](https://modelscope.cn/models/qwen/Qwen3-ASR-1.7B) 拉取模型到 `backend/models/Qwen3-ASR-1.7B` 目录：

```bash
python backend/download_model.py
```

#### 🌐 国外用户 — 通过 Hugging Face 下载

推荐使用 `huggingface-cli` 工具从 [Hugging Face 仓库](https://huggingface.co/Qwen/Qwen3-ASR-1.7B) 下载模型：

```bash
pip install huggingface_hub
huggingface-cli download Qwen/Qwen3-ASR-1.7B --local-dir backend/models/Qwen3-ASR-1.7B
```

### 3. 启动后端服务

模型下载完成后，直接启动后端：

```bash
python backend/main.py
```

> **提示**：服务默认会在 `http://localhost:8000` 启动。启动时会自动加载模型到 GPU（如果可用）或 CPU。出现 `Model loaded successfully!` 即表示启动成功。

### 4. API 接口说明

后端提供 **OpenAI 兼容格式** 的 API 接口，方便与各类前端或工具对接。

#### 接口地址格式

前端连接后端时，设置中的 **API 地址** 需要填写到 `/v1` 层级，例如：

```
http://localhost:8000/v1
```

实际请求的完整路径由前端自动拼接：

| 功能 | 请求方法 | 完整路径 |
|------|---------|---------|
| 模型列表（健康检查） | `GET` | `{base_url}/models` → `http://localhost:8000/v1/models` |
| 语音识别转写 | `POST` | `{base_url}/chat/completions` → `http://localhost:8000/v1/chat/completions` |

#### 转写接口请求格式

请求体遵循 OpenAI Chat Completions 规范，音频通过 Base64 Data URL 传递：

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

返回格式：

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
        "content": "识别出的文本内容"
      },
      "finish_reason": "stop"
    }
  ]
}
```

***

## 🚀 前端界面使用指南

### 运行前端悬浮窗

（由于环境已统一安装，您可以直接运行）

```bash
python app/main.py
```

> **提示**：启动后，您可以点击界面上的 ⚙（齿轮）按钮，确认或修改后端 API 地址（默认为 `http://localhost:8000/v1`）。
>
> - 点击 `—`：窗口折叠到任务栏。
> - 点击 `×`：窗口最小化隐藏到系统托盘（右下角电脑图标），双击图标恢复，右键图标彻底退出。

***

## 📦 如何打包前端为独立的 EXE 文件？

如果你想将前端界面打包为免安装 Python 环境的程序，你可以使用自动化打包脚本。

**在 Windows 上，只需要双击运行根目录下的：**

> **`build_exe.bat`**

脚本会自动清理缓存并使用 `PyInstaller` 将项目打包。打包成功后，你可以在 **`dist/ASR_Floating_App/`** 目录下找到 **`ASR_Floating_App.exe`**。

***

## 📚 引用与参考资料

本项目的后端语音识别能力由阿里云通义实验室开源的 **Qwen3-ASR** 模型提供支持。Qwen3-ASR 是一个支持 52 种语言和方言的多语种语音识别系统。

- **官方技术博客 / 论文**：[Qwen3-ASR: Alibaba's Open-Source Speech Recognition System](https://qwen-ai.com/qwen-asr/)
- **HuggingFace 仓库**：[Qwen/Qwen3-ASR-1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B)
- **ModelScope (魔搭) 仓库**：[Qwen/Qwen3-ASR-1.7B](https://modelscope.cn/models/qwen/qwen3-asr-1.7b)
- **GitHub 开源代码库**：[QwenLM/Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)

