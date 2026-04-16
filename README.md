# 快说 (KuaiShuo) - ASR 桌面悬浮窗

这是一个基于 Python + PySide6 的现代化、轻量级桌面悬浮窗应用。
不仅包含了一个小巧方便的**前端界面**，还集成了一个开箱即用的**后端服务**，专门适配并调用阿里云开源的 **Qwen3-ASR-1.7B** 语音识别模型。

## 核心功能

- **小巧悬浮窗**：现代化 UI，简洁淡蓝色风格，支持置顶、右下角拖动调整大小。
- **一键录音与导入**：支持麦克风一键录音（带计时器），也支持导入本地音频文件进行识别。
- **自动转写**：支持调用本地部署的 Qwen3-ASR 接口，速度快、准确率高。
- **结果管理**：支持识别结果追加、一键复制、保存录音文件以及保存文本为 `TXT` 文件。
- **灵活设置**：界面内置设置按钮（⚙），随时修改调用的 API 接口地址。

---

## 🚀 后端服务使用指南 (Qwen3-ASR-1.7B)

本项目自带了一个完全适配前端的轻量级后端服务（位于 `backend/` 目录下），它基于 FastAPI 构建，提供兼容 OpenAI 格式的 API 接口，底层使用 `qwen-asr` 官方库进行推理。

### 1. 安装依赖
进入项目根目录，安装项目所需的全部环境（前端界面与后端模型依赖）：
```bash
pip install -r requirements.txt
```

### 2. 下载本地模型
后端为了保证离线可用并避免网络波动，采用完全本地化加载。请先执行下载脚本，它会通过 ModelScope（魔搭社区）将模型拉取到 `backend/models/Qwen3-ASR-1.7B` 目录中（约 3.4GB）：
```bash
python backend/download_model.py
```

### 3. 启动后端服务
模型下载完成后，直接启动后端：
```bash
python backend/main.py
```
> **提示**：服务默认会在 `http://localhost:8000` 启动。启动时会自动加载模型到 GPU（如果可用）或 CPU。出现 `Model loaded successfully!` 即表示启动成功。

---

## 🚀 前端界面使用指南

### 2. 运行前端悬浮窗
（由于环境已统一安装，您可以直接运行）
```bash
python app/main.py
```
> **提示**：启动后，您可以点击界面上的 ⚙（齿轮）按钮，确认或修改后端 API 地址（默认为 `http://localhost:8000/v1`）。
> - 点击 `—`：窗口折叠到任务栏。
> - 点击 `×`：窗口最小化隐藏到系统托盘（右下角电脑图标），双击图标恢复，右键图标彻底退出。

---

## 📦 如何打包前端为独立的 EXE 文件？

如果你想将前端界面打包为免安装 Python 环境的程序，你可以使用自动化打包脚本。

**在 Windows 上，只需要双击运行根目录下的：**
> **`build_exe.bat`**

脚本会自动清理缓存并使用 `PyInstaller` 将项目打包。打包成功后，你可以在 **`dist/ASR_Floating_App/`** 目录下找到 **`ASR_Floating_App.exe`**。

---

## 📚 引用与参考资料

本项目的后端语音识别能力由阿里云通义实验室开源的 **Qwen3-ASR** 模型提供支持。Qwen3-ASR 是一个支持 52 种语言和方言的多语种语音识别系统。

- **官方技术博客 / 论文**：[Qwen3-ASR: Alibaba's Open-Source Speech Recognition System](https://qwen-ai.com/qwen-asr/)
- **HuggingFace 仓库**：[Qwen/Qwen3-ASR-1.7B](https://huggingface.co/Qwen/Qwen3-ASR-1.7B)
- **ModelScope (魔搭) 仓库**：[Qwen/Qwen3-ASR-1.7B](https://modelscope.cn/models/qwen/qwen3-asr-1.7b)
- **GitHub 开源代码库**：[QwenLM/Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR)
