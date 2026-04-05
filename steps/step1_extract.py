"""Step 1: 从原始12通道WAV提取标准数据

将每个原始文件重组为3通道标准格式（102秒完整长度）
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.io import wavfile

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.chirp_params import WAVE_PARAMS, WAVE_TYPES, SAMPLE_RATE, MIC_CHANNEL
from config.raw_files import VALID_FILES, RAW_DATA_DIR
from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger


class ChirpExtractor:
    """Chirp提取器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.timestamp = datetime.now().strftime('%Y%m%d')
        self.total_samples = int(102.0 * SAMPLE_RATE)  # 102秒完整长度

    def extract_single_file(self, raw_file: str) -> bool:
        """
        从单个原始文件提取标准数据

        输出102秒完整长度的3通道文件：
        - ch0: 喇叭参考（全102秒）
        - ch1: 麦克风（全102秒）
        - ch2: 所有波型响应叠加在同一通道
        """
        raw_path = self.config.raw_data_dir / raw_file
        if not raw_path.exists():
            logger.error(f"原始文件不存在: {raw_path}")
            return False

        # 读取原始12通道数据
        sr, data = wavfile.read(raw_path)
        logger.info(f"读取: {raw_file}, 形状: {data.shape}")

        # 创建3通道输出数组（102秒完整长度）
        output = np.zeros((self.total_samples, 3), dtype=data.dtype)

        # ch0: 喇叭参考（全102秒，原始通道0）
        output[:, 0] = data[:self.total_samples, 0]

        # ch1: 麦克风（全102秒，原始通道6）
        output[:, 1] = data[:self.total_samples, MIC_CHANNEL]

        # ch2: 各波型响应叠加到同一通道
        for wave_type in WAVE_TYPES:
            params = WAVE_PARAMS[wave_type]
            emission_times = params['emission_times']
            delay_min = params['delay_min']
            delay_max = params['delay_max']
            duration = params['duration']

            for i, emission_time in enumerate(emission_times):
                chirp_index = i + 1  # 1-indexed

                # 计算响应窗口
                resp_start_time = emission_time + delay_min
                resp_end_time = emission_time + delay_max + duration

                # 转换为样本索引
                resp_start = int(round(resp_start_time * sr))
                resp_end = int(round(resp_end_time * sr))

                if resp_end <= len(data):
                    # 将该chirp的麦克风响应叠加到ch2的对应时间位置
                    output[resp_start:resp_end, 2] += data[resp_start:resp_end, MIC_CHANNEL]

        # 生成输出文件名
        output_filename = f"{raw_file.replace('.wav', '')}_ch6_3ch.wav"
        output_path = self.config.standard_data_dir / output_filename

        wavfile.write(output_path, sr, output)
        logger.info(f"  -> 输出: {output_filename}")
        return True

    def run(self) -> int:
        """运行提取流程"""
        self.config.ensure_dirs()

        success = 0
        for raw_file in VALID_FILES:
            if self.extract_single_file(raw_file):
                success += 1

        logger.info(f"Step 1 完成: 共提取 {success} 个标准WAV")
        return success


def main():
    setup_logging('INFO')

    project_root = Path(__file__).parent.parent
    config = PipelineConfig(project_root)

    extractor = ChirpExtractor(config)
    extractor.run()


if __name__ == '__main__':
    main()
