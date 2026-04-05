"""处理器基类"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from pipeline.logging import logger


class BaseProcessor(ABC):
    """处理器基类"""

    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = input_dir
        self.output_dir = output_dir

    @abstractmethod
    def process(self, input_path: Path) -> bool:
        """处理单个输入"""
        pass

    @abstractmethod
    def run(self) -> int:
        """运行处理流程"""
        pass

    def get_input_files(self, pattern: str = '*.wav') -> List[Path]:
        """获取输入文件列表"""
        return sorted(self.input_dir.glob(pattern))