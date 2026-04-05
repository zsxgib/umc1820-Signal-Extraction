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
