import sounddevice as sd
import soundfile as sf
import queue
import threading
from PySide6.QtCore import QObject, Signal

class AudioRecorder(QObject):
    """
    后台录音模块，使用 QThread / QObject 处理录音逻辑，不阻塞主线程
    """
    recording_started = Signal()
    recording_stopped = Signal(str)  # 发送临时文件路径
    error_occurred = Signal(str)

    def __init__(self, temp_wav_path: str):
        super().__init__()
        self.temp_wav_path = temp_wav_path
        self.samplerate = 16000  # ASR 常用 16kHz
        self.channels = 1        # 单声道
        self.is_recording = False
        self._q = queue.Queue()
        self._thread = None

    def _audio_callback(self, indata, frames, time, status):
        """sounddevice 的音频回调，收集音频数据"""
        if status:
            print(status)
        self._q.put(indata.copy())

    def _record_thread(self):
        """实际执行录音的后台线程"""
        try:
            with sf.SoundFile(self.temp_wav_path, mode='w', samplerate=self.samplerate,
                              channels=self.channels, subtype='PCM_16') as file:
                with sd.InputStream(samplerate=self.samplerate, channels=self.channels,
                                    callback=self._audio_callback):
                    while self.is_recording or not self._q.empty():
                        try:
                            data = self._q.get(timeout=0.1)
                            file.write(data)
                        except queue.Empty:
                            pass
            self.recording_stopped.emit(self.temp_wav_path)
        except Exception as e:
            self.error_occurred.emit(f"录音出错: {str(e)}")
            self.is_recording = False

    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return
        self.is_recording = True
        self._q.queue.clear()
        self.recording_started.emit()
        self._thread = threading.Thread(target=self._record_thread, daemon=True)
        self._thread.start()

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        # _record_thread 结束时会发射 recording_stopped 信号
