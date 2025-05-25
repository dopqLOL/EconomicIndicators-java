import pandas as pd
from glob import glob
from datetime import timedelta
import pytz # タイムゾーン処理のため
import numpy as np
import os

# --- 設定項目 ---
# パスを親ディレクトリからの相対パスに変更
ZIGZAG_DATA_PATH = "../csv/Zigzag-data/mt5_zigzag_legs_*.csv"
OUTPUT_CSV_PATH = "../csv/CalculatedVolatility/intraday_volatility.csv"

# JST時間帯の定義 (開始時, 終了時)
# 例: 7時00分から8時59分まで (9時は含まない)
JST_TIME_RANGES = [
    (7, 9),
    (9, 12),
    (12, 15),
    (15, 21),
    (21, 24), # 21:00 JST to 23:59 JST (exclusive of 24:00)
    (0, 3),   # 00:00 JST to 02:59 JST (exclusive of 03:00)
    (3, 7)    # 03:00 JST to 06:59 JST (exclusive of 07:00)
]

# --- ヘルパー関数 ---
def convert_to_jst(dt_series_utc_naive):
    """
    pandas Series の naive datetime オブジェクト (UTCと仮定) をJSTに変換する。
    """
    return dt_series_utc_naive.dt.tz_localize('UTC').dt.tz_convert('Asia/Tokyo')

def is_weekend(dt):
    """
    与えられた日時が土日かどうかを返す。
    土曜日: 5, 日曜日: 6
    """
    weekday = dt.weekday()
    return weekday >= 5  # 5=土曜日、6=日曜日

# --- メイン処理 ---
def main():
    # 現在の実行パスを表示
    print(f"Current working directory: {os.getcwd()}")
    
    all_files = glob(ZIGZAG_DATA_PATH)
    if not all_files:
        print(f"No files found at {ZIGZAG_DATA_PATH}")
        return

    print(f"Found {len(all_files)} files: {all_files}")

    df_list = []
    for f in all_files:
        try:
            df_temp = pd.read_csv(f, sep='\t')
            required_cols = ['start_time_utc_seconds', 'end_time_utc_seconds', 'start_price', 'end_price']
            if not all(col in df_temp.columns for col in required_cols):
                print(f"Skipping file {f} due to missing one or more required columns: {', '.join(required_cols)}.")
                continue
            df_list.append(df_temp)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
    
    if not df_list:
        print("No valid ZigZag data could be loaded.")
        return

    df_zigzag = pd.concat(df_list, ignore_index=True)

    try:
        df_zigzag['start_time_dt'] = pd.to_datetime(df_zigzag['start_time_utc_seconds'], unit='s')
        df_zigzag['end_time_dt'] = pd.to_datetime(df_zigzag['end_time_utc_seconds'], unit='s')
    except KeyError as e:
        print(f"KeyError: One of the critical time columns ('start_time_utc_seconds' or 'end_time_utc_seconds') is missing. Error: {e}")
        return
    except ValueError as e:
        print(f"ValueError: Could not convert time columns to datetime. Ensure they are Unix timestamps in seconds. Error: {e}")
        return
    except Exception as e: # Other potential errors during conversion
        print(f"An unexpected error occurred during time column conversion: {e}")
        return

    df_zigzag['start_time_jst'] = convert_to_jst(df_zigzag['start_time_dt'])
    df_zigzag['end_time_jst'] = convert_to_jst(df_zigzag['end_time_dt'])

    results = []

    unique_dates_jst = df_zigzag['start_time_jst'].dt.normalize().unique()
    print(f"Processing {len(unique_dates_jst)} unique dates.")

    for current_date_jst_norm in unique_dates_jst: 
        # 土日判定を追加
        is_weekend_day = is_weekend(current_date_jst_norm)
        
        for start_hour_jst, end_hour_jst in JST_TIME_RANGES:
            
            start_datetime_jst_tz = current_date_jst_norm.replace(hour=start_hour_jst, minute=0, second=0, microsecond=0)
            
            if end_hour_jst == 24:
                end_datetime_jst_tz = (current_date_jst_norm + pd.Timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                end_datetime_jst_tz = current_date_jst_norm.replace(hour=end_hour_jst, minute=0, second=0, microsecond=0)
            
            mask = (
                (df_zigzag['start_time_jst'] >= start_datetime_jst_tz) &
                (df_zigzag['start_time_jst'] < end_datetime_jst_tz)
            )
            
            legs_in_range = df_zigzag[mask]

            # データがない場合はNaNを設定
            price_movement = np.nan
            max_high_in_range = np.nan
            min_low_in_range = np.nan

            if not legs_in_range.empty:
                prices_in_legs = pd.concat([legs_in_range['start_price'], legs_in_range['end_price']]).dropna()
                
                if not prices_in_legs.empty:
                    max_high_in_range = float(prices_in_legs.max())
                    min_low_in_range = float(prices_in_legs.min())
                    price_movement = max_high_in_range - min_low_in_range
            
            results.append({
                "Date_JST": current_date_jst_norm.strftime('%Y-%m-%d'),
                "TimeRange_JST": f"{str(start_hour_jst).zfill(2)}:00-{str(end_hour_jst).zfill(2)}:00",
                "PriceMovement": price_movement,
                "MaxHigh_in_Range": max_high_in_range,
                "MinLow_in_Range": min_low_in_range,
                "IsWeekend": is_weekend_day,
                "Weekday": current_date_jst_norm.strftime('%A')  # 曜日名を追加（英語）
            })

    df_results = pd.DataFrame(results)
    
    # 数値の欠損値を「データなし」として扱う
    for col in ['PriceMovement', 'MaxHigh_in_Range', 'MinLow_in_Range']:
        # 数値をフォーマット（3桁小数点）し、NaNはNoneに置き換え
        df_results[col] = df_results[col].apply(lambda x: f'{x:.3f}' if pd.notnull(x) else None)
    
    output_dir = os.path.dirname(OUTPUT_CSV_PATH)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    df_results.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Volatility data saved to {OUTPUT_CSV_PATH}")
    print(f"Total records: {len(df_results)}")

if __name__ == "__main__":
    main() 