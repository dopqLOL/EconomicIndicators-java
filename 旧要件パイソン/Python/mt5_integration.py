#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MT5連携モジュール

このモジュールはMetaTrader 5 (MT5)から出力された経済指標データを監視し、
処理するための機能を提供します。ファイル監視ベースの連携方式を採用しており、
MT5側で出力されたCSVファイルを検出し、データ処理パイプラインに渡します。

主な機能:
- CSVディレクトリの監視
- 新しい経済指標データファイルの検出
- 完了フラグファイルの確認
- データの読み込みと前処理
- エラー処理とリカバリーメカニズム
"""

import os
import time
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

# ロガーの設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class EconomicIndicatorFileHandler(FileSystemEventHandler):
    """
    経済指標ファイルの変更を検出し処理するハンドラークラス
    """
    
    def __init__(self, callback_function=None, target_dir=None, done_suffix=".done"):
        """
        初期化
        
        Args:
            callback_function: 新しいファイルが検出された時に呼び出す関数
            target_dir: 監視対象ディレクトリ
            done_suffix: 完了フラグファイルの接尾辞
        """
        self.callback_function = callback_function
        self.target_dir = Path(target_dir) if target_dir else None
        self.done_suffix = done_suffix
        self.processed_files = set()  # 処理済みファイルを追跡
        
    def on_created(self, event):
        """
        ファイル作成イベントのハンドラー
        
        Args:
            event: ファイルシステムイベント
        """
        if not event.is_directory:
            self._process_file_event(event)
                
    def on_modified(self, event):
        """
        ファイル変更イベントのハンドラー
        
        Args:
            event: ファイルシステムイベント
        """
        if not event.is_directory:
            self._process_file_event(event)
    
    def _process_file_event(self, event):
        """
        ファイルイベントを処理する内部メソッド
        
        Args:
            event: ファイルシステムイベント
        """
        file_path = Path(event.src_path)
        
        # 既に処理済みのファイルはスキップ
        if str(file_path) in self.processed_files:
            return
            
        # 経済指標CSVファイルかつ完了フラグファイルが存在する場合のみ処理
        if (file_path.name.startswith("EconomicIndicators_") and 
            file_path.suffix.lower() == ".csv"):
            
            # 対応する完了フラグファイルのパス
            done_file = file_path.with_suffix(self.done_suffix)
            
            # 完了フラグファイルが存在するか確認
            if done_file.exists():
                logger.info(f"新しい経済指標ファイルを検出しました: {file_path}")
                
                # コールバック関数が設定されていれば呼び出す
                if self.callback_function:
                    try:
                        self.callback_function(file_path)
                        # 処理済みとしてマーク
                        self.processed_files.add(str(file_path))
                        logger.info(f"ファイルの処理が完了しました: {file_path}")
                    except Exception as e:
                        logger.error(f"ファイル処理中にエラーが発生しました: {e}")


class MT5Integration:
    """
    MT5との連携を管理するメインクラス
    """
    
    def __init__(self, 
                 csv_dir: str = "../csv/EconomicIndicators",
                 output_dir: str = "../csv/MergedData",
                 done_suffix: str = ".done",
                 retry_interval: int = 60,
                 max_retries: int = 5):
        """
        初期化
        
        Args:
            csv_dir: MT5から出力されるCSVファイルのディレクトリ
            output_dir: 処理後のデータを保存するディレクトリ
            done_suffix: 完了フラグファイルの接尾辞
            retry_interval: エラー時のリトライ間隔（秒）
            max_retries: 最大リトライ回数
        """
        self.csv_dir = Path(csv_dir)
        self.output_dir = Path(output_dir)
        self.done_suffix = done_suffix
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self.observer = None
        
        # ディレクトリの存在確認と作成
        self._ensure_directories()
        
    def _ensure_directories(self):
        """
        必要なディレクトリが存在することを確認し、なければ作成
        """
        for directory in [self.csv_dir, self.output_dir]:
            if not directory.exists():
                logger.info(f"ディレクトリを作成します: {directory}")
                directory.mkdir(parents=True, exist_ok=True)
    
    def start_monitoring(self):
        """
        ファイル監視を開始
        """
        logger.info(f"ディレクトリの監視を開始します: {self.csv_dir}")
        
        # ファイルハンドラーの設定
        event_handler = EconomicIndicatorFileHandler(
            callback_function=self.process_indicator_file,
            target_dir=self.csv_dir,
            done_suffix=self.done_suffix
        )
        
        # 監視の設定と開始
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.csv_dir), recursive=False)
        self.observer.start()
        
        try:
            # 既存ファイルのチェック（起動時に既に存在するファイルを処理）
            self._check_existing_files()
            
            logger.info("ファイル監視中... Ctrl+Cで終了")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """
        ファイル監視を停止
        """
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("ファイル監視を停止しました")
    
    def _check_existing_files(self):
        """
        既存のファイルをチェックして処理
        """
        logger.info(f"既存ファイルをチェックしています: {self.csv_dir}")
        
        # CSVファイルとそれに対応する完了フラグファイルを探す
        csv_files = list(self.csv_dir.glob("EconomicIndicators_*.csv"))
        
        for csv_file in csv_files:
            done_file = csv_file.with_suffix(self.done_suffix)
            if done_file.exists():
                # 完了フラグファイルが存在する場合、手動でイベントを発生させる
                logger.info(f"既存の完了済みファイルを検出: {csv_file}")
                event = FileCreatedEvent(str(csv_file))
                handler = EconomicIndicatorFileHandler(
                    callback_function=self.process_indicator_file,
                    target_dir=self.csv_dir,
                    done_suffix=self.done_suffix
                )
                handler.on_created(event)
    
    def process_indicator_file(self, file_path: Path) -> bool:
        """
        経済指標ファイルを処理
        
        Args:
            file_path: 処理対象のファイルパス
            
        Returns:
            bool: 処理が成功したかどうか
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                logger.info(f"経済指標ファイルの処理を開始: {file_path}")
                
                # CSVファイルの読み込み
                df = pd.read_csv(file_path)
                
                # 基本的なデータ検証
                if df.empty:
                    logger.warning(f"ファイルにデータがありません: {file_path}")
                    return False
                
                # 必要なカラムがあるか確認
                required_columns = ["DateTime (UTC)", "Currency", "EventName", "Forecast", "Actual"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    logger.error(f"必要なカラムがありません: {missing_columns}")
                    return False
                
                # 日時の変換
                df['DateTime_UTC'] = pd.to_datetime(df['DateTime (UTC)'])
                
                # 日本時間への変換
                df['DateTime_JST'] = df['DateTime_UTC'] + pd.Timedelta(hours=9)
                
                # 日付と時刻を分離
                df['Date_JST'] = df['DateTime_JST'].dt.date
                df['Time_JST'] = df['DateTime_JST'].dt.time
                
                # 出力ファイル名の生成
                output_filename = f"Processed_{file_path.stem}.csv"
                output_path = self.output_dir / output_filename
                
                # 処理済みデータの保存
                df.to_csv(output_path, index=False)
                logger.info(f"処理済みデータを保存しました: {output_path}")
                
                return True
                
            except Exception as e:
                retries += 1
                logger.error(f"処理中にエラーが発生しました ({retries}/{self.max_retries}): {e}")
                if retries <= self.max_retries:
                    logger.info(f"{self.retry_interval}秒後にリトライします...")
                    time.sleep(self.retry_interval)
                else:
                    logger.error(f"最大リトライ回数に達しました。処理を中止します: {file_path}")
                    return False
        
        return False


def main():
    """
    メイン実行関数
    """
    # コマンドライン引数の処理などを追加可能
    
    # MT5連携モジュールの初期化と監視開始
    mt5_integration = MT5Integration()
    mt5_integration.start_monitoring()


if __name__ == "__main__":
    main() 