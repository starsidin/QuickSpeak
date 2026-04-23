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
    recording_canceled = Signal()    # 录音被取消的信号
    error_occurred = Signal(str)

    def __init__(self, temp_wav_path: str, device_index: int = None):
        super().__init__()
        self.temp_wav_path = temp_wav_path
        self.samplerate = 16000  # ASR 常用 16kHz
        self.channels = 1        # 单声道
        self.is_recording = False
        self.is_canceled = False # 是否被取消标志
        self._q = queue.Queue()
        self._thread = None
        self.device_index = device_index

    @staticmethod
    def get_input_devices():
        """获取所有可用的输入设备（麦克风）"""
        devices = []
        try:
            device_list = sd.query_devices()
            for i, dev in enumerate(device_list):
                if dev['max_input_channels'] > 0:
                    devices.append({'index': i, 'name': dev['name']})
        except Exception as e:
            print(f"获取设备列表失败: {e}")
        return devices

    def set_device(self, device_index: int):
        """设置使用的麦克风设备索引"""
        self.device_index = device_index

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
                # 尝试使用指定的设备，如果不指定则使用系统默认设备
                with sd.InputStream(samplerate=self.samplerate, channels=self.channels,
                                    callback=self._audio_callback, device=self.device_index):
                    while self.is_recording or not self._q.empty():
                        # 如果在排空队列期间被取消了，直接跳出循环
                        if self.is_canceled:
                            break
                        try:
                            data = self._q.get(timeout=0.1)
                            file.write(data)
                        except queue.Empty:
                            pass
            
            # 根据标志判断是正常停止还是被取消
            if self.is_canceled:
                self.recording_canceled.emit()
            else:
                self.recording_stopped.emit(self.temp_wav_path)
        except Exception as e:
            self.error_occurred.emit(f"录音出错: {str(e)}")
            self.is_recording = False
            self.is_canceled = False

    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return
        self.is_recording = True
        self.is_canceled = False
        self._q.queue.clear()
        self.recording_started.emit()
        self._thread = threading.Thread(target=self._record_thread, daemon=True)
        self._thread.start()

    def stop_recording(self):
        """停止录音（正常停止，触发识别）"""
        self.is_recording = False
        self.is_canceled = False
        # _record_thread 结束时会发射 recording_stopped 信号

    def cancel_recording(self):
        """取消录音（不触发识别）"""
        self.is_recording = False
        self.is_canceled = True
        # _record_thread 结束时会发射 recording_canceled 信号
