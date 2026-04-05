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
