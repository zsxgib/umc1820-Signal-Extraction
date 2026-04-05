"""波型参数定义"""

WAVE_PARAMS = {
    'PS': {
        'freq_start': 1000,
        'freq_end': 2000,
        'duration': 0.020,
        'delay_min': 0.0173,
        'delay_max': 0.0479,
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
        'delay_min': 0.0382,
        'delay_max': 0.0882,
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
