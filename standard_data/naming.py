"""文件命名和解析工具"""

import re
from pathlib import Path
from typing import Optional


class ChirpFilenameParser:
    """解析 Chirp 标准文件名"""

    PATTERN = re.compile(
        r'^(.+)_mic(\d+)_(PS|SV|SH|A0H|A0L)_(\d{2})_(extracted|matched|accumulated)_(\d+)\.wav$'
    )

    @classmethod
    def parse(cls, filename: str) -> Optional[dict]:
        """解析文件名，返回成分字典"""
        match = cls.PATTERN.match(filename)
        if not match:
            return None
        return {
            'original_filename': match.group(1),
            'mic_id': int(match.group(2)),
            'wave_type': match.group(3),
            'chirp_index': int(match.group(4)),
            'status': match.group(5),
            'timestamp': match.group(6),
        }

    @classmethod
    def is_valid_wave_type(cls, wave_type: str) -> bool:
        """验证波型是否有效"""
        valid_types = ['PS', 'SV', 'SH', 'A0H', 'A0L']
        return wave_type in valid_types

    @classmethod
    def is_valid_chirp_index(cls, index: int) -> bool:
        """验证chirp编号是否有效"""
        return 1 <= index <= 10


class ChirpFilenameBuilder:
    """构建 Chirp 标准文件名"""

    @staticmethod
    def build(
        original_filename: str,
        mic_id: int,
        wave_type: str,
        chirp_index: int,
        status: str,
        timestamp: str
    ) -> str:
        """构建标准文件名"""
        return f"{original_filename}_mic{mic_id}_{wave_type}_{chirp_index:02d}_{status}_{timestamp}.wav"