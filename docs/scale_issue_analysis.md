# 缩放问题分析

## 问题描述

重构版本与原始版本的 step2 缩放逻辑存在架构性差异，导致最终输出信号比例不同。

## 原始 step2 缩放逻辑 (pipeline/processing/matched_filter.py)

```python
# 第一步：创建累加buffer，将所有chirp的matched结果累加到各自的时间窗口
accumulated = np.zeros(len(data), dtype=np.float64)

for i, chirp_t in enumerate(chirp_times):
    matched = matched_results[wave_name][i]
    # 累加到响应窗口
    accumulated[resp_start:resp_end] += matched[:resp_end - resp_start]

# 第二步：用累加结果计算scale_factor
matched_max = np.max(np.abs(accumulated))
orig_max = np.max(np.abs(data[:, wave_channel]))
scale_factor = orig_max / matched_max

# 第三步：应用scale_factor并写入
output_data[:, wave_channel] = (accumulated * scale_factor).astype(np.int32)
```

**关键**：所有 chirps 的 matched 先累加到各自时间位置，然后**计算一次 scale_factor**，最后统一缩放。

## 重构 step2 缩放逻辑 (steps/step2_match.py)

```python
# 每个chirp单独处理
matched = signal.correlate(mic_response, chirp_template, mode='same')

# 计算缩放因子
matched_max = np.max(np.abs(matched))
orig_max = np.max(np.abs(mic_response))

if matched_max > 0 and orig_max > 0:
    scale_factor = float(orig_max) / float(matched_max)
else:
    scale_factor = 1.0

matched_scaled = np.multiply(matched, scale_factor, dtype=np.float64)
```

**关键**：每个 chirp **单独计算 scale_factor，单独缩放**。

## 数学差异

假设3个chirps的matched峰值：
- Chirp 1: 3.08e+19
- Chirp 2: 2.15e+19
- Chirp 3: 1.05e+19
- orig_max = 3.0e+8

### 原始缩放

```python
accumulated = 3.08e+19 + 2.15e+19 + 1.05e+19 = 6.28e+19
scale = 3.0e+8 / 6.28e+19 = 4.7771e-12

结果:
- Chirp1缩放: 3.08e+19 * 4.7771e-12 = 1.47e+08
- Chirp2缩放: 2.15e+19 * 4.7771e-12 = 1.03e+08
- Chirp3缩放: 1.05e+19 * 4.7771e-12 = 5.02e+07
```

### 重构缩放

```python
scale1 = 3.0e+8 / 3.08e+19 = 9.7403e-12
scale2 = 3.0e+8 / 2.15e+19 = 1.3953e-11
scale3 = 3.0e+8 / 1.05e+19 = 2.8571e-11

结果:
- Chirp1缩放: 3.08e+19 * 9.7403e-12 = 3.00e+08
- Chirp2缩放: 2.15e+19 * 1.3953e-11 = 3.00e+08
- Chirp3缩放: 1.05e+19 * 2.8571e-11 = 3.00e+08
```

## 差异对比

| Chirp | 原始缩放后 | 重构缩放后 |
|-------|-----------|-----------|
| 1 | 1.47e+08 | 3.00e+08 |
| 2 | 1.03e+08 | 3.00e+08 |
| 3 | 5.02e+07 | 3.00e+08 |

- **原始**：chirp1最强，chirp3最弱（按比例衰减）
- **重构**：所有chirps一样强（都达到orig_max）

## 影响

这种差异导致：
1. 信号强度分布完全不同
2. 累积时可能产生不同的峰值位置
3. 最终输出可能有"线头"样的异常

## 解决方案

### 方案1：修改重构step2，输出完整文件（推荐）

让重构 step2 输出完整文件（像原始那样），在完整文件上累加所有 chirps 后计算一次 scale_factor。

### 方案2：修改重构step3的scale计算

在 step3 累积时，重新计算统一的 scale_factor。

### 方案3：短文件流程中实现统一缩放

先收集所有 chirps 的 matched 数据，累加后计算统一的 scale_factor，再重新缩放每个 chirp 后保存。
