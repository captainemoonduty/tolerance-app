import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="不專業公差分析工具", layout="wide")

st.title("📏 零件 vs 成品規格公差分析")
st.write("設定各零件公差，並自定義成品的「目標規格界限」，自動計算 Cpk 與良率。")

# 1. 側邊欄：成品目標規格設定 (Spec Limits)
with st.sidebar:
    st.header("🎯 成品目標規格 (Spec)")
    spec_nominal = st.number_input("成品名義尺寸目標", value=30.0, step=0.1, format="%.3f")
    spec_upper_limit = st.number_input("成品允收上公差 (+)", value=0.20, min_value=0.0, step=0.01, format="%.3f")
    spec_lower_limit = st.number_input("成品允收下公差 (-)", value=0.20, min_value=0.0, step=0.01, format="%.3f")
    
    st.divider()
    st.info(f"成品規格範圍：\n{spec_nominal - spec_lower_limit:.3f} ~ {spec_nominal + spec_upper_limit:.3f}")

# 2. 零件資料輸入
st.subheader("1. 輸入各零件公差 (零件層級)")
num_parts = st.number_input("零件數量", min_value=1, max_value=50, value=3)

default_data = pd.DataFrame({
    "零件名稱": [f"Part {i+1}" for i in range(num_parts)],
    "名義尺寸": [10.0] * num_parts,
    "上公差 (+)": [0.05] * num_parts,
    "下公差 (-)": [0.05] * num_parts,
    "零件 Cpk": [1.33] * num_parts
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# 3. 分析計算
if st.button("🚀 執行公差對比分析", type="primary"):
    nominals = edited_df["名義尺寸"].values
    u_tols = edited_df["上公差 (+)"].values
    l_tols = edited_df["下公差 (-)"].values
    cpks = edited_df["零件 Cpk"].values
    
    # --- A. 零件疊加計算 ---
    total_nom = np.sum(nominals)
    # Worst Case
    wc_upper = np.sum(u_tols)
    wc_lower = np.sum(l_tols)
    # RSS (Sigma 計算)
    sigmas_u = u_tols / (3 * cpks)
    sigmas_l = l_tols / (3 * cpks)
    total_sigma_u = np.sqrt(np.sum(sigmas_u**2))
    total_sigma_l = np.sqrt(np.sum(sigmas_l**2))

    # --- B. 對比成品規格 (Spec Limits) ---
    USL = spec_nominal + spec_upper_limit
    LSL = spec_nominal - spec_lower_limit
    
    # 計算相對於成品目標的位移 (Shift)
    # 如果零件疊加的名義總和與成品目標名義尺寸不同，會產生偏移
    mean_shift = total_nom - spec_nominal
    
    # 計算成品 Cpk
    # Cpk = min( (USL - Mean)/3sigma, (Mean - LSL)/3sigma )
    cpk_u = (spec_upper_limit - mean_shift) / (3 * total_sigma_u)
    cpk_l = (spec_lower_limit + mean_shift) / (3 * total_sigma_l)
    final_cpk = min(cpk_u, cpk_l)
    
    # 計算良率
    yield_u = norm.cdf(spec_upper_limit, mean_shift, total_sigma_u)
    yield_l = norm.cdf(-spec_lower_limit, mean_shift, total_sigma_l)
    total_yield = (yield_u - yield_l) * 100

    # 4. 顯示結果
    st.divider()
    st.subheader("2. 分析結果對比")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("零件疊加總尺寸", f"{total_nom:.3f} mm", f"偏離目標 {mean_shift:.3f}", delta_color="inverse")
    c2.metric("成品預估 Cpk", f"{final_cpk:.3f}")
    c3.metric("預估良率 (Yield)", f"{total_yield:.4f} %")
    
    # 判斷 Worst Case 是否爆表
    is_wc_ok = (total_nom + wc_upper <= USL) and (total_nom - wc_lower >= LSL)
    c4.metric("Worst Case 判定", "通過" if is_wc_ok else "超出規格", delta_color="normal" if is_wc_ok else "inverse")

    # 5. 視覺化：零件分佈 vs 成品規格
    st.subheader("3. 尺寸分佈與成品規格界限對比")
    
    # 繪圖範圍
    plot_min = min(LSL, total_nom - 4*total_sigma_l)
    plot_max = max(USL, total_nom + 4*total_sigma_u)
    x = np.linspace(plot_min - 0.1, plot_max + 0.1, 500)
    
    # 分佈曲線
    y = np.where(x < total_nom, 
                 norm.pdf(x, total_nom, total_sigma_l), 
                 norm.pdf(x, total_nom, total_sigma_u))
    
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(x, y, color='#2E86C1', lw=2, label='Assembly Distribution')
    ax.fill_between(x, y, alpha=0.2, color='#2E86C1')
    
    # 畫出成品 Spec Limits (目標規格)
    ax.axvline(USL, color='red', lw=2, label=f'Spec Upper ({USL:.3f})')
    ax.axvline(LSL, color='red', lw=2, label=f'Spec Lower ({LSL:.3f})')
    
    # 畫出 Worst Case 範圍 (陰影)
    ax.axvspan(total_nom - wc_lower, total_nom + wc_upper, color='gray', alpha=0.1, label='Worst Case Range')
    
    ax.set_title("Distribution vs. Product Specifications")
    ax.set_xlabel("Dimension (mm)")
    ax.legend(loc='upper right')
    st.pyplot(fig)

    if not is_wc_ok:
        st.warning("⚠️ 注意：Worst Case 計算結果已超出成品規格上限或下限。")
