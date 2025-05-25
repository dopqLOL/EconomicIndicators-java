import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# 入出力ファイルパス設定
VOLATILITY_DATA_PATH = "../csv/CalculatedVolatility/intraday_volatility.csv"
ECONOMIC_INDICATORS_PATH = "../csv/EconomicIndicators/EconomicIndicators_20190501-20250518.csv"
OUTPUT_PATH = "../csv/MergedData/indicators_with_volatility.csv"

def main():
    print(f"Current working directory: {os.getcwd()}")
    
    # ボラティリティデータの読み込み
    print(f"Loading volatility data from {VOLATILITY_DATA_PATH}...")
    try:
        df_volatility = pd.read_csv(VOLATILITY_DATA_PATH)
        print(f"Loaded {len(df_volatility)} volatility records.")
        print(f"Volatility data columns: {df_volatility.columns.tolist()}")
    except Exception as e:
        print(f"Error loading volatility data: {e}")
        return
    
    # 経済指標データの読み込み
    print(f"Loading economic indicators data from {ECONOMIC_INDICATORS_PATH}...")
    try:
        # エンコーディングの問題に対応するためにいくつかのエンコーディングを試す
        encodings = ['utf-8', 'cp932', 'shift-jis', 'latin1']
        df_indicators = None
        
        for encoding in encodings:
            try:
                df_indicators = pd.read_csv(ECONOMIC_INDICATORS_PATH, encoding=encoding)
                print(f"Successfully loaded with encoding: {encoding}")
                break
            except UnicodeDecodeError:
                print(f"Failed to load with encoding: {encoding}")
                continue
        
        if df_indicators is None:
            print("Failed to load economic indicators data with any of the tried encodings.")
            return
            
        print(f"Loaded {len(df_indicators)} economic indicator records.")
        print(f"Economic indicators data columns: {df_indicators.columns.tolist()}")
        
        # 異常値の処理: 極端に大きな負の値を NaN に置き換え
        for col in ['Forecast', 'Actual']:
            if col in df_indicators.columns:
                # -9223372036854775808 は Int64の最小値で、欠損値を示している可能性が高い
                df_indicators[col] = df_indicators[col].replace(-9223372036854775808, np.nan)
        
    except Exception as e:
        print(f"Error loading economic indicators data: {e}")
        return
    
    # 日付時刻の形式を統一する
    try:
        # 経済指標データの日時フォーマット変換（UTC）
        df_indicators['DateTime_UTC'] = pd.to_datetime(df_indicators['DateTime (UTC)'], 
                                                       format='%Y.%m.%d %H:%M:%S')
        
        # 日本時間への変換
        df_indicators['DateTime_JST'] = df_indicators['DateTime_UTC'].dt.tz_localize('UTC').dt.tz_convert('Asia/Tokyo')
        
        # 日付部分と時間部分を分離
        df_indicators['Date_JST'] = df_indicators['DateTime_JST'].dt.strftime('%Y-%m-%d')
        df_indicators['Hour_JST'] = df_indicators['DateTime_JST'].dt.hour
        
        print("Date and time conversion completed.")
    except Exception as e:
        print(f"Error during date/time conversion: {e}")
        return
    
    # 各経済指標が発表された時間帯を特定
    print("Identifying time ranges for each economic indicator...")
    
    # 時間帯の定義（一致判定用）
    jst_time_ranges = [
        (7, 9),
        (9, 12),
        (12, 15),
        (15, 21),
        (21, 24),
        (0, 3),
        (3, 7)
    ]
    
    # 時間帯のマッピング関数
    def get_time_range(hour):
        for start, end in jst_time_ranges:
            if start <= hour < end:
                return f"{str(start).zfill(2)}:00-{str(end).zfill(2)}:00"
        return None
    
    # 各指標に時間帯を割り当て
    df_indicators['TimeRange_JST'] = df_indicators['Hour_JST'].apply(get_time_range)
    
    # 時間帯割り当てができなかった指標を確認
    missing_time_range = df_indicators[df_indicators['TimeRange_JST'].isna()]
    if not missing_time_range.empty:
        print(f"Warning: {len(missing_time_range)} indicators couldn't be assigned to a time range.")
    
    # ボラティリティデータと経済指標データを紐付け
    print("Merging economic indicators with volatility data...")
    
    # マージのための準備 - キーは 'Date_JST' と 'TimeRange_JST'
    merged_df = pd.merge(
        df_indicators,
        df_volatility,
        on=['Date_JST', 'TimeRange_JST'],
        how='left'
    )
    
    print(f"Merged data has {len(merged_df)} records.")
    
    # 無効な指標（文字化けしているデータなど）をフィルタリング
    # EventNameが特定のパターンを持つ行を除外
    if 'EventName' in merged_df.columns:
        # 正規表現パターンで異常値を検出し、必要に応じてフィルタリング
        problematic_pattern = r'□.*□'
        filtered_df = merged_df[~merged_df['EventName'].str.contains(problematic_pattern, regex=True, na=False)]
        print(f"Filtered out {len(merged_df) - len(filtered_df)} problematic event names.")
        merged_df = filtered_df
    
    # 数値の小数点以下の桁数を制限する処理
    numeric_cols = ['Forecast', 'Actual', 'PriceMovement', 'MaxHigh_in_Range', 'MinLow_in_Range']
    for col in numeric_cols:
        if col in merged_df.columns:
            # 小数点以下3桁に制限
            merged_df[col] = merged_df[col].apply(lambda x: round(float(x), 3) if pd.notnull(x) else x)
    
    # デバッグ用：データの一部をプレビュー表示
    print("\n===== データプレビュー =====")
    # 1. 通貨別にボラティリティデータの平均値を計算して表示
    print("\n1. 通貨別ボラティリティ平均:")
    currency_volatility = merged_df.groupby('Currency')['PriceMovement'].mean().sort_values(ascending=False)
    for currency, mean_volatility in currency_volatility.items():
        if pd.notnull(mean_volatility):
            print(f"{currency}: {mean_volatility:.3f}")

    # 2. 経済指標のサンプルデータを表示（数値の整形済み）
    print("\n2. 経済指標サンプル（各通貨の最初の5件）:")
    for currency in merged_df['Currency'].unique()[:5]:  # 最初の5通貨のみ
        currency_data = merged_df[merged_df['Currency'] == currency].head(3)  # 各通貨の最初の3件
        print(f"\n-- {currency} --")
        for _, row in currency_data.iterrows():
            if pd.notnull(row['Actual']) and pd.notnull(row['PriceMovement']):
                print(f"日時: {row['Date_JST']} {row['TimeRange_JST']}, イベント: {row['EventName']}")
                print(f"  予測: {row['Forecast']:.3f}, 実績: {row['Actual']:.3f}, 変動幅: {row['PriceMovement']:.3f}")
    
    # 3. 価格変動が大きい（上位10件）経済指標イベントを表示
    print("\n3. 価格変動が最も大きい経済指標イベント:")
    top_volatility = merged_df.sort_values('PriceMovement', ascending=False).head(10)
    for _, row in top_volatility.iterrows():
        if pd.notnull(row['PriceMovement']):
            print(f"{row['Date_JST']} {row['TimeRange_JST']} {row['Currency']} {row['EventName']}: {row['PriceMovement']:.3f}")

    # 出力
    output_dir = os.path.dirname(OUTPUT_PATH)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # 小数点以下の桁数を制限して出力
    merged_df.to_csv(OUTPUT_PATH, index=False, float_format='%.3f')
    print(f"\nMerged data saved to {OUTPUT_PATH}")
    print(f"Final record count: {len(merged_df)}")
    
    # マージ結果のサマリを表示
    indicators_with_volatility = merged_df.dropna(subset=['PriceMovement'])
    print(f"Indicators with valid volatility data: {len(indicators_with_volatility)} ({len(indicators_with_volatility)/len(merged_df)*100:.2f}%)")
    
    # 通貨別の指標数を表示
    if 'Currency' in merged_df.columns:
        currency_counts = merged_df['Currency'].value_counts()
        print("\nIndicators by currency:")
        print(currency_counts)

if __name__ == "__main__":
    main() 