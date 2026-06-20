================================================================================
                          WriteVoiceDown v1.0.0
================================================================================

【产品介绍】
WriteVoiceDown 是一款语音转文字工具，支持本地识别和云端识别两种模式。
- 本地模式：完全离线，数据不上传，隐私安全
- 云端模式：使用豆包 API，识别更准确

================================================================================
【快速开始】
================================================================================

1. 首次运行
   - 双击 WriteVoiceDown.exe 启动程序
   - 程序会在同目录下创建 data 文件夹存放配置和临时文件

2. 配置 API Key（云端模式）
   - 点击界面右上角"设置"按钮
   - 在"识别引擎"中选择"豆包 API"
   - 在设置界面输入您的 API Key
   - 点击"保存"

3. 开始录音识别
   - 点击"开始录音"按钮
   - 说话完毕后点击"停止录音"
   - 等待识别结果显示在文本框中
   - 可以点击"复制"按钮复制文本

4. 使用快捷键（可选）
   - 在设置中启用"全局快捷键录音"
   - 设置您喜欢的快捷键（如 Ctrl+Space）
   - 按住快捷键开始录音，松开自动停止并识别

================================================================================
【功能特性】
================================================================================

✓ 语音识别
  - 支持本地千问/Whisper 模型
  - 支持豆包云端 API
  - 自动检测音频格式（WAV/MP3/M4A/FLAC 等）

✓ 录音控制
  - 手动开始/停止录音
  - 全局快捷键按住说话
  - 麦克风设备选择和测试
  - 实时音量波形显示

✓ 文本编辑
  - 识别结果可直接编辑
  - 支持富文本格式（加粗、斜体、下划线）
  - 可导入文本文件
  - 可保存为 TXT 或 Word 文档

✓ 数据安全
  - 本地模式数据完全离线
  - 临时文件自动清理
  - 配置统一存储在 data 目录

✓ 其他功能
  - 系统托盘最小化
  - 自动复制识别结果
  - 创作模式（连续识别）
  - 自动保存未导出内容

================================================================================
【目录结构】
================================================================================

WriteVoiceDown/
├── WriteVoiceDown.exe      # 主程序
├── README.txt              # 本说明文件
├── data/                   # 数据目录（自动创建）
│   ├── config.json         # 配置文件
│   └── temp/               # 临时文件目录
├── _internal/              # 运行时依赖（勿删除）
└── icon.ico                # 程序图标

================================================================================
【配置说明】
================================================================================

配置文件位置：data/config.json

配置项说明：
{
  "doubao_api_key": "您的豆包 API Key",
  "local_backend_url": "http://localhost:8000",  // 本地后端地址
  "asr_provider": "doubao",                      // doubao 或 local
  "local_model": "qwen",                         // qwen 或 whisper
  "save_folder": "",                             // 默认保存目录
  "hotkey_enabled": false,                       // 是否启用快捷键
  "hotkey_key": "",                              // 快捷键名称
  "microphone_device": ""                        // 麦克风设备名称或索引
}

================================================================================
【本地后端部署（可选）】
================================================================================

如果您需要使用本地识别模式：

1. 安装后端依赖
   pip install fastapi uvicorn transformers torch torchaudio

2. 启动后端服务
   python backend/main.py

3. 配置前端
   - 在设置中选择"本地千问"或"本地 Whisper"
   - 确保后端地址为 http://localhost:8000

注意：本地模式需要较高的硬件配置（建议 16GB 内存，GPU 加速更佳）

================================================================================
【常见问题】
================================================================================

Q: 程序无法启动？
A: 请确保系统已安装 Visual C++ Redistributable 2015-2022

Q: 识别失败，提示"API Key 无效"？
A: 请检查设置中的 API Key 是否正确，或网络连接是否正常

Q: 本地模式提示"后端未启动"？
A: 请先启动本地后端服务（python backend/main.py）

Q: 录音没有声音？
A: 在设置中点击"测试麦克风"，检查是否选择了正确的麦克风设备

Q: 如何备份配置？
A: 复制 data/config.json 文件即可

Q: 程序异常退出？
A: 临时文件会自动清理，重启程序即可

================================================================================
【隐私政策】
================================================================================

本地模式：
- 所有录音和识别均在本地完成
- 不会上传任何数据到外部服务器
- 临时文件在程序退出时自动删除

云端模式：
- 使用豆包 API 进行识别
- 音频数据会上传至字节跳动服务器
- 遵循字节跳动的隐私政策

您可以在设置中随时切换识别模式。

================================================================================
【许可证】
================================================================================

MIT License

Copyright (c) 2026 WriteVoiceDown Team

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
SOFTWARE.

================================================================================
【技术支持】
================================================================================

如有问题或建议，请访问项目主页：
https://github.com/yourusername/writervoicedown

================================================================================
