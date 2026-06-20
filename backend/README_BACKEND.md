# QuickSpeak Backend v1.0.2

这是“说记 QuickSpeak”的本地 Qwen3-ASR 后端发行包，不包含模型文件。

## Windows 快速启动

1. 安装 Python 3.10 或 3.11 x64，并在安装时勾选 `Add Python to PATH`。
2. 双击 `start_backend.bat`。
3. 首次运行会自动创建 `.venv` 并安装依赖。
4. 模型缺失时选择下载源：
   - 输入 `1`：ModelScope，推荐中国大陆网络使用。
   - 输入 `2`：Hugging Face，推荐国际网络使用。
5. 下载完成后，服务会自动启动在 `http://localhost:8000`。

模型约 3.4 GB，保存在 `models/Qwen3-ASR-1.7B`。该目录可删除后重新下载，也可以整体迁移到另一台机器。

## 手动运行

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-backend.txt
.venv\Scripts\python download_model.py
.venv\Scripts\python main.py
```

API：

- `GET /v1/models`
- `POST /v1/chat/completions`

Whisper 自 v1.0.1 起已舍弃，不再包含相关模型、依赖或 API。
