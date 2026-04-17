import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["font.family"] = "DejaVu Sans"
matplotlib.rcParams["axes.unicode_minus"] = False

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="高等統計品質報告｜牛仔褲腰圍製程管制",
    page_icon="📊",
    layout="wide",
)

st.title("📊 高等統計品質報告｜牛仔褲腰圍製程管制")
st.markdown("使用 **X-bar R** 與 **X-bar S** 管制圖分析牛仔褲腰圍製程品質")

# ── Constants ─────────────────────────────────────────────────────
ABNORMAL_BASE = [15, 16, 17, 32, 33]

CLR = {
    "blue":   "#2c7bb6",
    "green":  "#1a9641",
    "purple": "#756bb1",
    "red":    "#d7191c",
}

# ── Control chart constants ───────────────────────────────────────
XR_CONSTANTS = {
    3: {"A2": 1.023, "D3": 0.000, "D4": 2.574},
    4: {"A2": 0.729, "D3": 0.000, "D4": 2.282},
    5: {"A2": 0.577, "D3": 0.000, "D4": 2.114},
}

def c4(n):
    return 4 * (n - 1) / (4 * n - 3)

# ── Helpers ───────────────────────────────────────────────────────
def generate_data(mean, std, shift, n, subgroups):
    abnormal = [b for b in ABNORMAL_BASE if b <= subgroups]
    records = []
    for b in range(1, subgroups + 1):
        m = mean + shift if b in abnormal else mean
        vals = np.random.normal(m, std, n)
        for v in vals:
            records.append({"batch": b, "value": round(v, 4)})
    return pd.DataFrame(records), abnormal

def get_ooc(values, ucl, lcl):
    return [i + 1 for i, v in enumerate(values) if v > ucl or v < lcl]

def add_ooc_markers(ax, batches, values, ooc_list):
    for b in ooc_list:
        idx = b - 1
        ax.plot(batches[idx], values[idx], "rv", markersize=10, zorder=5, label="_nolegend_")

def add_limit_labels(ax, x_end, pairs):
    for val, label, color in pairs:
        ax.text(x_end + 0.3, val, label, color=color, fontsize=8, va="center")

# ══════════════════════════════════════════════════════════════════
# Sidebar controls
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("⚙️ 製程參數設定")

    chart_type = st.radio("管制圖類型", ["X-bar & R Chart", "X-bar & S Chart"])

    st.divider()
    st.subheader("製程參數")
    mean  = st.slider("目標腰圍（吋）",  min_value=30.0, max_value=34.0, value=32.0, step=0.1)
    std   = st.slider("標準差（吋）",    min_value=0.1,  max_value=1.0,  value=0.3,  step=0.05)
    shift = st.slider("異常批次偏移量（吋）", min_value=0.0, max_value=3.0, value=1.0, step=0.1)

    st.divider()
    st.subheader("抽樣設定")

    if chart_type == "X-bar & R Chart":
        n         = st.slider("每批抽樣數 n（R Chart 適用 n≤5）", min_value=3, max_value=5,  value=5, step=1)
        subgroups = st.slider("批次數量",  min_value=20, max_value=40, value=40, step=1)
    else:
        n         = st.slider("每批抽樣數 n（S Chart 適用 n>10）", min_value=10, max_value=30, value=12, step=1)
        subgroups = st.slider("批次數量",  min_value=20, max_value=60, value=40, step=1)

    regenerate = st.button("🔄 重新模擬資料", use_container_width=True)

# ── Generate data ─────────────────────────────────────────────────
# Use session state so data only regenerates on button press
if "df" not in st.session_state or regenerate:
    st.session_state.df, st.session_state.abnormal = generate_data(mean, std, shift, n, subgroups)
    st.session_state.params = (mean, std, shift, n, subgroups)

df      = st.session_state.df
abnormal = st.session_state.abnormal

# Recalculate stats every time sliders change
stats = df.groupby("batch")["value"].agg(
    xbar="mean",
    R=lambda x: x.max() - x.min(),
    S="std",
).reset_index()

batches   = stats["batch"].tolist()
xbar_vals = stats["xbar"].tolist()
x_end     = subgroups + 0.5

xbar_bar = np.mean(xbar_vals)

