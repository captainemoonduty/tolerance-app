import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 頁面設定
st.set_page_config(page_title="公差分析工具", layout="centered")

st.title("📏 零件公差分析小程式")
st.write("輸入各零件的名義尺寸與公差，自動計算 Worst Case 與 RSS。")

# 1. 輸入介面
with st.container():
    st.subheader("1. 設定零件資料")
    num_parts = st.number_input("零件總數", min_value=1, max_value=50, value=3)
    
    # 使用 Data Editor 讓輸入更快速 (像 Excel 一樣填寫)
    default_data = pd.DataFrame({
        "零件名稱": [f"Part {i+1}" for i in range(num_parts)],
        "名義尺寸 (mm)": [10.0] * num_parts,
        "公差 (+/- mm)": [0.05] * num_parts
    })
    
    edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# 2. 計算邏輯
if st.button("🚀 執行公差分析", type="primary"):
    nominals = edited_df["名義尺寸 (mm)"].values
    tolerances = edited_df["公差 (+/- mm)"].values
    
    # 計算總和
    total_nom = np.sum(nominals)
    wc_tol = np.sum(tolerances)
    rss_tol = np.sqrt(np.sum(tolerances**2))
    
    # 顯示結果卡片
    st.divider()
    st.subheader("2. 分析結果")
    c1, c2, c3 = st.columns(3)
    c1.metric("總名義尺寸", f"{total_nom:.3f} mm")
    c2.metric("Worst Case (最差)", f"±{wc_tol:.3f} mm")
    c3.metric("RSS (統計)", f"±{rss_tol:.3f} mm")
    
    # 3. 視覺化圖表
    st.subheader("3. 尺寸分佈預測 (RSS)")
    mu = total_nom
    sigma = rss_tol / 3  # 假設為 3-sigma 分佈
    
    x = np.linspace(mu - 4*sigma, mu + 4*sigma, 100)
    y = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * ((x - mu) / sigma)**2)
    
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, color='#1f77b4', lw=2)
    ax.fill_between(x, y, alpha=0.3, color='#1f77b4')
    ax.axvline(mu + rss_tol, color='red', linestyle='--', label=f'RSS Limit (+{rss_tol:.3f})')
    ax.axvline(mu - rss_tol, color='red', linestyle='--', label=f'RSS Limit (-{rss_tol:.3f})')
    ax.set_xlabel("Dimension (mm)")
    ax.set_ylabel("Probability Density")
    ax.legend()
    
    st.pyplot(fig)
    
    st.success("分析完成！你可以根據 RSS 結果評估組裝良率。")
