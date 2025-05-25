import pandas as pd
import numpy as np
import os
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# 入出力ファイルパス設定
INPUT_PATH = "../csv/MergedData/indicators_with_volatility.csv"
OUTPUT_PATH = "../csv/Statistics/indicator_statistics.csv"
CATEGORY_OUTPUT_PATH = "../csv/Statistics/category_statistics.csv"
PLOTS_DIR = "../plots"

def main():
    print(f"Current working directory: {os.getcwd()}")
    
    # マージ済みデータの読み込み
    print(f"Loading merged data from {INPUT_PATH}...")
    try:
        df = pd.read_csv(INPUT_PATH)
        print(f"Loaded {len(df)} records.")
        print(f"Data columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # 無効なボラティリティデータを持つ行を除外
    df_valid = df.dropna(subset=['PriceMovement'])
    print(f"Records with valid volatility data: {len(df_valid)} ({len(df_valid)/len(df)*100:.2f}%)")
    
    # 列のデータ型を確認・変換
    numeric_cols = ['PriceMovement', 'MaxHigh_in_Range', 'MinLow_in_Range']
    for col in numeric_cols:
        if col in df_valid.columns:
            df_valid[col] = pd.to_numeric(df_valid[col], errors='coerce')
    
    # 国名と指標名でグループ化して統計量を計算
    print("Calculating statistics for each indicator...")
    stats = df_valid.groupby(['Currency', 'EventName']).agg({
        'PriceMovement': [
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
    
    # 小数点以下の桁数を制限
    float_cols = [col for col in stats.columns if stats[col].dtype == 'float64']
    for col in float_cols:
        stats[col] = stats[col].round(3)
    
    # データ件数でフィルタリング（サンプル数が少ない指標は除外）
    min_samples = 5
    stats_filtered = stats[stats['PriceMovement_count'] >= min_samples]
    print(f"Filtered indicators with at least {min_samples} samples: {len(stats_filtered)} out of {len(stats)}")
    
    # 平均ボラティリティに基づいてカテゴリ分類（三分位数を使用）
    print("Categorizing indicators based on mean volatility...")
    
    # 三分位数の計算
    q1 = stats_filtered['PriceMovement_mean'].quantile(0.33)
    q2 = stats_filtered['PriceMovement_mean'].quantile(0.67)
    
    # カテゴリ列の追加
    def get_category(x):
        if x < q1:
            return "小"
        elif x < q2:
            return "中"
        else:
            return "大"
    
    stats_filtered['Volatility_Category'] = stats_filtered['PriceMovement_mean'].apply(get_category)
    
    # カテゴリ別の統計量
    category_stats = stats_filtered.groupby('Volatility_Category').agg({
        'PriceMovement_mean': ['mean', 'min', 'max', 'count']
    })
    
    # マルチインデックスを解除
    category_stats.columns = ['_'.join(col).strip() for col in category_stats.columns.values]
    category_stats = category_stats.reset_index()
    
    # 出力ディレクトリの作成
    output_dir = Path(OUTPUT_PATH).parent
    plots_dir = Path(PLOTS_DIR)
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    if not plots_dir.exists():
        plots_dir.mkdir(parents=True, exist_ok=True)
    
    # 結果の保存
    stats_filtered.to_csv(OUTPUT_PATH, index=False)
    category_stats.to_csv(CATEGORY_OUTPUT_PATH, index=False)
    
    print(f"Statistics saved to {OUTPUT_PATH}")
    print(f"Category statistics saved to {CATEGORY_OUTPUT_PATH}")
    
    # デバッグ用：データの一部をプレビュー表示
    print("\n===== データプレビュー =====")
    
    # 通貨別の平均ボラティリティ
    print("\n1. 通貨別の平均ボラティリティ:")
    currency_volatility = stats_filtered.groupby('Currency')['PriceMovement_mean'].mean().sort_values(ascending=False)
    for currency, mean in currency_volatility.items():
        print(f"{currency}: {mean:.3f}")
    
    # ボラティリティが最も高い指標（上位10件）
    print("\n2. ボラティリティが最も高い指標（上位10件）:")
    top_volatile = stats_filtered.sort_values('PriceMovement_mean', ascending=False).head(10)
    for _, row in top_volatile.iterrows():
        print(f"{row['Currency']} {row['EventName']}: {row['PriceMovement_mean']:.3f} (サンプル数: {int(row['PriceMovement_count'])})")
    
    # ボラティリティカテゴリの分布
    print("\n3. ボラティリティカテゴリの分布:")
    category_counts = stats_filtered['Volatility_Category'].value_counts()
    for category, count in category_counts.items():
        print(f"{category}: {count} 指標")
    
    # カテゴリ別の平均ボラティリティ
    print("\n4. カテゴリ別の平均ボラティリティ:")
    for _, row in category_stats.iterrows():
        print(f"{row['Volatility_Category']}: 平均 {row['PriceMovement_mean_mean']:.3f}, 指標数: {int(row['PriceMovement_mean_count'])}")
    
    # 可視化：ボラティリティの分布
    print("\n5. 可視化グラフを生成中...")
    
    # 1. ヒストグラム：指標別平均ボラティリティの分布
    plt.figure(figsize=(10, 6))
    sns.histplot(stats_filtered['PriceMovement_mean'], bins=30, kde=True)
    plt.title('Distribution of Mean Volatility by Indicator')
    plt.xlabel('Mean Volatility')
    plt.ylabel('Count')
    plt.savefig(f"{PLOTS_DIR}/volatility_distribution.png")
    
    # 2. 箱ひげ図：通貨別のボラティリティ分布
    plt.figure(figsize=(12, 8))
    sns.boxplot(x='Currency', y='PriceMovement_mean', data=stats_filtered.sort_values('PriceMovement_mean', ascending=False))
    plt.title('Volatility Distribution by Currency')
    plt.xlabel('Currency')
    plt.ylabel('Mean Volatility')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/volatility_by_currency.png")
    
    # 3. 散布図：サンプル数とボラティリティの関係
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x='PriceMovement_count', y='PriceMovement_mean', hue='Currency', data=stats_filtered)
    plt.title('Sample Count vs Mean Volatility')
    plt.xlabel('Number of Samples')
    plt.ylabel('Mean Volatility')
    plt.tight_layout()
    plt.savefig(f"{PLOTS_DIR}/samples_vs_volatility.png")
    
    print(f"Visualization plots saved to {PLOTS_DIR}/")

if __name__ == "__main__":
    main() 