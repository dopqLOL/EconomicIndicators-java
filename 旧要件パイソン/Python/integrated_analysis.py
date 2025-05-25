#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
統合分析モジュール

このモジュールは、経済指標発表前後の価格変動分析のための複数の分析手法を
統合的に実行するためのインターフェースを提供します。非対称分析、統計処理、
マルチスケール分析を連携させて、一貫した分析ワークフローを実現します。

使用例:
    python integrated_analysis.py --input_indicators ../csv/MergedData/indicators_with_volatility.csv 
                                 --input_zigzag ../csv/Zigzag-data/ 
                                 --output_dir ../csv/Statistics/
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any

# 独自モジュールのインポート
from asymmetric_analysis import AsymmetricAnalyzer, batch_process_indicators
from statistical_processor import StatisticalProcessor
from multiscale_analysis import MultiscaleAnalyzer

# ロガーの設定
logger = logging.getLogger(__name__)

def setup_logging(log_level: str = 'INFO', log_file: str = None):
    """
    ロギングの設定を行う
    
    Args:
        log_level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
        log_file: ログファイル名（Noneの場合は自動生成）
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    if log_file is None:
        log_file = f"integrated_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # コンソール出力
            logging.FileHandler(log_file)  # ファイル出力
        ]
    )

def parse_arguments():
    """
    コマンドライン引数を解析する
    
    Returns:
        argparse.Namespace: 解析された引数
    """
    parser = argparse.ArgumentParser(description='Integrated analysis of economic indicators with ZigZag data')
    
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
    parser.add_argument('--post_windows', type=str, default='5,15,30,60',
                        help='Comma-separated list of post-event analysis windows in minutes (default: 5,15,30,60)')
    parser.add_argument('--reference_scale', type=int, default=15,
                        help='Reference time scale in minutes for multi-scale analysis (default: 15)')
    parser.add_argument('--min_samples', type=int, default=5,
                        help='Minimum number of samples required for statistics (default: 5)')
    
    # 分析オプション
    parser.add_argument('--run_asymmetric', action='store_true', default=True,
                        help='Run asymmetric analysis (default: True)')
    parser.add_argument('--run_statistical', action='store_true', default=True,
                        help='Run statistical processing (default: True)')
    parser.add_argument('--run_multiscale', action='store_true', default=True,
                        help='Run multi-scale analysis (default: True)')
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
        from process_indicators import load_zigzag_data as process_load_zigzag
        return process_load_zigzag(path)
    except ImportError:
        logger.error("Failed to import process_indicators module, using simplified ZigZag loading")
        
        try:
            # ディレクトリの場合は単一ファイルを読み込む
            if os.path.isdir(path):
                logger.info(f"Loading ZigZag data from directory (first file only): {path}")
                zigzag_files = [os.path.join(path, f) for f in os.listdir(path) if f.endswith('.csv')]
                if not zigzag_files:
                    logger.error(f"No CSV files found in {path}")
                    return pd.DataFrame()
                file_path = zigzag_files[0]
            else:
                # 単一ファイルの場合
                logger.info(f"Loading ZigZag data from file: {path}")
                file_path = path
            
            # ファイルを読み込む
            try:
                df_zigzag = pd.read_csv(file_path, sep='\t')
                
                # 時間列を変換
                if 'start_time_utc_seconds' in df_zigzag.columns:
                    df_zigzag['start_time_dt'] = pd.to_datetime(df_zigzag['start_time_utc_seconds'], unit='s')
                
                if 'end_time_utc_seconds' in df_zigzag.columns:
                    df_zigzag['end_time_dt'] = pd.to_datetime(df_zigzag['end_time_utc_seconds'], unit='s')
                
                logger.info(f"Loaded {len(df_zigzag)} ZigZag records")
                return df_zigzag
                
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                return pd.DataFrame()
            
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

def save_dataframe(df: pd.DataFrame, output_path: str, index: bool = False) -> bool:
    """
    DataFrameをCSVファイルとして保存する
    
    Args:
        df: 保存するDataFrame
        output_path: 出力ファイルパス
        index: インデックスを保存するかどうか
        
    Returns:
        bool: 成功したかどうか
    """
    try:
        if df.empty:
            logger.warning(f"DataFrame is empty, not saving to {output_path}")
            return False
        
        df.to_csv(output_path, index=index)
        logger.info(f"Saved DataFrame to {output_path} ({len(df)} records)")
        return True
    except Exception as e:
        logger.error(f"Error saving DataFrame to {output_path}: {e}")
        return False

def run_integrated_analysis(args) -> int:
    """
    統合分析を実行する
    
    Args:
        args: 解析された引数
        
    Returns:
        int: 終了コード（0: 成功, 非0: 失敗）
    """
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
    
    # 1. 非対称分析を実行
    analyzed_df = None
    if args.run_asymmetric:
        logger.info("Running asymmetric analysis")
        analyzer = AsymmetricAnalyzer(pre_window=args.pre_window, post_windows=post_windows)
        analyzed_df = batch_process_indicators(indicators_df, zigzag_df, analyzer)
        
        # 分析結果の保存
        if not analyzed_df.empty:
            analyzed_output_path = os.path.join(args.output_dir, "analyzed_indicators.csv")
            save_dataframe(analyzed_df, analyzed_output_path, index=False)
        else:
            logger.error("Asymmetric analysis failed to produce results")
            return 1
    
    # 2. 統計処理を実行
    if args.run_statistical and analyzed_df is not None:
        logger.info("Running statistical processing")
        
        # 各時間枠に対して統計処理を実行
        for window in post_windows:
            target_column = f"post_{window}min_price_movement"
            
            # 統計処理の実行
            processor = StatisticalProcessor(min_samples=args.min_samples, target_column=target_column)
            stats_df, category_stats_df = processor.process_analyzed_data(
                analyzed_df, 
                classification_method=args.classification_method
            )
            
            # 統計結果の保存
            if not stats_df.empty:
                stats_output_path = os.path.join(args.output_dir, f"indicator_statistics_{window}min.csv")
                save_dataframe(stats_df, stats_output_path, index=False)
            
            if not category_stats_df.empty:
                category_output_path = os.path.join(args.output_dir, f"category_statistics_{window}min.csv")
                save_dataframe(category_stats_df, category_output_path, index=False)
    
    # 3. マルチスケール分析を実行
    if args.run_multiscale and analyzed_df is not None:
        logger.info("Running multi-scale analysis")
        
        # マルチスケール分析の実行
        analyzer = MultiscaleAnalyzer(time_scales=post_windows, reference_scale=args.reference_scale)
        multiscale_results = analyzer.perform_multiscale_analysis(analyzed_df)
        
        # 結果の保存
        for result_name, result_df in multiscale_results.items():
            if not result_df.empty:
                output_path = os.path.join(args.output_dir, f"multiscale_{result_name}.csv")
                save_dataframe(result_df, output_path, index=(result_name == 'scale_correlations'))
    
    logger.info("Integrated analysis completed successfully")
    return 0

def main():
    """
    メイン処理関数
    """
    # 引数の解析
    args = parse_arguments()
    
    # ロギングの設定
    setup_logging(args.log_level)
    
    logger.info("Starting integrated analysis")
    logger.info(f"Arguments: {args}")
    
    # 統合分析の実行
    exit_code = run_integrated_analysis(args)
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main()) 