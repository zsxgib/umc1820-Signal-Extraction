# 标准数据格式重构实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 umc1820-Signal-Extraction 重构为基于标准数据格式的处理流程，每个 chirp 独立为 3 通道 WAV 文件。

**Architecture:** 
- 新目录: `/home/zsx/umc1820-2026-03-22-1/umc1820-Signal-Extraction_refactor`
- 每个原始文件拆分为 50 个标准 WAV（5 波型 × 10 chirp）
- 9 个有效文件共生成 450 个标准 WAV
- 处理流程: 提取 → 匹配滤波 → 相干累积

**Tech Stack:** Python 3, scipy, numpy, dataclass

---

## 原始文件信息

```
1-20260328_160012.wav
2-20260328_160617.wav
3-20260328_162520.wav
4-wind-20260328_164615.wav (风噪文件，不参与处理)
5-20260328_172538.wav
6-20260328_173024.wav
7-20260328_173827.wav
8-20260328_180101.wav
9-20260328_182051.wav
10-20260328_182617.wav
```

有效文件: 9 个（排除 4-wind）

---

## 目录结构

```
umc1820-Signal-Extraction_refactor/
├── config/
│   ├── __init__.py
│   ├── chirp_params.py      # 波型参数定义
│   └── raw_files.py         # 原始文件列表
├── standard_data/
│   ├── __init__.py
│   ├── chirp_chunk.py       # ChirpChunk 数据类
│   ├── naming.py            # 文件命名/解析工具
│   └── validator.py          # WAV 验证工具
├── pipeline/
│   ├── __init__.py
│   ├── base.py              # 处理器基类
│   ├── logging.py           # 日志工具
│   └── config.py            # 路径配置
├── steps/
│   ├── __init__.py
│   ├── step1_extract.py     # 提取标准数据
│   ├── step2_match.py       # 匹配滤波
│   └── step3_accumulate.py # 相干累积
├── run_pipeline.py          # 主入口
└── README.md
```

---

## 任务列表

### 任务 1: 创建目录结构和基础配置

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/config/__init__.py`
- Create: `umc1820-Signal-Extraction_refactor/config/chirp_params.py`
- Create: `umc1820-Signal-Extraction_refactor/config/raw_files.py`
- Create: `umc1820-Signal-Extraction_refactor/standard_data/__init__.py`
- Create: `umc1820-Signal-Extraction_refactor/pipeline/__init__.py`
- Create: `umc1820-Signal-Extraction_refactor/steps/__init__.py`

**Step 1: 创建 chirp_params.py**

```python
"""波型参数定义"""

