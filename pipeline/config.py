"""Pipeline 路径配置"""

from pathlib import Path

class PipelineConfig:
    """Pipeline 路径配置"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.raw_data_dir = Path('/home/zsx/umc1820-2026-03-22-1/umc1820_refactor/save-sound')
        self.standard_data_dir = project_root / 'standard_data'
        self.step2_output_dir = project_root / 'standard_data'  # matched文件也放在standard_data目录
        self.output_dir = project_root / 'output'

    def ensure_dirs(self):
        """确保目录存在"""
        self.standard_data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)