# ══════════════════════════════════════════════════════════════════
# X-bar & R Chart
# ══════════════════════════════════════════════════════════════════
if chart_type == "X-bar & R Chart":
    c = XR_CONSTANTS[n]
    A2, D3, D4 = c["A2"], c["D3"], c["D4"]

    R_vals = stats["R"].tolist()
    R_bar  = np.mean(R_vals)

    UCLx = xbar_bar + A2 * R_bar
    LCLx = xbar_bar - A2 * R_bar
    UCLR = D4 * R_bar
    LCLR = D3 * R_bar

    ooc_x = get_ooc(xbar_vals, UCLx, LCLx)
    ooc_r = get_ooc(R_vals,    UCLR, LCLR)

    # ── Metrics row ──
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("X̄ 總平均",   f"{xbar_bar:.4f} 吋")
    col2.metric("R̄ 全距均值", f"{R_bar:.4f} 吋")
    col3.metric("UCL (X̄)",    f"{UCLx:.4f}")
    col4.metric("LCL (X̄)",    f"{LCLx:.4f}")

    # ── Plot ──
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), tight_layout=True, sharex=True)
    fig.suptitle(f"X-bar & R Control Chart  |  n={n}, Subgroups={subgroups}", fontsize=13, fontweight="bold")

    # X-bar chart
    ax1.plot(batches, xbar_vals, "o-", color=CLR["blue"], markersize=4, linewidth=1.5, label="Subgroup Mean")
    ax1.axhline(xbar_bar, linestyle="--", color=CLR["blue"], linewidth=1, label=f"CL = {xbar_bar:.3f}")
    ax1.axhline(UCLx, color=CLR["red"], linewidth=1.5, label=f"UCL = {UCLx:.3f}")
    ax1.axhline(LCLx, color=CLR["red"], linewidth=1.5, label=f"LCL = {LCLx:.3f}")
    add_ooc_markers(ax1, batches, xbar_vals, ooc_x)
    add_limit_labels(ax1, x_end, [
        (UCLx,     f"UCL={UCLx:.3f}",     CLR["red"]),
        (xbar_bar, f"CL ={xbar_bar:.3f}", CLR["blue"]),
        (LCLx,     f"LCL={LCLx:.3f}",     CLR["red"]),
    ])
    ax1.set_xlim(0.5, x_end + 2)
    ax1.set_ylabel("腰圍平均值（吋）")
    ax1.set_title("X-bar Chart")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.legend(fontsize=8, loc="upper left")

    # R chart
    ax2.plot(batches, R_vals, "s-", color=CLR["green"], markersize=4, linewidth=1.5, label="Subgroup Range")
    ax2.axhline(R_bar, linestyle="--", color=CLR["green"], linewidth=1, label=f"CL = {R_bar:.3f}")
    ax2.axhline(UCLR, color=CLR["red"], linewidth=1.5, label=f"UCL = {UCLR:.3f}")
    ax2.axhline(LCLR, color=CLR["red"], linewidth=1.5, label=f"LCL = {LCLR:.3f}")
    add_ooc_markers(ax2, batches, R_vals, ooc_r)
    add_limit_labels(ax2, x_end, [
        (UCLR,  f"UCL={UCLR:.3f}",  CLR["red"]),
        (R_bar, f"CL ={R_bar:.3f}", CLR["green"]),
        (LCLR,  f"LCL={LCLR:.3f}",  CLR["red"]),
    ])
    ax2.set_xlim(0.5, x_end + 2)
    ax2.set_ylabel("批次全距（吋）")
    ax2.set_xlabel("批次編號")
    ax2.set_title("R Chart")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    ax2.legend(fontsize=8, loc="upper left")

    st.pyplot(fig)

    # ── Summary ──
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("X-bar Chart 管制界限")
        st.dataframe(pd.DataFrame({
            "界限": ["UCL", "中心線 CL", "LCL"],
            "數值": [f"{UCLx:.4f}", f"{xbar_bar:.4f}", f"{LCLx:.4f}"],
        }), hide_index=True)
        if ooc_x:
            st.error(f"⚠️ 超出管制界限的批次：{ooc_x}")
        else:
            st.success("✅ X-bar 所有批次均在管制界限內")

    with col_b:
        st.subheader("R Chart 管制界限")
        st.dataframe(pd.DataFrame({
            "界限": ["UCL", "中心線 CL", "LCL"],
            "數值": [f"{UCLR:.4f}", f"{R_bar:.4f}", f"{LCLR:.4f}"],
        }), hide_index=True)
        if ooc_r:
            st.error(f"⚠️ 超出管制界限的批次：{ooc_r}")
        else:
            st.success("✅ R 所有批次均在管制界限內")

