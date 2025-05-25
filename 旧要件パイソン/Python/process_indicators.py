#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
経済指標処理メインモジュール

このモジュールは、経済指標データとZigZagデータを読み込み、非対称分析と統計処理を
実行するためのメインエントリーポイントを提供します。コマンドライン引数の処理、
データ読み込み、分析の実行、結果の保存などの機能が含まれています。

使用例:
    python process_indicators.py --input_indicators ../csv/MergedData/indicators_with_volatility.csv 
                                --input_zigzag ../csv/Zigzag-data/ 
                                --output_dir ../csv/Statistics/
"""

import os
import sys
import argparse
import logging
import pandas as pd
from glob import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

# 独自モジュールのインポート
from asymmetric_analysis import AsymmetricAnalyzer, batch_process_indicators
from statistical_processor import StatisticalProcessor

# ロガーの設定
logger = logging.getLogger(__name__)

def setup_logging(log_level: str = 'INFO'):
    """
    ロギングの設定を行う
    
    Args:
        log_level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # コンソール出力
            logging.FileHandler(f"indicator_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")  # ファイル出力
        ]
    )

def parse_arguments():
    """
    コマンドライン引数を解析する
    
    Returns:
        argparse.Namespace: 解析された引数
    """
    parser = argparse.ArgumentParser(description='Process economic indicators with ZigZag data')
    
    # 入力ファイル関連
    parser.add_argument('--input_indicators', type=str, required=True,
                        help='Path to the indicators CSV file')
    parser.add_argument('--input_zigzag', type=str, required=True,
                        help='Path to the ZigZag data directory or file')
    
    # 出力ディレクトリ
    parser.add_argument('--output_dir', type=str, default='../csv/Statistics/',
                        help='Directory to save output files')
    
    # 分析パラメータ
    parser.add_argument('--pre_window', type=int, default=5,
                        help='Pre-event analysis window in minutes (default: 5)')
    parser.add_argument('--post_windows', type=str, default='5,15,30',
                        help='Comma-separated list of post-event analysis windows in minutes (default: 5,15,30)')
    parser.add_argument('--min_samples', type=int, default=5,
                        help='Minimum number of samples required for statistics (default: 5)')
    parser.add_argument('--target_window', type=int, default=15,
                        help='Target time window in minutes for statistics (default: 15)')
    
    # 分類方法
    parser.add_argument('--classification_method', type=str, choices=['percentile', 'absolute'],
                        default='percentile', help='Method for volatility classification (default: percentile)')
    
    # その他の設定
    parser.add_argument('--log_level', type=str, 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Logging level (default: INFO)')
    
    return parser.parse_args()

def load_indicator_data(file_path: str) -> pd.DataFrame:
    """
    経済指標データをCSVファイルから読み込む
    
    Args:
        file_path: 経済指標CSVファイルのパス
        
    Returns:
        DataFrame: 読み込まれた経済指標データ
    """
    try:
        logger.info(f"Loading indicator data from {file_path}")
        
        # エンコーディングの問題に対応するためにいくつかのエンコーディングを試す
        encodings = ['utf-8', 'cp932', 'shift-jis', 'latin1']
        df_indicators = None
        
        for encoding in encodings:
            try:
                df_indicators = pd.read_csv(file_path, encoding=encoding)
                logger.info(f"Successfully loaded indicators with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                logger.warning(f"Failed to load with encoding: {encoding}")
                continue
        
        if df_indicators is None:
            logger.error(f"Failed to load indicators with any of the tried encodings")
            return pd.DataFrame()
        
        logger.info(f"Loaded {len(df_indicators)} indicator records")
        return df_indicators
    
    except Exception as e:
        logger.error(f"Error loading indicator data: {e}")
        return pd.DataFrame()

def load_zigzag_data(path: str) -> pd.DataFrame:
    """
    ZigZagデータを読み込む（ディレクトリまたは単一ファイル）
    
    Args:
        path: ZigZagデータファイルまたはディレクトリのパス
        
    Returns:
        DataFrame: 読み込まれたZigZagデータ
    """
    try:
        # ディレクトリの場合は全ファイルを取得
        if os.path.isdir(path):
            logger.info(f"Loading ZigZag data from directory: {path}")
            zigzag_files = glob(os.path.join(path, "mt5_zigzag_legs_*.csv"))
        else:
            # 単一ファイルの場合
            logger.info(f"Loading ZigZag data from file: {path}")
            zigzag_files = [path]
        
        if not zigzag_files:
            logger.error(f"No ZigZag files found at {path}")
            return pd.DataFrame()
        
        logger.info(f"Found {len(zigzag_files)} ZigZag files")
        
        # 全ファイルを読み込んで結合
        df_list = []
        for file_path in zigzag_files:
            try:
                df_temp = pd.read_csv(file_path, sep='\t')
                df_list.append(df_temp)
                logger.debug(f"Loaded {len(df_temp)} records from {file_path}")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue
        
        if not df_list:
            logger.error("No valid ZigZag data could be loaded")
            return pd.DataFrame()
        
        # 全データを結合
        df_zigzag = pd.concat(df_list, ignore_index=True)
        
        # 時間列を変換
        if 'start_time_utc_seconds' in df_zigzag.columns:
            df_zigzag['start_time_dt'] = pd.to_datetime(df_zigzag['start_time_utc_seconds'], unit='s')
        
        if 'end_time_utc_seconds' in df_zigzag.columns:
            df_zigzag['end_time_dt'] = pd.to_datetime(df_zigzag['end_time_utc_seconds'], unit='s')
        
        logger.info(f"Loaded and combined {len(df_zigzag)} ZigZag records")
        return df_zigzag
    
    except Exception as e:
        logger.error(f"Error loading ZigZag data: {e}")
        return pd.DataFrame()

def ensure_directory(directory_path: str) -> bool:
    """
    ディレクトリが存在することを確認し、必要に応じて作成する
    
    Args:
        directory_path: 確認/作成するディレクトリのパス
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        directory = Path(directory_path)
        if not directory.exists():
            logger.info(f"Creating directory: {directory_path}")
            directory.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False

def main():
    """
    メイン処理関数
    """
    # 引数の解析
    args = parse_arguments()
    
    # ロギングの設定
    setup_logging(args.log_level)
    
    logger.info("Starting economic indicator processing")
    logger.info(f"Arguments: {args}")
    
    # 出力ディレクトリの確認/作成
    if not ensure_directory(args.output_dir):
        logger.error("Failed to ensure output directory exists")
        return 1
    
    # 経済指標データの読み込み
    indicators_df = load_indicator_data(args.input_indicators)
    if indicators_df.empty:
        logger.error("Failed to load indicator data, aborting")
        return 1
    
    # ZigZagデータの読み込み
    zigzag_df = load_zigzag_data(args.input_zigzag)
    if zigzag_df.empty:
        logger.error("Failed to load ZigZag data, aborting")
        return 1
    
    # 発表後時間枠のリストを作成
    post_windows = [int(x.strip()) for x in args.post_windows.split(',')]
    
    # 非対称分析の実行
    logger.info("Running asymmetric analysis")
    analyzer = AsymmetricAnalyzer(pre_window=args.pre_window, post_windows=post_windows)
    analyzed_df = batch_process_indicators(indicators_df, zigzag_df, analyzer)
    
    # 分析結果の保存
    analyzed_output_path = os.path.join(args.output_dir, "analyzed_indicators.csv")
    analyzed_df.to_csv(analyzed_output_path, index=False)
    logger.info(f"Saved analyzed indicators to {analyzed_output_path}")
    
    # 統計処理の対象列を設定
    target_column = f"post_{args.target_window}min_price_movement"
    
    # 統計処理の実行
    logger.info("Running statistical processing")
    processor = StatisticalProcessor(min_samples=args.min_samples, target_column=target_column)
    stats_df, category_stats_df = processor.process_analyzed_data(
        analyzed_df, 
        classification_method=args.classification_method
    )
    
    # 統計結果の保存
    if not stats_df.empty:
        stats_output_path = os.path.join(args.output_dir, "indicator_statistics.csv")
        stats_df.to_csv(stats_output_path, index=False)
        logger.info(f"Saved indicator statistics to {stats_output_path}")
    else:
        logger.error("Failed to generate indicator statistics")
    
    if not category_stats_df.empty:
        category_output_path = os.path.join(args.output_dir, "category_statistics.csv")
        category_stats_df.to_csv(category_output_path, index=False)
        logger.info(f"Saved category statistics to {category_output_path}")
    else:
        logger.error("Failed to generate category statistics")
    
    logger.info("Economic indicator processing completed")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 