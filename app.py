import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="專業公差分析工具", layout="wide")

st.title("🛡️ 零件公差分析 (含 Cpk 良率預測)")

# 1. 側邊欄設定
with st.sidebar:
    st.header("全局設定")
    target_cpk = st.number_input("組合後的目標 Cpk", value=1.0, step=0.1)
    st.info("通常 Cpk=1.0 代表 3σ (99.73% 良率)，Cpk=1.33 代表 4σ。")

# 2. 輸入介面
st.subheader("1. 輸入零件資料")
num_parts = st.number_input("零件數量", min_value=1, max_value=50, value=3)

default_data = pd.DataFrame({
    "零件名稱": [f"Part {i+1}" for i in range(num_parts)],
    "名義尺寸 (mm)": [10.0] * num_parts,
    "公差 (+/- mm)": [0.05] * num_parts,
    "零件 Cpk": [1.0] * num_parts
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# 3. 計算邏輯
if st.button("🚀 執行進階分析", type="primary"):
    nominals = edited_df["名義尺寸 (mm)"].values
    tols = edited_df["公差 (+/- mm)"].values
    cpks = edited_df["零件 Cpk"].values
    
    # 計算每個零件的 Sigma (σ = Tol / (3 * Cpk))
    sigmas = tols / (3 * cpks)
    
    total_nom = np.sum(nominals)
    total_wc_tol = np.sum(tols)
    
    # 組合後的總 Sigma
    total_sigma = np.sqrt(np.sum(sigmas**2))
    # 在目標 Cpk 下的統計公差
    total_rss_tol = total_sigma * (3 * target_cpk)

    # 4. 顯示結果
    st.divider()
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("總名義尺寸", f"{total_nom:.3f} mm")
    res2.metric("Worst Case 公差", f"±{total_wc_tol:.3f} mm")
    res3.metric(f"RSS 公差 (Cpk={target_cpk})", f"±{total_rss_tol:.3f} mm")
    
    # 計算良率 (Yield)
    yield_rate = (norm.cdf(total_rss_tol, 0, total_sigma) - norm.cdf(-total_rss_tol, 0, total_sigma)) * 100
    res4.metric("預估良率", f"{yield_rate:.4f} %")

    # 5. 繪製圖表
    st.subheader("2. 尺寸分佈與公差界限")
    x = np.linspace(total_nom - 4*total_sigma, total_nom + 4*total_sigma, 200)
    y = norm.pdf(x, total_nom, total_sigma)
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, y, color='dodgerblue', lw=2, label='Predicted Distribution')
    ax.fill_between(x, y, alpha=0.2, color='dodgerblue')
    
    # 標示 RSS 範圍
    ax.axvline(total_nom + total_rss_tol, color='red', linestyle='--', label='Tolerance Limit')
    ax.axvline(total_nom - total_rss_tol, color='red', linestyle='--')
    
    ax.set_title(f"Assembly Distribution (Combined Sigma = {total_sigma:.4f})")
    ax.legend()
    st.pyplot(fig)
