#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MT5連携モジュール実行スクリプト

このスクリプトはMT5連携モジュールを実行するためのエントリーポイントです。
コマンドライン引数を解析し、MT5連携モジュールを適切な設定で起動します。
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from mt5_integration import MT5Integration

# ロガーの設定
logger = logging.getLogger(__name__)

def parse_arguments():
    """
    コマンドライン引数を解析
    
    Returns:
        argparse.Namespace: 解析された引数
    """
    parser = argparse.ArgumentParser(description='MT5連携モジュールの実行')
    
    parser.add_argument('--csv-dir', 
                        type=str, 
                        default="../csv/EconomicIndicators",
                        help='MT5から出力されるCSVファイルのディレクトリ')
    
    parser.add_argument('--output-dir', 
                        type=str, 
                        default="../csv/MergedData",
                        help='処理後のデータを保存するディレクトリ')
    
    parser.add_argument('--done-suffix', 
                        type=str, 
                        default=".done",
                        help='完了フラグファイルの接尾辞')
    
    parser.add_argument('--retry-interval', 
                        type=int, 
                        default=60,
                        help='エラー時のリトライ間隔（秒）')
    
    parser.add_argument('--max-retries', 
                        type=int, 
                        default=5,
                        help='最大リトライ回数')
    
    parser.add_argument('--log-level', 
                        type=str, 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='ログレベル')
    
    return parser.parse_args()

def setup_logging(log_level):
    """
    ロギングの設定
    
    Args:
        log_level: ログレベル
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'無効なログレベル: {log_level}')
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('mt5_integration.log')
        ]
    )

def main():
    """
    メイン実行関数
    """
    # コマンドライン引数の解析
    args = parse_arguments()
    
    # ロギングの設定
    setup_logging(args.log_level)
    
    # 実行情報のログ出力
    logger.info("MT5連携モジュールを起動します")
    logger.info(f"CSVディレクトリ: {args.csv_dir}")
    logger.info(f"出力ディレクトリ: {args.output_dir}")
    
    try:
        # MT5連携モジュールの初期化と監視開始
        mt5_integration = MT5Integration(
            csv_dir=args.csv_dir,
            output_dir=args.output_dir,
            done_suffix=args.done_suffix,
            retry_interval=args.retry_interval,
            max_retries=args.max_retries
        )
        
        # 監視開始
        mt5_integration.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断を検出しました。プログラムを終了します。")
        sys.exit(0)
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 