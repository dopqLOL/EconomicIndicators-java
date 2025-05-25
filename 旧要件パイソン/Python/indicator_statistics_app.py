import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from PIL import Image

# 入力ファイルパス設定
INDICATOR_STATS_PATH = "../csv/Statistics/indicator_statistics.csv"
CATEGORY_STATS_PATH = "../csv/Statistics/category_statistics.csv"
PLOTS_DIR = "../plots"

def load_data():
    """データの読み込み"""
    try:
        indicator_stats = pd.read_csv(INDICATOR_STATS_PATH)
        category_stats = pd.read_csv(CATEGORY_STATS_PATH)
        return indicator_stats, category_stats
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None, None

def plot_volatility_distribution(data):
    """ボラティリティ分布のプロット"""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.histplot(data['PriceMovement_mean'], bins=30, kde=True, ax=ax)
    ax.set_title('Distribution of Mean Volatility by Indicator')
    ax.set_xlabel('Mean Volatility')
    ax.set_ylabel('Count')
    return fig

def main():
    st.set_page_config(
        page_title="経済指標ボラティリティ分析",
        page_icon="📊",
        layout="wide",
    )
    
    st.title("経済指標ボラティリティ分析ツール")
    st.write("経済指標別のボラティリティ統計量を表示・分析するためのツールです。")
    
    # データの読み込み
    indicator_stats, category_stats = load_data()
    
    if indicator_stats is None or category_stats is None:
        st.error("データの読み込みに失敗しました。ファイルパスを確認してください。")
        return
    
    # サイドバー：フィルタリングオプション
    st.sidebar.header("フィルタリングオプション")
    
    # 通貨でフィルタリング
    all_currencies = ["全て"] + sorted(indicator_stats["Currency"].unique().tolist())
    selected_currency = st.sidebar.selectbox("通貨", all_currencies)
    
    # カテゴリでフィルタリング
    all_categories = ["全て"] + sorted(indicator_stats["Volatility_Category"].unique().tolist())
    selected_category = st.sidebar.selectbox("ボラティリティカテゴリ", all_categories)
    
    # 最小サンプル数でフィルタリング
    min_samples = st.sidebar.slider("最小サンプル数", 
                                   min_value=int(indicator_stats["PriceMovement_count"].min()), 
                                   max_value=int(indicator_stats["PriceMovement_count"].max()),
                                   value=5)
    
    # データのフィルタリング
    filtered_data = indicator_stats.copy()
    
    if selected_currency != "全て":
        filtered_data = filtered_data[filtered_data["Currency"] == selected_currency]
    
    if selected_category != "全て":
        filtered_data = filtered_data[filtered_data["Volatility_Category"] == selected_category]
    
    filtered_data = filtered_data[filtered_data["PriceMovement_count"] >= min_samples]
    
    # ソートオプション
    sort_options = {
        "平均ボラティリティ（降順）": ("PriceMovement_mean", False),
        "平均ボラティリティ（昇順）": ("PriceMovement_mean", True),
        "サンプル数（降順）": ("PriceMovement_count", False),
        "サンプル数（昇順）": ("PriceMovement_count", True),
        "標準偏差（降順）": ("PriceMovement_std", False),
        "標準偏差（昇順）": ("PriceMovement_std", True),
    }
    
    selected_sort = st.sidebar.selectbox("ソート順", list(sort_options.keys()))
    sort_col, sort_asc = sort_options[selected_sort]
    
    filtered_data = filtered_data.sort_values(by=sort_col, ascending=sort_asc)
    
    # メイン画面のレイアウト
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("指標別ボラティリティ統計量")
        st.write(f"フィルタリング結果: {len(filtered_data)} 件の指標が表示されています")
        
        # データテーブルの表示列を選択
        display_cols = [
            "Currency", "EventName", "Volatility_Category",
            "PriceMovement_mean", "PriceMovement_median", 
            "PriceMovement_std", "PriceMovement_min", 
            "PriceMovement_max", "PriceMovement_count"
        ]
        
        # 列名の日本語表示用マッピング
        col_mapping = {
            "Currency": "通貨",
            "EventName": "指標名",
            "Volatility_Category": "カテゴリ",
            "PriceMovement_mean": "平均",
            "PriceMovement_median": "中央値",
            "PriceMovement_std": "標準偏差",
            "PriceMovement_min": "最小",
            "PriceMovement_max": "最大",
            "PriceMovement_count": "サンプル数"
        }
        
        # 表示用のデータフレームを作成
        display_df = filtered_data[display_cols].copy()
        display_df = display_df.rename(columns=col_mapping)
        
        # データテーブルの表示
        st.dataframe(display_df, use_container_width=True)
        
        # CSVダウンロードボタン
        csv = filtered_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="CSVダウンロード",
            data=csv,
            file_name="filtered_indicator_statistics.csv",
            mime="text/csv",
        )
    
    with col2:
        st.header("ボラティリティカテゴリ統計")
        
        # カテゴリ統計の表示
        st.dataframe(category_stats, use_container_width=True)
        
        # 可視化セクション
        st.header("可視化")
        
        # プロットの表示方法
        plot_option = st.selectbox(
            "表示するプロット",
            ["1. ボラティリティ分布", "2. 通貨別ボラティリティ", "3. サンプル数とボラティリティの関係"]
        )
        
        if plot_option == "1. ボラティリティ分布":
            # 保存したプロットがあれば読み込み、なければ生成
            plot_path = f"{PLOTS_DIR}/volatility_distribution.png"
            if os.path.exists(plot_path):
                image = Image.open(plot_path)
                st.image(image, caption="指標別平均ボラティリティの分布")
            else:
                fig = plot_volatility_distribution(filtered_data)
                st.pyplot(fig)
        
        elif plot_option == "2. 通貨別ボラティリティ":
            plot_path = f"{PLOTS_DIR}/volatility_by_currency.png"
            if os.path.exists(plot_path):
                image = Image.open(plot_path)
                st.image(image, caption="通貨別のボラティリティ分布")
            else:
                fig, ax = plt.subplots(figsize=(12, 8))
                sns.boxplot(x='Currency', y='PriceMovement_mean', data=filtered_data, ax=ax)
                ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
                ax.set_title('Volatility Distribution by Currency')
                st.pyplot(fig)
        
        elif plot_option == "3. サンプル数とボラティリティの関係":
            plot_path = f"{PLOTS_DIR}/samples_vs_volatility.png"
            if os.path.exists(plot_path):
                image = Image.open(plot_path)
                st.image(image, caption="サンプル数とボラティリティの関係")
            else:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.scatterplot(x='PriceMovement_count', y='PriceMovement_mean', 
                               hue='Currency', data=filtered_data, ax=ax)
                ax.set_title('Sample Count vs Mean Volatility')
                st.pyplot(fig)
    
    # 詳細分析セクション
    st.header("詳細分析")
    
    # 通貨別の平均ボラティリティ
    st.subheader("通貨別の平均ボラティリティ")
    currency_volatility = indicator_stats.groupby('Currency')['PriceMovement_mean'].mean().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    currency_volatility.plot(kind='bar', ax=ax)
    ax.set_title('Average Volatility by Currency')
    ax.set_ylabel('Mean Volatility')
    st.pyplot(fig)
    
    # カテゴリ別の指標数分布
    st.subheader("カテゴリ別の指標数分布")
    category_counts = indicator_stats['Volatility_Category'].value_counts()
    
    fig, ax = plt.subplots(figsize=(8, 6))
    category_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax)
    ax.set_title('Distribution of Indicators by Volatility Category')
    st.pyplot(fig)
    
    # フッター
    st.markdown("---")
    st.caption("© 2024 GoldEventAnalyzer - 経済指標ボラティリティ分析ツール")

if __name__ == "__main__":
    main() 