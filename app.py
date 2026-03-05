import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="進階非對稱公差分析", layout="wide")

st.title("📏 進階公差分析 (支援非對稱公差與 Cpk)")
st.write("各零件可獨立設定上/下公差，系統將自動計算成品目標界限。")

# 1. 側邊欄：全局設定
with st.sidebar:
    st.header("⚙️ 全局設定")
    target_cpk = st.number_input("成品目標 Cpk", value=1.0, min_value=0.1, step=0.1)
    st.info("計算 RSS 時，會依據此 Cpk 縮放統計公差界限。")

# 2. 資料輸入區
st.subheader("1. 輸入零件公差資料")
num_parts = st.number_input("零件數量", min_value=1, max_value=50, value=3)

# 建立預設表格（拆分上下公差）
default_data = pd.DataFrame({
    "零件名稱": [f"Part {i+1}" for i in range(num_parts)],
    "名義尺寸": [10.0] * num_parts,
    "上公差 (+)": [0.05] * num_parts,
    "下公差 (-)": [0.02] * num_parts,
    "零件 Cpk": [1.0] * num_parts
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# 3. 分析計算
if st.button("🚀 執行非對稱分析", type="primary"):
    nominals = edited_df["名義尺寸"].values
    u_tols = edited_df["上公差 (+)"].values
    l_tols = edited_df["下公差 (-)"].values
    cpks = edited_df["零件 Cpk"].values
    
    # --- 計算 Worst Case ---
    total_nom = np.sum(nominals)
    total_wc_upper = np.sum(u_tols)
    total_wc_lower = np.sum(l_tols)
    
    # --- 計算 RSS (統計公差) ---
    # 對於非對稱公差，RSS 通常分別計算上限與下限的平方和
    # 計算各零件單邊的 Sigma: σ = Tolerance / (3 * Cpk)
    sigmas_u = u_tols / (3 * cpks)
    sigmas_l = l_tols / (3 * cpks)
    
    total_sigma_u = np.sqrt(np.sum(sigmas_u**2))
    total_sigma_l = np.sqrt(np.sum(sigmas_l**2))
    
    # 根據目標 Cpk 計算統計界限
    rss_upper = total_sigma_u * (3 * target_cpk)
    rss_lower = total_sigma_l * (3 * target_cpk)

    # 4. 顯示結果卡片
    st.divider()
    st.subheader("2. 分析結果總結")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("總名義尺寸 (Nominal)", f"{total_nom:.3f} mm")
    
    # Worst Case 顯示
    wc_text = f"+{total_wc_upper:.3f} / -{total_wc_lower:.3f}"
    c2.metric("Worst Case 總界限", wc_text)
    
    # RSS 顯示
    rss_text = f"+{rss_upper:.3f} / -{rss_lower:.3f}"
    c3.metric(f"RSS 統計界限 (Cpk={target_cpk})", rss_text)

    # 5. 良率評估 (採用較差的那一邊作為保守估計)
    avg_total_sigma = (total_sigma_u + total_sigma_l) / 2
    # 簡化模型：計算在 RSS 界限內的機率
    yield_u = norm.cdf(rss_upper, 0, total_sigma_u)
    yield_l = norm.cdf(rss_lower, 0, total_sigma_l)
    total_yield = (yield_u + yield_l - 1) * 100
    
    st.info(f"💡 預估組裝良率：**{total_yield:.4f}%** (基於非對稱分佈模型)")

    # 6. 視覺化圖表
    st.subheader("3. 尺寸分佈圖 (非對稱分佈)")
    
    # 繪圖範圍：取較大的那一邊擴張
    max_range = max(rss_upper, rss_lower) * 1.5
    x = np.linspace(total_nom - max_range, total_nom + max_range, 400)
    
    # 建立一個簡單的非對稱正態分佈模擬 (分段正態)
    y = np.where(x < total_nom, 
                 norm.pdf(x, total_nom, total_sigma_l), 
                 norm.pdf(x, total_nom, total_sigma_u))
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, y, color='#2E86C1', lw=2)
    ax.fill_between(x, y, alpha=0.3, color='#2E86C1')
    
    # 畫出 RSS 上下限
    ax.axvline(total_nom + rss_upper, color='red', linestyle='--', label=f'Upper Limit (+{rss_upper:.3f})')
    ax.axvline(total_nom - rss_lower, color='red', linestyle='--', label=f'Lower Limit (-{rss_lower:.3f})')
    
    ax.set_title("Assembly Dimension Distribution (Asymmetric)")
    ax.set_xlabel("Dimension (mm)")
    ax.legend()
    st.pyplot(fig)
