#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
統計処理モジュール

このモジュールは、経済指標ボラティリティ分析のための統計計算機能を提供します。
指標ごとの統計量の計算やカテゴリ分類アルゴリズムなどが含まれています。

主な機能:
- 指標ごとの統計量計算（平均値、中央値、標準偏差など）
- ボラティリティに基づく指標の分類（大・中・小）
- カテゴリ別の統計情報の集計
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Union, Any

# ロガーの設定
logger = logging.getLogger(__name__)

class StatisticalProcessor:
    """
    指標データの統計処理を行うクラス
    """
    
    def __init__(self, 
                 category_thresholds: Tuple[float, float] = None,
                 min_samples: int = 5,
                 target_column: str = 'post_15min_price_movement'):
        """
        初期化
        
        Args:
            category_thresholds: カテゴリ分類のしきい値 (低・中の境界, 中・高の境界)
                                Noneの場合は自動でパーセンタイルを計算
            min_samples: 統計計算に必要な最小サンプル数
            target_column: 統計計算とカテゴリ分類の対象列
        """
        self.category_thresholds = category_thresholds
        self.min_samples = min_samples
        self.target_column = target_column
        logger.info(f"StatisticalProcessor initialized with min_samples={min_samples}, "
                   f"target_column={target_column}")
    
    def calculate_indicator_statistics(self, 
                                      analyzed_df: pd.DataFrame,
                                      group_columns: List[str] = None) -> pd.DataFrame:
        """
        指標ごとの統計量を計算する
        
        Args:
            analyzed_df: 分析済みの指標データ
            group_columns: グループ化する列名のリスト（デフォルトは['Currency', 'EventName']）
            
        Returns:
            DataFrame: 指標ごとの統計量
        """
        if group_columns is None:
            group_columns = ['Currency', 'EventName']
        
        logger.info(f"Calculating statistics for {len(analyzed_df)} records, grouped by {group_columns}")
        
        try:
            # カラムが存在するか確認
            missing_cols = [col for col in group_columns + [self.target_column] if col not in analyzed_df.columns]
            if missing_cols:
                logger.error(f"Missing columns in dataframe: {missing_cols}")
                return pd.DataFrame()
            
            # ターゲット列の無効な値をフィルタリング
            valid_data = analyzed_df.dropna(subset=[self.target_column])
            logger.info(f"Valid data after dropping NaN: {len(valid_data)} records")
            
            # グループごとに統計量を計算
            stats = valid_data.groupby(group_columns).agg({
                self.target_column: [
                    ('mean', 'mean'),
                    ('median', 'median'),
                    ('std', 'std'),
                    ('min', 'min'),
                    ('max', 'max'),
                    ('count', 'count')
                ]
            })
            
            # マルチインデックスを解除
            stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
            stats = stats.reset_index()
            
            # 最小サンプル数でフィルタリング
            count_col = f"{self.target_column}_count"
            stats_filtered = stats[stats[count_col] >= self.min_samples]
            logger.info(f"Filtered statistics with at least {self.min_samples} samples: "
                       f"{len(stats_filtered)} out of {len(stats)}")
            
            # 小数点以下の桁数を制限
            float_cols = [col for col in stats_filtered.columns if stats_filtered[col].dtype == 'float64']
            for col in float_cols:
                stats_filtered[col] = stats_filtered[col].round(3)
            
            return stats_filtered
            
        except Exception as e:
            logger.error(f"Error calculating indicator statistics: {e}")
            return pd.DataFrame()
    
    def classify_indicators(self, 
                           stats_df: pd.DataFrame,
                           method: str = 'percentile') -> pd.DataFrame:
        """
        指標をボラティリティに基づいて分類する
        
        Args:
            stats_df: 指標統計量のDataFrame
            method: 分類方法 ('percentile'または'absolute')
            
        Returns:
            DataFrame: カテゴリ列が追加された統計量
        """
        try:
            # 統計量データのコピーを作成
            classified_df = stats_df.copy()
            
            # 平均値列の名前を特定
            mean_col = f"{self.target_column}_mean"
            if mean_col not in classified_df.columns:
                logger.error(f"Mean column '{mean_col}' not found in dataframe")
                return stats_df
            
            # カテゴリ分類を適用
            if method == 'percentile':
                # パーセンタイルに基づく分類
                if self.category_thresholds is None:
                    # 33パーセンタイルと67パーセンタイルを計算
                    q1 = classified_df[mean_col].quantile(0.33)
                    q2 = classified_df[mean_col].quantile(0.67)
                else:
                    q1, q2 = self.category_thresholds
                
                logger.info(f"Using percentile thresholds: q1={q1:.3f}, q2={q2:.3f}")
                
                # カテゴリ分類関数
                def get_category(x):
                    if x < q1:
                        return "小"
                    elif x < q2:
                        return "中"
                    else:
                        return "大"
                
            elif method == 'absolute':
                # 絶対値に基づく分類
                if self.category_thresholds is None:
                    # デフォルト値を設定
                    q1, q2 = 0.0005, 0.001  # 例: 5pips, 10pips (XAUUSDの場合は調整が必要)
                else:
                    q1, q2 = self.category_thresholds
                
                logger.info(f"Using absolute thresholds: q1={q1:.3f}, q2={q2:.3f}")
                
                # カテゴリ分類関数
                def get_category(x):
                    if x < q1:
                        return "小"
                    elif x < q2:
                        return "中"
                    else:
                        return "大"
            
            else:
                logger.error(f"Unknown classification method: {method}")
                return stats_df
            
            # カテゴリ列の追加
            classified_df['Volatility_Category'] = classified_df[mean_col].apply(get_category)
            logger.info("Indicator classification completed")
            
            return classified_df
            
        except Exception as e:
            logger.error(f"Error classifying indicators: {e}")
            return stats_df
    
    def calculate_category_statistics(self, 
                                     classified_df: pd.DataFrame) -> pd.DataFrame:
        """
        カテゴリ別の統計量を計算する
        
        Args:
            classified_df: カテゴリ分類された指標統計量のDataFrame
            
        Returns:
            DataFrame: カテゴリ別統計量
        """
        try:
            # カテゴリ列が存在するか確認
            if 'Volatility_Category' not in classified_df.columns:
                logger.error("Volatility_Category column not found in dataframe")
                return pd.DataFrame()
            
            # 平均値列の名前を特定
            mean_col = f"{self.target_column}_mean"
            if mean_col not in classified_df.columns:
                logger.error(f"Mean column '{mean_col}' not found in dataframe")
                return pd.DataFrame()
            
            # カテゴリ別の統計量を計算
            category_stats = classified_df.groupby('Volatility_Category').agg({
                mean_col: ['mean', 'min', 'max', 'count']
            })
            
            # マルチインデックスを解除
            category_stats.columns = ['_'.join(col).strip() for col in category_stats.columns.values]
            category_stats = category_stats.reset_index()
            
            # 小数点以下の桁数を制限
            float_cols = [col for col in category_stats.columns if category_stats[col].dtype == 'float64']
            for col in float_cols:
                category_stats[col] = category_stats[col].round(3)
            
            logger.info("Category statistics calculation completed")
            return category_stats
            
        except Exception as e:
            logger.error(f"Error calculating category statistics: {e}")
            return pd.DataFrame()
    
    def process_analyzed_data(self, 
                             analyzed_df: pd.DataFrame,
                             group_columns: List[str] = None,
                             classification_method: str = 'percentile') -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分析済みデータの一連の統計処理を実行する
        
        Args:
            analyzed_df: 分析済みの指標データ
            group_columns: グループ化する列名のリスト
            classification_method: 分類方法
            
        Returns:
            Tuple[DataFrame, DataFrame]: (指標統計量, カテゴリ統計量)
        """
        logger.info(f"Starting statistical processing of {len(analyzed_df)} records")
        
        # 1. 指標ごとの統計量計算
        indicator_stats = self.calculate_indicator_statistics(analyzed_df, group_columns)
        if indicator_stats.empty:
            logger.error("Failed to calculate indicator statistics")
            return pd.DataFrame(), pd.DataFrame()
        
        # 2. 指標の分類
        classified_stats = self.classify_indicators(indicator_stats, classification_method)
        
        # 3. カテゴリ別統計の計算
        category_stats = self.calculate_category_statistics(classified_stats)
        
        logger.info("Statistical processing completed successfully")
        return classified_stats, category_stats


def calculate_percentiles(data_series: pd.Series, 
                         percentiles: List[float] = None) -> Dict[float, float]:
    """
    データ系列のパーセンタイルを計算する
    
    Args:
        data_series: 値の系列
        percentiles: 計算するパーセンタイルのリスト（デフォルトは[0.25, 0.5, 0.75, 0.9, 0.95]）
        
    Returns:
        Dict[float, float]: パーセンタイル値の辞書
    """
    if percentiles is None:
        percentiles = [0.25, 0.5, 0.75, 0.9, 0.95]
    
    try:
        # 欠損値を除外
        valid_data = data_series.dropna()
        
        if len(valid_data) == 0:
            logger.warning("No valid data for percentile calculation")
            return {p: None for p in percentiles}
        
        # パーセンタイルの計算
        percentile_values = {}
        for p in percentiles:
            percentile_values[p] = valid_data.quantile(p)
        
        return percentile_values
    
    except Exception as e:
        logger.error(f"Error calculating percentiles: {e}")
        return {p: None for p in percentiles}


def analyze_distribution(data_series: pd.Series) -> Dict[str, float]:
    """
    データ分布の特性を分析する
    
    Args:
        data_series: 値の系列
        
    Returns:
        Dict[str, float]: 分布特性の辞書
    """
    try:
        # 欠損値を除外
        valid_data = data_series.dropna()
        
        if len(valid_data) < 2:
            logger.warning("Insufficient data for distribution analysis")
            return {
                'mean': None,
                'median': None,
                'std': None,
                'skewness': None,
                'kurtosis': None,
                'count': len(valid_data)
            }
        
        # 基本統計量
        stats = {
            'mean': valid_data.mean(),
            'median': valid_data.median(),
            'std': valid_data.std(),
            'count': len(valid_data)
        }
        
        # 歪度と尖度（3以上でより尖った分布）
        if len(valid_data) >= 3:
            stats['skewness'] = valid_data.skew()
            stats['kurtosis'] = valid_data.kurt()
        
        return stats
    
    except Exception as e:
        logger.error(f"Error analyzing distribution: {e}")
        return {
            'mean': None,
            'median': None,
            'std': None,
            'skewness': None,
            'kurtosis': None,
            'count': 0,
            'error': str(e)
        }


def detect_outliers(data_series: pd.Series, 
                   method: str = 'iqr', 
                   threshold: float = 1.5) -> pd.Series:
    """
    データ系列から外れ値を検出する
    
    Args:
        data_series: 値の系列
        method: 検出方法（'iqr'または'zscore'）
        threshold: 閾値（IQR法の場合は倍率、Zスコア法の場合は標準偏差の倍数）
        
    Returns:
        Series: 外れ値フラグ（True/False）の系列
    """
    try:
        # 欠損値を除外
        valid_data = data_series.dropna()
        
        if len(valid_data) < 4:
            logger.warning("Insufficient data for outlier detection")
            return pd.Series([False] * len(data_series), index=data_series.index)
        
        if method == 'iqr':
            # IQR法（四分位範囲）による外れ値検出
            q1 = valid_data.quantile(0.25)
            q3 = valid_data.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - (threshold * iqr)
            upper_bound = q3 + (threshold * iqr)
            
            outliers = (data_series < lower_bound) | (data_series > upper_bound)
            
        elif method == 'zscore':
            # Zスコア法による外れ値検出
            mean = valid_data.mean()
            std = valid_data.std()
            
            if std == 0:
                logger.warning("Standard deviation is zero, cannot detect outliers using zscore method")
                return pd.Series([False] * len(data_series), index=data_series.index)
            
            zscores = (data_series - mean) / std
            outliers = abs(zscores) > threshold
            
        else:
            logger.error(f"Unknown outlier detection method: {method}")
            return pd.Series([False] * len(data_series), index=data_series.index)
        
        return outliers
    
    except Exception as e:
        logger.error(f"Error detecting outliers: {e}")
        return pd.Series([False] * len(data_series), index=data_series.index)


if __name__ == "__main__":
    # モジュール単体テスト用コード
    logging.basicConfig(level=logging.INFO,
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("StatisticalProcessor module loaded successfully")
    print("Run unit tests or import this module to use its functionality") 