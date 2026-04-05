"""ChirpChunk 标准数据类"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import numpy as np


@dataclass
class ChirpChunk:
    """单个Chirp的标准数据块"""

    # 身份信息
    original_filename: str      # 原始文件名
    mic_id: int               # 麦克风编号 (5)
    wave_type: str            # PS/SV/SH/A0H/A0L
    chirp_index: int          # 1-10

    # 时间参数
    emission_time: float      # 发射时刻
    response_start: float     # 响应窗口开始
    response_end: float       # 响应窗口结束

    # 频率参数
    freq_start: float
    freq_end: float
    duration: float
    delay_min: float
    delay_max: float

    # 信号数据
    speaker_signal: Optional[np.ndarray] = None   # 喇叭模板
    mic_response: Optional[np.ndarray] = None    # 麦克风原始
    response_window: Optional[np.ndarray] = None  # 截取窗口

    # 处理状态
    status: str = 'extracted'  # extracted/matched/accumulated
    timestamp: str = ''         # 处理时间戳

    @property
    def chunk_id(self) -> str:
        """生成chunk标识"""
        return f"{self.original_filename}_mic{self.mic_id}_{self.wave_type}_{self.chirp_index:02d}"

    @property
    def wav_filename(self) -> str:
        """生成标准WAV文件名"""
        return f"{self.chunk_id}_{self.status}_{self.timestamp}.wav"

    def get_response_samples(self) -> tuple:
        """获取响应窗口样本范围 (start_sample, end_sample)"""
        sr = 192000
        start = int(self.response_start * sr)
        end = int(self.response_end * sr)
        return (start, end)
