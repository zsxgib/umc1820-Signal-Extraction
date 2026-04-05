"""Step 3: 相干累积

按波型累积所有 matched 文件
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.io import wavfile
from scipy import signal

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.chirp_params import WAVE_PARAMS, WAVE_TYPES, SAMPLE_RATE
from config.raw_files import VALID_FILES
from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger


class CoherentAccumulator:
    """相干累积处理器"""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.timestamp = datetime.now().strftime('%Y%m%d')
        self.sr = SAMPLE_RATE
        self.total_samples = int(102.0 * self.sr)  # 102秒

    def find_delay_by_crosscorr(self, ref_signal: np.ndarray, target_signal: np.ndarray) -> int:
        """
        使用互相关找目标信号相对于参考信号的时延

        Args:
            ref_signal: 参考信号 (1D array)
            target_signal: 目标信号 (1D array)，长度须与ref_signal相同

        Returns:
            int: 时延值（正表示target滞后于ref，需要正偏移对齐）
                 即：用 offset = -delay 进行线性移位可将target对齐到ref
        """
        # 互相关
        corr = signal.correlate(target_signal, ref_signal, mode='full')
        # 相关长度
        n = len(ref_signal)
        # 峰值位置（无时延时应在中心位置 n-1）
        peak_idx = np.argmax(np.abs(corr))
        # 中心点
        center = n - 1
        # 时延：正值表示target滞后（需要右移），负值表示target超前（需要左移）
        delay = peak_idx - center
        return delay

    def linear_shift(self, seg: np.ndarray, offset: int) -> np.ndarray:
        """
        线性移位（替代np.roll循环移位）

        Args:
            seg: 输入信号
            offset: 偏移量，正表示向右移（信号晚到，需要右移对齐），负表示向左移

        Returns:
            移位后的信号，长度与输入相同，边缘补零
        """
        if offset > 0:
            # 正偏移：向右移，右边补零
            shifted = np.pad(seg, (offset, 0), mode='constant')[:len(seg)]
        elif offset < 0:
            # 负偏移：向左移，左边补零
            shifted = np.pad(seg, (0, -offset), mode='constant')[-len(seg):]
        else:
            shifted = seg
        return shifted

    def accumulate_wave_to_buffer(self, wave_type: str, output_buffer: np.ndarray, files: list) -> None:
        """
        将指定波型的所有 matched 文件累积到缓冲区

        Args:
            wave_type: 波型 (PS/SV/SH/A0H/A0L)
            output_buffer: 完整长度的输出缓冲区 (samples, 3)
            files: matched 文件列表
        """
        params = WAVE_PARAMS[wave_type]
        emission_times = params['emission_times']
        delay_min = params['delay_min']
        delay_max = params['delay_max']
        duration = params['duration']

        # 波型通道映射：PS=2, SV=3, SH=4, A0H=5, A0L=6
        wave_channel = {'PS': 2, 'SV': 3, 'SH': 4, 'A0H': 5, 'A0L': 6}[wave_type]

        logger.info(f"  {wave_type}: 累积 {len(emission_times)} 个 chirp")

        # 计算第一个chirp的响应窗口大小
        # 使用与原始版本相同的计算方式，避免浮点数精度问题
        # response_end = emission_time + delay_max (精确值 83.3)
        # duration 单独加，避免 83.4 = 82.0 + 1.3 + 0.1 的浮点数精度损失
        first_emission = emission_times[0]
        first_resp_start_time = first_emission + delay_min
        first_resp_end_time = first_emission + delay_max
        first_start_sample = int(first_resp_start_time * self.sr)
        first_end_sample = int(first_resp_end_time * self.sr) + int(duration * self.sr)
        window_len = first_end_sample - first_start_sample

        # 为该波型创建累积buffer
        wave_buffer = np.zeros(window_len, dtype=np.float64)

        # 对每个 chirp 分别收集、对齐、累加
        for i, emission_time in enumerate(emission_times):
            chirp_idx = i + 1  # 1-indexed

            # 计算响应窗口大小
            # 使用与原始版本相同的计算方式，避免浮点数精度问题
            resp_start_time = emission_time + delay_min
            resp_end_time = emission_time + delay_max
            start_sample = int(resp_start_time * self.sr)
            end_sample = int(resp_end_time * self.sr) + int(duration * self.sr)
            resp_window_len = end_sample - start_sample

            # 收集所有文件该chirp的响应
            all_segments = []
            all_peak_positions = []

            for f in files:
                try:
                    _, data = wavfile.read(f)
                except Exception as e:
                    logger.warning(f"读取失败 {f}: {e}")
                    continue

                if len(data) <= start_sample:
                    continue

                # 从对应波型通道读取该chirp的滤波结果，强制为固定长度window_len
                seg_end = min(start_sample + window_len, len(data))
                segment = data[start_sample:seg_end, wave_channel].astype(np.float64)

                # 如果长度不足，补零到window_len
                if len(segment) < window_len:
                    segment = np.pad(segment, (0, window_len - len(segment)), mode='constant')

                if len(segment) > 0:
                    peak_idx = np.argmax(np.abs(segment))
                    all_segments.append(segment)
                    all_peak_positions.append(peak_idx)

            if len(all_segments) == 0:
                continue

            # 使用互相关找时延对齐（替代循环移位）
            # 以第一个segment为参考
            ref_segment = all_segments[0]

            # 创建该chirp的累积数组
            chirp_accumulated = np.zeros(window_len, dtype=np.float64)

            # 参考segment直接累积
            chirp_accumulated += ref_segment

            # 对其他segment用互相关找时延，线性移位对齐后累加
            for seg in all_segments[1:]:
                # 使用互相关找时延
                delay = self.find_delay_by_crosscorr(ref_segment, seg)
                # 线性移位对齐
                # delay > 0 表示 seg 晚到（需左移，offset为负）
                # delay < 0 表示 seg 早到（需右移，offset为正）
                # offset = -delay 实现正确的对齐方向
                shifted = self.linear_shift(seg, -delay)
                chirp_accumulated += shifted

            # 累加到wave_buffer
            actual_len = min(len(chirp_accumulated), len(wave_buffer))
            wave_buffer[:actual_len] += chirp_accumulated[:actual_len]

            logger.debug(f"    {wave_type} chirp {chirp_idx}: 累积了 {len(all_segments)} 个文件 (使用互相关对齐)")

        # 计算缩放因子
        # 与原始Step3一致：使用整个matched文件ch1的最大值（不是仅响应窗口）
        # data_ref[:, 1]是matched文件的麦克风通道，取整个102秒的最大值
        orig_max = np.max(np.abs(output_buffer[:, 1]))  # 整个102秒麦克风信号的最大值
        accum_max = np.max(np.abs(wave_buffer))

        if accum_max > 0 and orig_max > 0:
            scale = orig_max * 0.8 / accum_max  # 缩放到原信号最大值的80%
        else:
            scale = 1.0

        logger.debug(f"  {wave_type}: orig_max={orig_max:.2e}, accum_max={accum_max:.2e}, scale={scale:.4f}")

        wave_buffer = wave_buffer * scale

        # 将波型累积结果放置到输出缓冲区的第一个chirp位置
        # 与原始版本一致：最后统一clip，不在每步clip
        end_sample = min(first_start_sample + window_len, self.total_samples)
        actual_len = end_sample - first_start_sample
        output_buffer[first_start_sample:end_sample, 2] += wave_buffer[:actual_len]

    def run(self) -> bool:
        """运行相干累积"""
        # 创建输出目录
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建完整长度的输出缓冲区 (102秒，float64与原始版本一致)
        output_buffer = np.zeros((self.total_samples, 3), dtype=np.float64)
        logger.info(f"创建输出缓冲区: {self.total_samples} 样本 ({self.total_samples/self.sr:.1f}秒)")

        # 查找 matched 文件
        matched_files = sorted(self.config.step2_output_dir.glob('matched_*_ch6_7ch.wav'))
        logger.info(f"找到 {len(matched_files)} 个 matched 文件")

        # 与原始版本一致：限制为 NUM_MICS=8 个文件
        NUM_MICS = 8
        matched_files = matched_files[:NUM_MICS]
        logger.info(f"限制为前 {len(matched_files)} 个文件进行累积")

        if not matched_files:
            logger.warning("没有找到 matched 文件!")
            return False

        # 从第一个matched文件加载 ch0 和 ch1（与原始版本一致）
        logger.info("从matched文件加载完整信号...")
        _, ref_data = wavfile.read(matched_files[0])

        # ch0=喇叭参考, ch1=麦克风（float64与原始版本一致）
        output_buffer[:, 0] = ref_data[:self.total_samples, 0].astype(np.float64)
        output_buffer[:, 1] = ref_data[:self.total_samples, 1].astype(np.float64)
        logger.info(f"  ch0 (喇叭) max: {np.max(np.abs(output_buffer[:,0])):.2e}")
        logger.info(f"  ch1 (麦克风) max: {np.max(np.abs(output_buffer[:,1])):.2e}")

        # 按波型累积
        for wave_type in WAVE_TYPES:
            logger.info(f"处理波型: {wave_type}")
            self.accumulate_wave_to_buffer(wave_type, output_buffer, matched_files)

        # 生成最终输出文件名
        output_filename = f"coherent_accumulation_{self.timestamp}.wav"
        output_path = output_dir / output_filename

        # 与原始版本一致：最后统一clip到int32范围后保存
        output_int = np.clip(output_buffer, -2147483647, 2147483647).astype(np.int32)
        wavfile.write(output_path, self.sr, output_int)
        logger.info(f"Step 3 完成: {output_path}")
        logger.info(f"  形状: {output_int.shape}")
        logger.info(f"  时长: {len(output_int)/self.sr:.1f}秒")
        logger.info(f"  ch0 max: {np.max(np.abs(output_int[:,0]))}")
        logger.info(f"  ch1 max: {np.max(np.abs(output_int[:,1]))}")
        logger.info(f"  ch2 max: {np.max(np.abs(output_int[:,2]))}")

        return True


def main():
    setup_logging('INFO')

    project_root = Path(__file__).parent.parent
    config = PipelineConfig(project_root)

    accumulator = CoherentAccumulator(config)
    accumulator.run()


if __name__ == '__main__':
    main()
