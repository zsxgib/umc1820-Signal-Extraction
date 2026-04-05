"""Step 2: 匹配滤波处理

对标准WAV应用匹配滤波，输出7通道文件
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy import signal
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.chirp_params import WAVE_PARAMS, WAVE_TYPES, SAMPLE_RATE
from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger


class MatchedFilterProcessor:
    """匹配滤波处理器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.timestamp = datetime.now().strftime('%Y%m%d')
        self.sr = SAMPLE_RATE

    def process_single(self, wav_path: Path) -> bool:
        """处理单个标准WAV文件（102秒完整长度）"""
        # 验证文件
        if not wav_path.exists():
            logger.error(f"文件不存在: {wav_path}")
            return False

        filename = wav_path.name
        if 'matched' in filename:
            logger.debug(f"跳过已处理的: {filename}")
            return True

        # 读取数据（3通道：ch0喇叭，ch1麦克风，ch2波型响应）
        sr, data = wavfile.read(wav_path)
        logger.debug(f"处理: {filename}, 形状: {data.shape}")

        # 创建7通道输出数组
        output_data = np.zeros((len(data), 7), dtype=data.dtype)

        # ch0: 喇叭参考（不变）
        output_data[:, 0] = data[:, 0]

        # ch1: 麦克风（不变）
        output_data[:, 1] = data[:, 1]

        # 对每种波型分别处理
        for wave_name in WAVE_TYPES:
            config = WAVE_PARAMS[wave_name]
            chirp_times = config['emission_times']
            duration = config['duration']
            delay_min = config['delay_min']
            delay_max = config['delay_max']

            # 波型通道映射：PS=2, SV=3, SH=4, A0H=5, A0L=6
            wave_channel = {'PS': 2, 'SV': 3, 'SH': 4, 'A0H': 5, 'A0L': 6}[wave_name]

            # 创建累加buffer，将所有chirp的matched结果累加到各自的时间窗口
            accumulated = np.zeros(len(data), dtype=np.float64)

            for i, chirp_t in enumerate(chirp_times):
                # 提取chirp模板（从喇叭通道）
                template_start = int(chirp_t * self.sr)
                template_end = template_start + int(duration * self.sr)

                if template_end > len(data):
                    continue

                chirp_template = data[template_start:template_end, 0].astype(np.float64)

                if len(chirp_template) == 0:
                    continue

                # 提取响应窗口
                resp_start = int((chirp_t + delay_min) * self.sr)
                resp_end = int((chirp_t + delay_max + duration) * self.sr)

                if resp_end > len(data):
                    resp_end = len(data)
                if resp_start >= len(data):
                    continue

                # 从麦克风通道提取响应
                response = data[resp_start:resp_end, 1].astype(np.float64)

                if len(response) == 0:
                    continue

                # 匹配滤波 (互相关)
                matched = signal.correlate(response, chirp_template, mode='same')

                # 累加到响应窗口
                accumulated[resp_start:resp_end] += matched[:resp_end - resp_start]

            # 用累加结果计算scale_factor
            matched_max = np.max(np.abs(accumulated))
            # 对于3通道输入，所有波型响应在同一通道(通道2)上
            if data.shape[1] >= 7:
                orig_max = np.max(np.abs(data[:, wave_channel]))
            else:
                orig_max = np.max(np.abs(data[:, 2]))

            if matched_max > 0 and orig_max > 0:
                scale_factor = orig_max / matched_max
            else:
                scale_factor = 1.0

            # 应用scale_factor
            matched_scaled = accumulated * scale_factor

            # clip到int32范围
            int32_max = 2147483647
            matched_scaled = np.clip(matched_scaled, -int32_max, int32_max)

            output_data[:, wave_channel] = matched_scaled.astype(np.int32)

            logger.debug(f"  {wave_name}: matched_max={matched_max:.2e}, orig_max={orig_max:.2e}, scale={scale_factor:.4f}")

        # 生成新文件名
        base_name = filename.replace('_ch6_3ch', '').replace('.wav', '')
        new_filename = f"matched_{base_name}_ch6_7ch.wav"

        # 保存前clip到int32范围（与原始版本一致，使用-2147483647而非-2147483648）
        int32_max = 2147483647
        output_data = np.clip(output_data, -int32_max, int32_max).astype(np.int32)

        # 保存
        output_path = self.config.step2_output_dir / new_filename
        wavfile.write(output_path, sr, output_data)

        return True

    def run(self) -> int:
        """运行匹配滤波"""
        # 查找标准数据文件
        files = list(self.config.standard_data_dir.glob('*_ch6_3ch.wav'))
        logger.info(f"找到 {len(files)} 个标准数据文件")

        success = 0
        for wav_path in files:
            if self.process_single(wav_path):
                success += 1

        logger.info(f"Step 2 完成: 处理了 {success}/{len(files)} 个文件")
        return success


def main():
    setup_logging('INFO')

    project_root = Path(__file__).parent.parent
    config = PipelineConfig(project_root)

    processor = MatchedFilterProcessor(config)
    processor.run()


if __name__ == '__main__':
    main()
