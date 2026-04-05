"""WAV 文件验证工具"""

from scipy.io import wavfile
from pathlib import Path
from typing import Tuple, Optional


class WAVValidator:
    """WAV 文件验证器"""

    EXPECTED_SAMPLE_RATE = 192000
    EXPECTED_CHANNELS = 3

    @classmethod
    def validate(cls, wav_path: Path) -> Tuple[bool, Optional[str]]:
        """
        验证 WAV 文件

        Returns:
            (is_valid, error_message)
        """
        try:
            sr, data = wavfile.read(wav_path)

            # 检查采样率
            if sr != cls.EXPECTED_SAMPLE_RATE:
                return False, f"采样率错误: 期望{cls.EXPECTED_SAMPLE_RATE}, 实际{sr}"

            # 检查通道数
            if data.ndim == 1:
                channels = 1
            else:
                channels = data.shape[1]
            if channels != cls.EXPECTED_CHANNELS:
                return False, f"通道数错误: 期望{cls.EXPECTED_CHANNELS}, 实际{channels}"

            return True, None

        except Exception as e:
            return False, f"读取文件失败: {e}"

    @classmethod
    def validate_duration(cls, wav_path: Path, expected_duration: float, tolerance: float = 0.01) -> Tuple[bool, Optional[str]]:
        """验证时长是否合理"""
        try:
            sr, data = wavfile.read(wav_path)
            actual_duration = len(data) / sr
            if abs(actual_duration - expected_duration) > tolerance:
                return False, f"时长偏差过大: 期望{expected_duration}s, 实际{actual_duration}s"
            return True, None
        except Exception as e:
            return False, f"验证时长失败: {e}"