WAVE_PARAMS = {
    'PS': {
        'freq_start': 1000,
        'freq_end': 2000,
        'duration': 0.020,
        'delay_min': 0.017,
        'delay_max': 0.048,
        'emission_times': [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
    },
    'SV': {
        'freq_start': 800,
        'freq_end': 1200,
        'duration': 0.025,
        'delay_min': 0.035,
        'delay_max': 0.085,
        'emission_times': [22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 34.0, 36.0, 38.0, 40.0],
    },
    'SH': {
        'freq_start': 800,
        'freq_end': 1200,
        'duration': 0.025,
        'delay_min': 0.038,
        'delay_max': 0.088,
        'emission_times': [42.0, 44.0, 46.0, 48.0, 50.0, 52.0, 54.0, 56.0, 58.0, 60.0],
    },
    'A0H': {
        'freq_start': 500,
        'freq_end': 800,
        'duration': 0.025,
        'delay_min': 0.065,
        'delay_max': 0.145,
        'emission_times': [62.0, 64.0, 66.0, 68.0, 70.0, 72.0, 74.0, 76.0, 78.0, 80.0],
    },
    'A0L': {
        'freq_start': 100,
        'freq_end': 300,
        'duration': 0.100,
        'delay_min': 0.200,
        'delay_max': 1.300,
        'emission_times': [82.0, 84.0, 86.0, 88.0, 90.0, 92.0, 94.0, 96.0, 98.0, 100.0],
    },
}

WAVE_TYPES = ['PS', 'SV', 'SH', 'A0H', 'A0L']
SAMPLE_RATE = 192000
NUM_MICS = 8
MIC_USED = 5  # 麦克风5 (通道7, 1-indexed)
SPEAKER_CHANNELS = [0, 1]  # 喇叭左/右
MIC_CHANNEL = 6  # 麦克风5 (0-indexed)
```

**Step 2: 创建 raw_files.py**

```python
"""原始文件列表"""

RAW_FILES = [
    '1-20260328_160012.wav',
    '2-20260328_160617.wav',
    '3-20260328_162520.wav',
    '4-wind-20260328_164615.wav',  # 风噪文件
    '5-20260328_172538.wav',
    '6-20260328_173024.wav',
    '7-20260328_173827.wav',
    '8-20260328_180101.wav',
    '9-20260328_182051.wav',
    '10-20260328_182617.wav',
]

# 有效文件（排除风噪）
VALID_FILES = [f for f in RAW_FILES if 'wind' not in f.lower()]

# 原始数据路径
RAW_DATA_DIR = '/home/zsx/umc1820-2026-03-22-1/umc1820_refactor/save-sound'
```

**Step 3: 创建空 __init__.py 文件**

创建所有目录的 `__init__.py` 文件。

---

### 任务 2: ChirpChunk 数据类

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/standard_data/chirp_chunk.py`

**Step 1: 编写 ChirpChunk 类**

```python
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
```

---

### 任务 3: 文件命名和验证工具

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/standard_data/naming.py`
- Create: `umc1820-Signal-Extraction_refactor/standard_data/validator.py`

**Step 1: 创建 naming.py**

```python
"""文件命名和解析工具"""

import re
from pathlib import Path
from typing import Optional, Tuple
from config.chirp_params import WAVE_TYPES


class ChirpFilenameParser:
    """解析 Chirp 标准文件名"""
    
    PATTERN = re.compile(
        r'^(.+)_mic(\d+)_(【PS|SV|SH|A0H|A0L】)_\d\d_(extracted|matched|accumulated)_(\d+)\.wav$'
    )
    # 注: 上面【】应为{}

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
        return wave_type in WAVE_TYPES

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
```

**Step 2: 创建 validator.py**

```python
"""WAV 文件验证工具"""

import numpy as np
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
```

---

### 任务 4: Pipeline 基础组件

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/pipeline/base.py`
- Create: `umc1820-Signal-Extraction_refactor/pipeline/config.py`
- Create: `umc1820-Signal-Extraction_refactor/pipeline/logging.py`

**Step 1: 创建 pipeline/config.py**

```python
"""Pipeline 路径配置"""

from pathlib import Path

class PipelineConfig:
    """Pipeline 路径配置"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.raw_data_dir = Path('/home/zsx/umc1820-2026-03-22-1/umc1820_refactor/save-sound')
        self.standard_data_dir = project_root / 'standard_data'
        self.output_dir = project_root / 'output'
        
    def ensure_dirs(self):
        """确保目录存在"""
        self.standard_data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
```

**Step 2: 创建 pipeline/logging.py**

```python
"""日志工具"""

import logging
import sys

def setup_logging(level: str = 'INFO'):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

logger = logging.getLogger(__name__)
```

**Step 3: 创建 pipeline/base.py**

```python
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
```

---

### 任务 5: Step 1 - 提取标准数据

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/steps/step1_extract.py`

**Step 1: 创建 step1_extract.py**

```python
"""Step 1: 从原始12通道WAV提取标准数据

将每个原始文件拆分为50个标准3通道WAV文件
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
from standard_data.naming import ChirpFilenameBuilder
from standard_data.validator import WAVValidator
from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger


class ChirpExtractor:
    """Chirp提取器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.timestamp = datetime.now().strftime('%Y%m%d')
    
    def extract_single_file(self, raw_file: str) -> int:
        """
        从单个原始文件提取50个标准WAV
        
        Returns:
            提取的标准WAV数量
        """
        raw_path = self.config.raw_data_dir / raw_file
        if not raw_path.exists():
            logger.error(f"原始文件不存在: {raw_path}")
            return 0
        
        # 读取原始12通道数据
        sr, data = wavfile.read(raw_path)
        logger.info(f"读取: {raw_file}, 形状: {data.shape}")
        
        count = 0
        for wave_type in WAVE_TYPES:
            params = WAVE_PARAMS[wave_type]
            emission_times = params['emission_times']
            
            for i, emission_time in enumerate(emission_times):
                chirp_index = i + 1  # 1-indexed
                
                # 计算响应窗口
                response_start = emission_time + params['delay_min']
                response_end = emission_time + params['delay_max'] + params['duration']
                
                # 转换为样本索引
                start_sample = int(response_start * sr)
                end_sample = int(response_end * sr)
                
                # 提取喇叭模板
                template_start = int(emission_time * sr)
                template_end = template_start + int(params['duration'] * sr)
                speaker_template = data[template_start:template_end, 0].astype(np.float32)
                
                # 提取麦克风原始响应（响应窗口）
                mic_response = data[start_sample:end_sample, MIC_CHANNEL].astype(np.float32)
                
                # 构建标准WAV数据（3通道）
                output_data = np.zeros((len(mic_response), 3), dtype=np.float32)
                output_data[:, 0] = speaker_template[:len(mic_response)] if len(speaker_template) >= len(mic_response) else np.pad(speaker_template, (0, len(mic_response) - len(speaker_template)))
                output_data[:, 1] = mic_response
                output_data[:, 2] = mic_response  # ch2 = ch1 截取窗口
                
                # 生成文件名
                filename = ChirpFilenameBuilder.build(
                    original_filename=raw_file.replace('.wav', ''),
                    mic_id=5,
                    wave_type=wave_type,
                    chirp_index=chirp_index,
                    status='extracted',
                    timestamp=self.timestamp
                )
                
                # 保存
                output_path = self.config.standard_data_dir / filename
                wavfile.write(output_path, sr, output_data)
                count += 1
        
        logger.info(f"  -> 提取了 {count} 个标准WAV")
        return count
    
    def run(self) -> int:
        """运行提取流程"""
        self.config.ensure_dirs()
        
        total = 0
        for raw_file in VALID_FILES:
            count = self.extract_single_file(raw_file)
            total += count
        
        logger.info(f"Step 1 完成: 共提取 {total} 个标准WAV")
        return total


def main():
    setup_logging('INFO')
    
    project_root = Path(__file__).parent.parent
    config = PipelineConfig(project_root)
    
    extractor = ChirpExtractor(config)
    extractor.run()


if __name__ == '__main__':
    main()
```

---

### 任务 6: Step 2 - 匹配滤波

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/steps/step2_match.py`

**Step 1: 创建 step2_match.py**

```python
"""Step 2: 匹配滤波处理

对标准WAV应用匹配滤波，更新状态为 matched
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy import signal
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.chirp_params import WAVE_PARAMS
from standard_data.naming import ChirpFilenameParser, ChirpFilenameBuilder
from standard_data.validator import WAVValidator
from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger


class MatchedFilterProcessor:
    """匹配滤波处理器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.timestamp = datetime.now().strftime('%Y%m%d')
    
    def process_single(self, wav_path: Path) -> bool:
        """处理单个标准WAV"""
        # 验证
        is_valid, error = WAVValidator.validate(wav_path)
        if not is_valid:
            logger.error(f"验证失败 {wav_path}: {error}")
            return False
        
        # 解析文件名
        filename = wav_path.name
        parsed = ChirpFilenameParser.parse(filename)
        if not parsed:
            logger.error(f"文件名格式错误: {filename}")
            return False
        
        if parsed['status'] != 'extracted':
            logger.debug(f"跳过已处理的: {filename}")
            return True
        
        # 读取数据
        sr, data = wavfile.read(wav_path)
        
        # 提取喇叭模板和麦克风响应
        speaker_template = data[:, 0].astype(np.float32)
        mic_response = data[:, 1].astype(np.float32)
        
        # 生成chirp模板
        wave_type = parsed['wave_type']
        params = WAVE_PARAMS[wave_type]
        n = int(params['duration'] * sr)
        t = np.linspace(0, params['duration'], n)
        chirp_template = np.sin(2 * np.pi * t * np.linspace(params['freq_start'], params['freq_end'], n)).astype(np.float32)
        
        # 匹配滤波
        matched = signal.correlate(mic_response, chirp_template, mode='same')
        
        # 更新数据
        output_data = np.zeros(data.shape, dtype=data.dtype)
        output_data[:, 0] = speaker_template
        output_data[:, 1] = mic_response
        output_data[:, 2] = matched.astype(np.int32)
        
        # 生成新文件名
        new_filename = ChirpFilenameBuilder.build(
            original_filename=parsed['original_filename'],
            mic_id=parsed['mic_id'],
            wave_type=wave_type,
            chirp_index=parsed['chirp_index'],
            status='matched',
            timestamp=self.timestamp
        )
        
        # 保存
        output_path = self.config.standard_data_dir / new_filename
        wavfile.write(output_path, sr, output_data)
        
        # 删除旧文件
        wav_path.unlink()
        
        return True
    
    def run(self) -> int:
        """运行匹配滤波"""
        files = list(self.config.standard_data_dir.glob('*_extracted_*.wav'))
        logger.info(f"找到 {len(files)} 个 extracted 文件")
        
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
```

---

### 任务 7: Step 3 - 相干累积

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/steps/step3_accumulate.py`

**Step 1: 创建 step3_accumulate.py**

```python
"""Step 3: 相干累积

按波型累积所有 matched 文件
"""

import sys
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.chirp_params import WAVE_PARAMS, WAVE_TYPES
from standard_data.naming import ChirpFilenameParser
from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger


class CoherentAccumulator:
    """相干累积处理器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.timestamp = datetime.now().strftime('%Y%m%d')
    
    def accumulate_by_wave(self, wave_type: str) -> np.ndarray:
        """按波型累积所有 matched 文件"""
        pattern = f'*_{wave_type}_*_matched_*.wav'
        files = sorted(self.config.standard_data_dir.glob(pattern))
        
        if not files:
            logger.warning(f"没有找到 {wave_type} 的 matched 文件")
            return None
        
        logger.info(f"  {wave_type}: 找到 {len(files)} 个文件")
        
        # 读取第一个文件作为参考
        sr, ref_data = wavfile.read(files[0])
        accum_data = np.zeros(ref_data.shape, dtype=np.float64)
        
        # 读取所有文件并累加 ch2
        for f in files:
            _, data = wavfile.read(f)
            accum_data[:, 2] += data[:, 2].astype(np.float64)
        
        # 保持 ch0 和 ch1 不变
        accum_data[:, 0] = ref_data[:, 0].astype(np.float64)
        accum_data[:, 1] = ref_data[:, 1].astype(np.float64)
        
        return accum_data.astype(np.int32)
    
    def run(self) -> bool:
        """运行相干累积"""
        # 创建输出目录
        output_dir = self.config.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 按波型分别累积
        accumulated = {}
        for wave_type in WAVE_TYPES:
            data = self.accumulate_by_wave(wave_type)
            if data is not None:
                accumulated[wave_type] = data
        
        if not accumulated:
            logger.error("没有累积数据")
            return False
        
        # 生成最终输出文件名
        output_filename = f"coherent_accumulation_{self.timestamp}.wav"
        output_path = output_dir / output_filename
        
        # 合并到单个3通道文件
        # 读取第一个波型的形状作为参考
        ref_data = accumulated[WAVE_TYPES[0]]
        final_output = np.zeros(ref_data.shape, dtype=np.int32)
        
        # ch0 和 ch1 来自第一个文件
        final_output[:, 0] = ref_data[:, 0]
        final_output[:, 1] = ref_data[:, 1]
        
        # ch2 按时间顺序放置各波型累积结果
        sr = 192000
        for wave_type in WAVE_TYPES:
            if wave_type not in accumulated:
                continue
            
            data = accumulated[wave_type]
            params = WAVE_PARAMS[wave_type]
            emission_times = params['emission_times']
            
            # 使用第一个chirp的时间位置
            placement_time = emission_times[0]
            start_sample = int(placement_time * sr)
            
            # 累积结果的时长
            accum_len = len(data)
            
            # 放置到 ch2
            end_sample = min(start_sample + accum_len, len(final_output))
            final_output[start_sample:end_sample, 2] = data[:end_sample - start_sample, 2]
        
        # 保存最终输出
        wavfile.write(output_path, sr, final_output)
        logger.info(f"Step 3 完成: {output_path}")
        
        return True


def main():
    setup_logging('INFO')
    
    project_root = Path(__file__).parent.parent
    config = PipelineConfig(project_root)
    
    accumulator = CoherentAccumulator(config)
    accumulator.run()


if __name__ == '__main__':
    main()
```

---

### 任务 8: 主入口脚本

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/run_pipeline.py`

**Step 1: 创建 run_pipeline.py**

```python
"""主入口脚本"""

import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.config import PipelineConfig
from pipeline.logging import setup_logging, logger
from steps.step1_extract import ChirpExtractor
from steps.step2_match import MatchedFilterProcessor
from steps.step3_accumulate import CoherentAccumulator


def run_pipeline(steps: list, project_root: Path = None):
    """运行流水线"""
    if project_root is None:
        project_root = Path(__file__).parent
    
    config = PipelineConfig(project_root)
    
    if 1 in steps:
        logger.info("=" * 50)
        logger.info("Step 1: 提取标准数据")
        logger.info("=" * 50)
        extractor = ChirpExtractor(config)
        extractor.run()
    
    if 2 in steps:
        logger.info("=" * 50)
        logger.info("Step 2: 匹配滤波")
        logger.info("=" * 50)
        processor = MatchedFilterProcessor(config)
        processor.run()
    
    if 3 in steps:
        logger.info("=" * 50)
        logger.info("Step 3: 相干累积")
        logger.info("=" * 50)
        accumulator = CoherentAccumulator(config)
        accumulator.run()
    
    logger.info("流水线完成")


def main():
    parser = argparse.ArgumentParser(description='HDPE膜声学探测信号提取流水线')
    parser.add_argument('--step', type=int, default=3, help='运行到第几步')
    parser.add_argument('--project-root', type=str, default=None, help='项目根目录')
    
    args = parser.parse_args()
    
    setup_logging('INFO')
    
    project_root = Path(args.project_root) if args.project_root else Path(__file__).parent
    steps = list(range(1, args.step + 1))
    
    run_pipeline(steps, project_root)


if __name__ == '__main__':
    main()
```

---

### 任务 9: 创建 README.md

**Files:**
- Create: `umc1820-Signal-Extraction_refactor/README.md`

**Step 1: 创建 README.md**

```markdown
# HDPE Membrane Acoustic Detection - Signal Extraction Pipeline (Refactored)

## 概述

基于标准数据格式的信号提取流水线。每个 chirp 独立为 3 通道 WAV 文件，便于追踪和处理。

## 标准数据格式

### 命名规范

```
{原始文件名}_mic5_{波型}_{Chirp编号}_{状态}_{时间戳}.wav

示例：
1-20260328_160012_mic5_PS_01_extracted_20260404.wav
```

### WAV 结构（3通道）

| 通道 | 内容 |
|------|------|
| ch1 | 喇叭参考信号 |
| ch2 | 麦克风原始响应 |
| ch3 | 处理结果 |

## 处理流程

```
原始12ch WAV → Step1: 提取 → 450个标准3ch WAV → Step2: 匹配滤波 → Step3: 相干累积 → 最终输出
```

## 使用方法

```bash
cd /home/zsx/umc1820-2026-03-22-1/umc1820-Signal-Extraction_refactor

# 运行完整流水线
python3 run_pipeline.py

# 仅 Step 1
python3 run_pipeline.py --step 1

# 仅 Step 1-2
python3 run_pipeline.py --step 2
```

## 原始文件

- 1-20260328_160012.wav
- 2-20260328_160617.wav
- 3-20260328_162520.wav
- 4-wind-20260328_164615.wav (风噪，不参与处理)
- 5-20260328_172538.wav
- 6-20260328_173024.wav
- 7-20260328_173827.wav
- 8-20260328_180101.wav
- 9-20260328_182051.wav
- 10-20260328_182617.wav
```

---

## 执行方式

**执行选项：**

1. **Subagent-Driven (本会话)** - 我按任务逐个执行子代理，期间审查，适合快速迭代

2. **Parallel Session (新会话)** - 在新会话中打开 executing-plans，批量执行带检查点

**选择哪种方式？**
