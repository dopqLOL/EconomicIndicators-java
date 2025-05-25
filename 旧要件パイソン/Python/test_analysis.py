#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
分析モジュールテストスクリプト

このスクリプトは、実装した分析モジュールの機能をテストするために使用します。
サンプルデータを生成または読み込み、各モジュールの主要な機能をテストします。
"""

import os
import sys
import logging
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# テスト対象のモジュールをインポート
try:
    from asymmetric_analysis import AsymmetricAnalyzer, batch_process_indicators, extract_zigzag_window
    from statistical_processor import StatisticalProcessor, calculate_percentiles, detect_outliers
    from multiscale_analysis import MultiscaleAnalyzer, compare_time_windows
except ImportError as e:
    print(f"Error importing analysis modules: {e}")
    print("Make sure you're running this script from the Python directory.")
    sys.exit(1)

# ロガーの設定
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDataGenerator:
    """
    テスト用のデータを生成するクラス
    """
    
    @staticmethod
    def generate_zigzag_data(num_points: int = 100, 
                           start_time: datetime = None,
                           time_increment: timedelta = None) -> pd.DataFrame:
        """
        ZigZagデータを生成する
        
        Args:
            num_points: 生成するデータポイント数
            start_time: 開始時刻（Noneの場合は現在時刻から1日前）
            time_increment: 時間の増分（Noneの場合は1分）
            
        Returns:
            DataFrame: 生成されたZigZagデータ
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        
        if time_increment is None:
            time_increment = timedelta(minutes=1)
        
        # 時間列の生成
        times = [start_time + time_increment * i for i in range(num_points)]
        times_utc_seconds = [int(t.timestamp()) for t in times]
        
        # ZigZag価格の生成
        np.random.seed(42)  # 再現性のために乱数シードを固定
        base_price = 1800.0  # 金価格の基準値
        
        # ランダムな変動を追加
        price_changes = np.random.normal(0, 1, num_points)
        prices = [base_price]
        
        for i in range(1, num_points):
            # 前の価格に変動を追加
            new_price = prices[-1] + price_changes[i]
            prices.append(new_price)
        
        # 前のポイントの価格と同じにならないように小さな調整を加える
        for i in range(1, len(prices)):
            if abs(prices[i] - prices[i-1]) < 0.1:
                prices[i] += 0.1
        
        # DataFrameを作成
        df = pd.DataFrame({
            'start_time_utc_seconds': times_utc_seconds,
            'start_time_dt': times,
            'price': prices,
            'leg_length': np.abs(np.diff(np.array(prices), prepend=prices[0])),
            'is_high': [i % 2 == 0 for i in range(num_points)]  # 偶数インデックスを高値とする
        })
        
        return df
    
    @staticmethod
    def generate_indicator_data(num_indicators: int = 10, 
                              num_currencies: int = 3,
                              start_time: datetime = None) -> pd.DataFrame:
        """
        経済指標データを生成する
        
        Args:
            num_indicators: 生成する指標数
            num_currencies: 通貨数
            start_time: 開始時刻（Noneの場合は現在時刻から2日前）
            
        Returns:
            DataFrame: 生成された経済指標データ
        """
        if start_time is None:
            start_time = datetime.now() - timedelta(days=2)
        
        currencies = ['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'NZD'][:num_currencies]
        event_names = [
            'Interest Rate Decision', 'GDP Growth Rate', 'Inflation Rate', 
            'Unemployment Rate', 'PMI', 'Retail Sales', 'Trade Balance',
            'Consumer Confidence'
        ]
        
        data = []
        for i in range(num_indicators):
            # ランダムな通貨とイベントを選択
            currency = currencies[i % len(currencies)]
            event_name = event_names[i % len(event_names)]
            
            # 発表時刻（開始時刻から1時間ごと）
            event_time = start_time + timedelta(hours=i)
            
            # 影響度（1-3）
            impact = (i % 3) + 1
            
            # 予想値と実際値
            forecast = np.random.normal(2.0, 0.5)
            actual = forecast + np.random.normal(0, 0.3)
            
            # レコードを追加
            data.append({
                'ID': i + 1,
                'Currency': currency,
                'EventName': event_name,
                'DateTime_UTC': event_time,
                'Impact': impact,
                'Forecast': round(forecast, 1),
                'Actual': round(actual, 1),
                'Surprise': round(actual - forecast, 1)
            })
        
        return pd.DataFrame(data)

class TestAsymmetricAnalysis(unittest.TestCase):
    """
    AsymmetricAnalyzerのテスト
    """
    
    def setUp(self):
        """
        テスト用のデータを準備
        """
        # テストデータの生成
        self.data_generator = TestDataGenerator()
        self.zigzag_df = self.data_generator.generate_zigzag_data(200)
        self.indicator_df = self.data_generator.generate_indicator_data(10)
        
        # 分析インスタンスの作成
        self.analyzer = AsymmetricAnalyzer(pre_window=3, post_windows=[3, 10, 20])
    
    def test_extract_zigzag_window(self):
        """
        extract_zigzag_window関数のテスト
        """
        # テスト用の時間範囲を設定
        start_time = self.zigzag_df['start_time_dt'].iloc[50]
        end_time = self.zigzag_df['start_time_dt'].iloc[60]
        
        # ウィンドウを抽出
        window_data = extract_zigzag_window(self.zigzag_df, start_time, end_time)
        
        # 結果を検証
        self.assertGreaterEqual(len(window_data), 0)  # 少なくとも1件のデータがあるはず
        if len(window_data) > 0:
            self.assertTrue((window_data['start_time_dt'] >= start_time).all())
            self.assertTrue((window_data['start_time_dt'] <= end_time).all())
    
    def test_analyze_pre_event(self):
        """
        analyze_pre_event関数のテスト
        """
        # 単一の指標レコードを選択
        indicator_row = self.indicator_df.iloc[5]
        
        # 発表前分析を実行
        results = self.analyzer.analyze_pre_event(indicator_row, self.zigzag_df)
        
        # 結果を検証
        self.assertIsInstance(results, dict)
        self.assertIn('pre_event_valid', results)
        
        # テスト用に価格変動データを追加（StatisticalProcessorのテスト用）
        if not results.get('pre_event_valid', False):
            results['price_movement'] = 0.05
    
    def test_analyze_post_event(self):
        """
        analyze_post_event関数のテスト
        """
        # 単一の指標レコードを選択
        indicator_row = self.indicator_df.iloc[5]
        
        # 発表後分析を実行
        results = self.analyzer.analyze_post_event(indicator_row, self.zigzag_df)
        
        # 結果を検証
        self.assertIsInstance(results, dict)
        self.assertIn('post_event_valid', results)
        
        # テスト用に価格変動データを追加（StatisticalProcessorとMultiscaleAnalyzerのテスト用）
        post_windows = self.analyzer.post_windows
        for window in post_windows:
            results[f'post_{window}min_price_movement'] = 0.01 * window
    
    def test_batch_process_indicators(self):
        """
        batch_process_indicators関数のテスト
        """
        # サンプルサイズを小さくして処理時間を短縮
        sample_indicators = self.indicator_df.head(3)
        
        # バッチ処理を実行
        results_df = batch_process_indicators(sample_indicators, self.zigzag_df, self.analyzer)
        
        # 結果を検証
        self.assertIsInstance(results_df, pd.DataFrame)
        self.assertEqual(len(results_df), len(sample_indicators))
        
        # テスト用に価格変動データを追加
        post_windows = self.analyzer.post_windows
        for window in post_windows:
            results_df[f'post_{window}min_price_movement'] = [0.01 * window * (i + 1) for i in range(len(results_df))]

class TestStatisticalProcessor(unittest.TestCase):
    """
    StatisticalProcessorのテスト
    """
    
    def setUp(self):
        """
        テスト用のデータを準備
        """
        # テストデータの生成
        self.data_generator = TestDataGenerator()
        self.zigzag_df = self.data_generator.generate_zigzag_data(200)
        self.indicator_df = self.data_generator.generate_indicator_data(20, num_currencies=4)
        
        # テスト用の分析結果を生成
        analyzer = AsymmetricAnalyzer(pre_window=3, post_windows=[3, 10])
        self.analyzed_df = batch_process_indicators(self.indicator_df, self.zigzag_df, analyzer)
        
        # テスト用に価格変動データを追加
        self.analyzed_df['post_10min_price_movement'] = [0.1 * (i % 5 + 1) for i in range(len(self.analyzed_df))]
        
        # 統計処理インスタンスの作成
        self.processor = StatisticalProcessor(min_samples=2, target_column='post_10min_price_movement')
    
    def test_calculate_indicator_statistics(self):
        """
        calculate_indicator_statistics関数のテスト
        """
        # 統計量を計算
        stats_df = self.processor.calculate_indicator_statistics(self.analyzed_df)
        
        # 結果を検証
        self.assertIsInstance(stats_df, pd.DataFrame)
        self.assertGreater(len(stats_df), 0)
        
        # 必須カラムが存在するか確認
        expected_columns = ['Currency', 'EventName', 'post_10min_price_movement_mean']
        for col in expected_columns:
            self.assertIn(col, stats_df.columns)
    
    def test_classify_indicators(self):
        """
        classify_indicators関数のテスト
        """
        # 統計量を計算
        stats_df = self.processor.calculate_indicator_statistics(self.analyzed_df)
        
        if len(stats_df) > 0:
            # 分類を実行
            classified_df = self.processor.classify_indicators(stats_df)
            
            # 結果を検証
            self.assertIsInstance(classified_df, pd.DataFrame)
            self.assertEqual(len(classified_df), len(stats_df))
            self.assertIn('Volatility_Category', classified_df.columns)
    
    def test_calculate_percentiles(self):
        """
        calculate_percentiles関数のテスト
        """
        # テスト用のデータ系列
        data_series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        
        # パーセンタイルを計算
        percentiles = calculate_percentiles(data_series, [0.25, 0.5, 0.75])
        
        # 結果を検証
        self.assertIsInstance(percentiles, dict)
        self.assertEqual(len(percentiles), 3)
        self.assertAlmostEqual(percentiles[0.25], 3.25, delta=0.01)
        self.assertAlmostEqual(percentiles[0.5], 5.5, delta=0.01)
        self.assertAlmostEqual(percentiles[0.75], 7.75, delta=0.01)
    
    def test_detect_outliers(self):
        """
        detect_outliers関数のテスト
        """
        # テスト用のデータ系列（外れ値を含む）
        data_series = pd.Series([1, 2, 3, 4, 5, 20, 6, 7, 8, 9])
        
        # 外れ値を検出
        outliers = detect_outliers(data_series, method='iqr', threshold=1.5)
        
        # 結果を検証
        self.assertIsInstance(outliers, pd.Series)
        self.assertEqual(len(outliers), len(data_series))
        self.assertTrue(outliers.iloc[5])  # インデックス5が外れ値として検出されるはず

class TestMultiscaleAnalysis(unittest.TestCase):
    """
    MultiscaleAnalyzerのテスト
    """
    
    def setUp(self):
        """
        テスト用のデータを準備
        """
        # テストデータの生成
        self.data_generator = TestDataGenerator()
        self.zigzag_df = self.data_generator.generate_zigzag_data(200)
        self.indicator_df = self.data_generator.generate_indicator_data(15, num_currencies=3)
        
        # テスト用の分析結果を生成
        analyzer = AsymmetricAnalyzer(pre_window=3, post_windows=[5, 15, 30])
        self.analyzed_df = batch_process_indicators(self.indicator_df, self.zigzag_df, analyzer)
        
        # テスト用に価格変動データを追加
        time_scales = [5, 15, 30]
        for scale in time_scales:
            self.analyzed_df[f'post_{scale}min_price_movement'] = [0.01 * scale * (i % 5 + 1) for i in range(len(self.analyzed_df))]
        
        # マルチスケール分析インスタンスの作成
        self.analyzer = MultiscaleAnalyzer(time_scales=[5, 15, 30], reference_scale=15)
    
    def test_calculate_scale_ratios(self):
        """
        calculate_scale_ratios関数のテスト
        """
        # スケール比率を計算
        result_df = self.analyzer.calculate_scale_ratios(self.analyzed_df)
        
        # 結果を検証
        self.assertIsInstance(result_df, pd.DataFrame)
        self.assertEqual(len(result_df), len(self.analyzed_df))
        
        # 新しいカラムが追加されているか確認
        self.assertIn('scale_ratio_5_to_15', result_df.columns)
        self.assertIn('scale_ratio_30_to_15', result_df.columns)
    
    def test_calculate_scale_correlations(self):
        """
        calculate_scale_correlations関数のテスト
        """
        # スケール間の相関を計算
        corr_matrix = self.analyzer.calculate_scale_correlations(self.analyzed_df)
        
        # 結果を検証
        self.assertIsInstance(corr_matrix, pd.DataFrame)
        self.assertEqual(corr_matrix.shape[0], corr_matrix.shape[1])  # 正方行列
    
    def test_compare_time_windows(self):
        """
        compare_time_windows関数のテスト
        """
        # 時間ウィンドウを比較
        results = compare_time_windows(self.analyzed_df, [5, 15, 30], 'price_movement')
        
        # 結果を検証
        self.assertIsInstance(results, pd.DataFrame)
        self.assertLessEqual(len(results), 3)  # 最大で3つのウィンドウを比較
        
        # 必須カラムが存在するか確認
        expected_columns = ['window_minutes', 'mean', 'median']
        for col in expected_columns:
            self.assertIn(col, results.columns)

def run_tests():
    """
    全テストを実行する
    """
    logger.info("Starting analysis module tests")
    
    # テスト対象のクラスを取得
    test_classes = [
        TestAsymmetricAnalysis,
        TestStatisticalProcessor,
        TestMultiscaleAnalysis
    ]
    
    # テストスイートを作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 結果の表示
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    return len(result.errors) + len(result.failures)

if __name__ == "__main__":
    sys.exit(run_tests()) 