# ══════════════════════════════════════════════════════════════════
# X-bar & S Chart
# ══════════════════════════════════════════════════════════════════
else:
    _c4  = c4(n)
    A3   = 3 / (_c4 * np.sqrt(n))
    B3   = max(0.0, 1 - 3 / (_c4 * np.sqrt(2 * (n - 1))))
    B4   = 1 + 3 / (_c4 * np.sqrt(2 * (n - 1)))

    S_vals = stats["S"].tolist()
    S_bar  = np.mean(S_vals)

    UCLx = xbar_bar + A3 * S_bar
    LCLx = xbar_bar - A3 * S_bar
    UCLS = B4 * S_bar
    LCLS = B3 * S_bar

    ooc_x = get_ooc(xbar_vals, UCLx, LCLx)
    ooc_s = get_ooc(S_vals,    UCLS, LCLS)

    # ── Metrics row ──
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("X̄ 總平均",      f"{xbar_bar:.4f} 吋")
    col2.metric("S̄ 標準差均值", f"{S_bar:.4f} 吋")
    col3.metric("UCL (X̄)",       f"{UCLx:.4f}")
    col4.metric("LCL (X̄)",       f"{LCLx:.4f}")

    # ── Plot ──
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6), tight_layout=True, sharex=True)
    fig.suptitle(f"X-bar & S Control Chart  |  n={n}, Subgroups={subgroups}", fontsize=13, fontweight="bold")

    # X-bar chart
    ax1.plot(batches, xbar_vals, "o-", color=CLR["blue"], markersize=4, linewidth=1.5, label="Subgroup Mean")
    ax1.axhline(xbar_bar, linestyle="--", color=CLR["blue"], linewidth=1, label=f"CL = {xbar_bar:.3f}")
    ax1.axhline(UCLx, color=CLR["red"], linewidth=1.5, label=f"UCL = {UCLx:.3f}")
    ax1.axhline(LCLx, color=CLR["red"], linewidth=1.5, label=f"LCL = {LCLx:.3f}")
    add_ooc_markers(ax1, batches, xbar_vals, ooc_x)
    add_limit_labels(ax1, x_end, [
        (UCLx,     f"UCL={UCLx:.3f}",     CLR["red"]),
        (xbar_bar, f"CL ={xbar_bar:.3f}", CLR["blue"]),
        (LCLx,     f"LCL={LCLx:.3f}",     CLR["red"]),
    ])
    ax1.set_xlim(0.5, x_end + 2)
    ax1.set_ylabel("腰圍平均值（吋）")
    ax1.set_title("X-bar Chart")
    ax1.grid(axis="y", linestyle=":", alpha=0.5)
    ax1.legend(fontsize=8, loc="upper left")

    # S chart
    ax2.plot(batches, S_vals, "s-", color=CLR["purple"], markersize=4, linewidth=1.5, label="Subgroup Std Dev")
    ax2.axhline(S_bar, linestyle="--", color=CLR["purple"], linewidth=1, label=f"CL = {S_bar:.3f}")
    ax2.axhline(UCLS, color=CLR["red"], linewidth=1.5, label=f"UCL = {UCLS:.3f}")
    ax2.axhline(LCLS, color=CLR["red"], linewidth=1.5, label=f"LCL = {LCLS:.3f}")
    add_ooc_markers(ax2, batches, S_vals, ooc_s)
    add_limit_labels(ax2, x_end, [
        (UCLS,  f"UCL={UCLS:.3f}",  CLR["red"]),
        (S_bar, f"CL ={S_bar:.3f}", CLR["purple"]),
        (LCLS,  f"LCL={LCLS:.3f}",  CLR["red"]),
    ])
    ax2.set_xlim(0.5, x_end + 2)
    ax2.set_ylabel("批次標準差（吋）")
    ax2.set_xlabel("批次編號")
    ax2.set_title("S Chart")
    ax2.grid(axis="y", linestyle=":", alpha=0.5)
    ax2.legend(fontsize=8, loc="upper left")

    st.pyplot(fig)

    # ── Summary ──
    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("X-bar Chart 管制界限")
        st.dataframe(pd.DataFrame({
            "界限": ["UCL", "中心線 CL", "LCL"],
            "數值": [f"{UCLx:.4f}", f"{xbar_bar:.4f}", f"{LCLx:.4f}"],
        }), hide_index=True)
        if ooc_x:
            st.error(f"⚠️ 超出管制界限的批次：{ooc_x}")
        else:
            st.success("✅ X-bar 所有批次均在管制界限內")

    with col_b:
        st.subheader("S Chart 管制界限")
        st.dataframe(pd.DataFrame({
            "界限": ["UCL", "中心線 CL", "LCL"],
            "數值": [f"{UCLS:.4f}", f"{S_bar:.4f}", f"{LCLS:.4f}"],
        }), hide_index=True)
        if ooc_s:
            st.error(f"⚠️ 超出管制界限的批次：{ooc_s}")
        else:
            st.success("✅ S 所有批次均在管制界限內")

# ── Raw data ──────────────────────────────────────────────────────
st.divider()
with st.expander("📋 查看原始批次統計資料"):
    st.dataframe(stats.rename(columns={
        "batch": "批次",
        "xbar": "平均值 X̄",
        "R": "全距 R",
        "S": "標準差 S",
    }), hide_index=True, use_container_width=True)

abn_str = "、".join(str(b) for b in abnormal) if abnormal else "無"
st.caption(f"模擬設定：目標均值 {mean} 吋 | 標準差 {std} 吋 | 異常批次偏移 {shift} 吋 | 異常批次：{abn_str}")
