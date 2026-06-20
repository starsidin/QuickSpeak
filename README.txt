================================================================================
                         说记 QuickSpeak v1.0.1
================================================================================

【适用环境】
  Windows 10/11 x64。此版本已打包 Python 和桌面端运行依赖，无需安装 Python。

【快速开始】
  1. 解压整个 QuickSpeak-v1.0.1-Windows-x64.zip。
  2. 双击 QuickSpeak\QuickSpeak.exe。
  3. 云端识别：在“设置”中填写豆包 API Key，需要联网。
  4. 本地识别：先部署 QuickSpeak-Backend-v1.0.1，再将后端地址设为
     http://localhost:8000。

【注意】
  - 不要只复制 QuickSpeak.exe；_internal 目录是必需的运行依赖。
  - data 目录用于保存本机配置和临时文件，会在首次运行时自动创建。
  - Whisper 自 v1.0.1 起已舍弃；界面中仅保留禁用标记，不能选择。
  - 本地后端只支持 Qwen3-ASR-1.7B。

【目录结构】
  QuickSpeak/
  ├── QuickSpeak.exe
  ├── README.txt
  ├── icon.ico
  ├── icon.png
  └── _internal/

【隐私】
  - 豆包模式会将音频发送到对应云端 API。
  - Qwen 本地模式由用户自己的 QuickSpeak 后端处理。
  - API Key 只保存在本机 data/config.json，不包含在发布包中。

项目主页：https://github.com/starsidin/QuickSpeak
Copyright (c) 2026 Ranklee Studio
