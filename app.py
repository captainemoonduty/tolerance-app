import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

st.set_page_config(page_title="不專業公差分析工具", layout="wide")

st.title("📏 零件 vs 成品規格公差分析")

# 1. 零件資料輸入 (先輸入零件，以便計算總和)
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
    
    # 新增自動計算開關
    auto_calc = st.checkbox("自動連動零件尺寸總和", value=True)
    
    if auto_calc:
        spec_nominal = st.number_input("成品名義尺寸目標 (已自動連動)", value=total_nom_sum, format="%.3f", disabled=True)
    else:
        spec_nominal = st.number_input("成品名義尺寸目標 (手動設定)", value=total_nom_sum, step=0.1, format="%.3f")
        
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
    cpk_u = (spec_upper_limit - mean_shift) / (3 * total_sigma_u)
    cpk_l = (spec_lower_limit + mean_shift) / (3 * total_sigma_l)
    final_cpk = min(cpk_u, cpk_l)
    
    yield_u = norm.cdf(spec_upper_limit, mean_shift, total_sigma_u)
    yield_l = norm.cdf(-spec_lower_limit, mean_shift, total_sigma_l)
    total_yield = (yield_u - yield_l) * 100

    # 4. 結果顯示
    st.divider()
    st.subheader("2. 分析結果總結")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("零件總名義尺寸", f"{total_nom:.3f} mm")
    c2.metric("預估 Cpk", f"{final_cpk:.3f}")
    c3.metric("預估良率", f"{total_yield:.4f} %")
    
    is_wc_ok = (total_nom + wc_upper <= USL + 0.00001) and (total_nom - wc_lower >= LSL - 0.00001)
    c4.metric("Worst Case 判定", "通過" if is_wc_ok else "超出規格", delta_color="normal" if is_wc_ok else "inverse")

    # 5. 繪圖
    st.subheader("3. 尺寸分佈對比圖")
    plot_range = max(wc_upper, wc_lower, spec_upper_limit, spec_lower_limit) * 1.5
    x = np.linspace(total_nom - plot_range, total_nom + plot_range, 500)
    y = np.where(x < total_nom, norm.pdf(x, total_nom, total_sigma_l), norm.pdf(x, total_nom, total_sigma_u))
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, y, color='#2E86C1', lw=2)
    ax.fill_
