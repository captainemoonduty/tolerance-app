import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="專業公差分析工具", layout="wide")

st.title("📏 零件 vs 成品規格公差分析")

# 1. 零件資料輸入
st.subheader("1. 輸入各零件公差 (零件層級)")
num_parts = st.number_input("零件數量", min_value=1, max_value=50, value=3)

# 初始化預設表格
default_data = pd.DataFrame({
    "零件名稱": [f"Part {i+1}" for i in range(num_parts)],
    "名義尺寸": [10.0] * num_parts,
    "上公差 (+)": [0.05] * num_parts,
    "下公差 (-)": [0.05] * num_parts,
    "零件 Cpk": [1.33] * num_parts
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# 核心計算：零件總和
total_nom_sum = edited_df["名義尺寸"].sum()

# 2. 側邊欄：成品目標規格設定
with st.sidebar:
    st.header("🎯 成品目標規格 (Spec)")
    
    auto_calc = st.checkbox("自動連動零件尺寸總和", value=True)
    
    if auto_calc:
        # 使用 st.session_state 或直接賦值，確保連動同步
        spec_nominal = total_nom_sum
        st.write(f"成品目標尺寸: {spec_nominal:.3f}")
    else:
        spec_nominal = st.number_input("成品名義尺寸目標", value=total_nom_sum, step=0.1, format="%.3f")
        
    spec_upper_limit = st.number_input("成品允收上公差 (+)", value=0.20, min_value=0.0, step=0.01, format="%.3f")
    spec_lower_limit = st.number_input("成品允收下公差 (-)", value=0.20, min_value=0.0, step=0.01, format="%.3f")
    
    st.divider()
    st.info(f"成品規格範圍：\n{spec_nominal - spec_lower_limit:.3f} ~ {spec_nominal + spec_upper_limit:.3f}")

# 3. 分析計算
if st.button("🚀 執行對比分析", type="primary"):
    nominals = edited_df["名義尺寸"].values
    u_tols = edited_df["上公差 (+)"].values
    l_tols = edited_df["下公差 (-)"].values
    cpks = edited_df["零件 Cpk"].values
    
    # 統計計算
    total_nom = np.sum(nominals)
    wc_upper = np.sum(u_tols)
    wc_lower = np.sum(l_tols)
    
    sigmas_u = u_tols / (3 * cpks)
    sigmas_l = l_tols / (3 * cpks)
    total_sigma_u = np.sqrt(np.sum(sigmas_u**2))
    total_sigma_l = np.sqrt(np.sum(sigmas_l**2))

    # 成品界限
    USL = spec_nominal + spec_upper_limit
    LSL = spec_nominal - spec_lower_limit
    mean_shift = total_nom - spec_nominal
    
    # Cpk 與 良率
    # 避免除以 0
    tsu = max(total_sigma_u, 0.000001)
    tsl = max(total_sigma_l, 0.000001)
    
    cpk_u = (spec_upper_limit - mean_shift) / (3 * tsu)
    cpk_l = (spec_lower_limit + mean_shift) / (3 * tsl)
    final_cpk = min(cpk_u, cpk_l)
    
    # 修正良率計算公式
    yield_u = norm.cdf(spec_upper_limit, mean_shift, tsu)
    yield_l = norm.cdf(-spec_lower_limit, mean_shift, tsl)
    total_yield = (yield_u - yield_l) * 100

    # 4. 結果顯示
    st.divider()
    st.subheader("2. 分析結果總結")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("零件總名義尺寸", f"{total_nom:.3f} mm")
    c2.metric("預估 Cpk", f"{final_cpk:.3f}")
    c3.metric("預估良率", f"{max(0, total_yield):.4f} %")
    
    # 判定 Worst Case
    is_wc_ok = (total_nom + wc_upper <= USL + 0.0001) and (total_nom - wc_lower >= LSL - 0.0001)
    c4.metric("Worst Case 判定", "通過" if is_wc_ok else "超出規格", delta_color="normal" if is_wc_ok else "inverse")

    # 5. 繪圖
    st.subheader("3. 尺寸分佈對比圖")
    
    # 設定 X 軸範圍
    display_sigma = max(tsu, tsl)
    plot_min = min(LSL, total_nom - 4 * display_sigma)
    plot_max = max(USL, total_nom + 4 * display_sigma)
    x = np.linspace(plot_min, plot_max, 500)
    
    # 非對稱分佈曲線
    y = np.where(x < total_nom, norm.pdf(x, total_nom, tsl), norm.pdf(x, total_nom, tsu))
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, y, color='#2E86C1', lw=2, label='Assembly Distribution')
    # 確保這裡寫完整: fill_between
    ax.fill_between(x, y, alpha=0.2, color='#2E86C1')
    
    # 標示成品規格界限
    ax.axvline(USL, color='red', lw=2, linestyle='-', label=f'Spec Upper ({USL:.3f})')
    ax.axvline(LSL, color='red', lw=2, linestyle='-', label=f'Spec Lower ({LSL:.3f})')
    
    # 標示名義尺寸位置
    ax.axvline(total_nom, color='gray', lw=1, linestyle='--', label='Mean')

    ax.set_title("Assembly Distribution vs. Product Spec Limits")
    ax.set_xlabel("Dimension (mm)")
    ax.legend()
    st.pyplot(fig)
