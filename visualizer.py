"""
visualizer.py — matplotlib 图表生成

共 8 张图表：
  图1: 每餐消费金额直方图 + KDE
  图2: 消费金额箱线图（按性别分组）
  图3: 消费金额箱线图（按年级分组）
  图4: 消费金额箱线图（按生源地区域分组）
  图5: 食堂就餐时段偏好柱状图（多选题统计）
  图6: 菜品类型偏好饼图（多选题统计）
  图7: 月生活费区间柱状图
  图8: 量表满意度均值 ± SE 柱状图
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

from config import LIKERT_COLS, LIKERT_LABELS, OUTPUT_DIR
from data_cleaner import get_multi_select_stats


# ============================================================
# 图1: 每餐消费金额直方图 + KDE
# ============================================================
def plot_consumption_hist(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """直方图 + 核密度估计，展示每餐消费金额分布"""
    col = "per_meal_cost_num"
    if col not in df.columns:
        print("[visualizer] 跳过图1: 无 per_meal_cost_num 列")
        return

    data = df[col].dropna()
    if len(data) == 0:
        print("[visualizer] 跳过图1: 无有效数据")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    # 直方图
    ax.hist(data, bins=30, density=True, alpha=0.6, color="steelblue",
            edgecolor="white", label="频次密度")

    # KDE
    x_range = np.linspace(data.min(), data.max(), 500)
    kde = stats.gaussian_kde(data)
    ax.plot(x_range, kde(x_range), "r-", linewidth=2, label="核密度估计(KDE)")

    ax.axvline(data.mean(), color="green", linestyle="--", linewidth=1.5,
               label=f"均值 = {data.mean():.2f} 元")
    ax.axvline(data.median(), color="orange", linestyle="--", linewidth=1.5,
               label=f"中位数 = {data.median():.2f} 元")

    ax.set_xlabel("每餐消费金额 (元)", fontsize=12)
    ax.set_ylabel("概率密度", fontsize=12)
    ax.set_title("图1 每餐食堂消费金额分布直方图与核密度估计", fontsize=14)
    ax.legend(loc="upper right")
    fig.tight_layout()

    path = os.path.join(output_dir, "fig1_consumption_hist.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图1 已保存: {path}")


# ============================================================
# 图2: 消费金额箱线图（按性别分组）
# ============================================================
def plot_consumption_boxplot_gender(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """按性别分组的消费金额箱线图，标注异常值"""
    col = "per_meal_cost_num"
    if col not in df.columns or "gender" not in df.columns:
        print("[visualizer] 跳过图2: 缺少列")
        return

    groups = []
    labels = []
    colors = []
    for g, c, lbl in [("男", "lightblue", "男"), ("女", "lightpink", "女")]:
        vals = df[df["gender"] == g][col].dropna()
        if len(vals) > 0:
            groups.append(vals)
            labels.append(f"{lbl}\n(n={len(vals)})")
            colors.append(c)

    if len(groups) < 2:
        print("[visualizer] 跳过图2: 性别分组不足")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    bp = ax.boxplot(groups, labels=labels, patch_artist=True, widths=0.5)

    for box, c in zip(bp["boxes"], colors):
        box.set_facecolor(c)

    # 标注均值
    for i, g in enumerate(groups):
        ax.text(i + 1, g.mean() + 0.5, f"mean={g.mean():.1f}",
                ha="center", fontsize=10, color="red", fontweight="bold")

    ax.set_ylabel("每餐消费金额 (元)", fontsize=12)
    ax.set_title("图2 不同性别每餐消费金额箱线图", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig2_boxplot_gender.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图2 已保存: {path}")


# ============================================================
# 图3: 消费金额箱线图（按年级分组）
# ============================================================
def plot_consumption_boxplot_grade(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """按年级分组的消费金额箱线图"""
    col = "per_meal_cost_num"
    if col not in df.columns or "grade" not in df.columns:
        print("[visualizer] 跳过图3: 缺少列")
        return

    grade_order = ["大一", "大二", "大三", "大四及以上"]
    groups = []
    labels = []
    for g in grade_order:
        vals = df[df["grade"] == g][col].dropna()
        if len(vals) > 0:
            groups.append(vals)
            labels.append(f"{g}\n(n={len(vals)})")

    if len(groups) < 2:
        print("[visualizer] 跳过图3: 年级分组不足")
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    bp = ax.boxplot(groups, labels=labels, patch_artist=True, widths=0.5)

    grade_colors = ["#a29bfe", "#74b9ff", "#55efc4", "#ffeaa7"]
    for box, c in zip(bp["boxes"], grade_colors[:len(groups)]):
        box.set_facecolor(c)

    for i, g in enumerate(groups):
        ax.text(i + 1, g.mean() + 0.5, f"mean={g.mean():.1f}",
                ha="center", fontsize=9, color="red")

    ax.set_ylabel("每餐消费金额 (元)", fontsize=12)
    ax.set_title("图3 不同年级每餐消费金额箱线图", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig3_boxplot_grade.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图3 已保存: {path}")


# ============================================================
# 图4: 消费金额箱线图（按生源地区域分组）
# ============================================================
def plot_consumption_boxplot_region(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """按生源地区域分组的消费金额箱线图"""
    col = "per_meal_cost_num"
    if col not in df.columns or "hometown_region" not in df.columns:
        print("[visualizer] 跳过图4: 缺少列")
        return

    region_order = ["上海本地", "东部地区", "中部地区", "西部地区"]
    groups = []
    labels = []
    for r in region_order:
        vals = df[df["hometown_region"] == r][col].dropna()
        if len(vals) > 0:
            groups.append(vals)
            labels.append(f"{r}\n(n={len(vals)})")

    if len(groups) < 2:
        print("[visualizer] 跳过图4: 区域分组不足")
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    bp = ax.boxplot(groups, labels=labels, patch_artist=True, widths=0.5)

    region_colors = ["#e17055", "#00b894", "#0984e3", "#6c5ce7"]
    for box, c in zip(bp["boxes"], region_colors[:len(groups)]):
        box.set_facecolor(c)

    for i, g in enumerate(groups):
        ax.text(i + 1, g.mean() + 0.5, f"mean={g.mean():.1f}",
                ha="center", fontsize=9, color="red")

    ax.set_ylabel("每餐消费金额 (元)", fontsize=12)
    ax.set_title("图4 不同生源地区域每餐消费金额箱线图", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig4_boxplot_region.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图4 已保存: {path}")


# ============================================================
# 图5: 食堂就餐时段偏好柱状图（多选题统计）
# ============================================================
def plot_meal_period_bar(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """就餐时段偏好柱状图（多选题各选项被选次数）"""
    stats = get_multi_select_stats(df, "meal_periods")
    if stats.empty:
        print("[visualizer] 跳过图5: 无 meal_periods 统计数据")
        return

    fig, ax = plt.subplots(figsize=(9, 6))

    # 按频次排序
    stats_sorted = stats.sort_values(ascending=True)
    colors = ["#ffeaa7", "#fab1a0", "#81ecec", "#a29bfe", "#55efc4", "#fd79a8"]
    bars = ax.barh(stats_sorted.index, stats_sorted.values,
                   color=colors[:len(stats_sorted)], edgecolor="gray")

    for bar, v in zip(bars, stats_sorted.values):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{v}人 ({100*v/len(df):.1f}%)",
                va="center", fontsize=10)

    ax.set_xlabel("选择人数", fontsize=12)
    ax.set_ylabel("就餐时段", fontsize=12)
    ax.set_title("图5 食堂就餐时段偏好（多选题统计）", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig5_meal_period_bar.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图5 已保存: {path}")


# ============================================================
# 图6: 菜品类型偏好饼图（多选题统计）
# ============================================================
def plot_dish_type_pie(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """常点菜品类型占比饼图"""
    stats = get_multi_select_stats(df, "dish_types")
    if stats.empty:
        print("[visualizer] 跳过图6: 无 dish_types 统计数据")
        return

    fig, ax = plt.subplots(figsize=(8, 8))

    colors = ["#ff6b6b", "#feca57", "#48dbfb", "#ff9ff3", "#54a0ff", "#5f27cd",
              "#01a3a4", "#f368e0", "#ff6348", "#7bed9f"]
    explode = tuple(0.02 for _ in range(len(stats)))

    wedges, texts, autotexts = ax.pie(
        stats.values, labels=stats.index, autopct="%1.1f%%",
        explode=explode, colors=colors[:len(stats)], startangle=140,
        pctdistance=0.85
    )
    for t in autotexts:
        t.set_fontsize(9)
    for t in texts:
        t.set_fontsize(10)

    ax.set_title("图6 常点菜品类型占比（多选题统计）", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig6_dish_type_pie.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图6 已保存: {path}")


# ============================================================
# 图7: 月生活费区间柱状图
# ============================================================
def plot_living_expense_bar(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """月生活费区间分布柱状图"""
    col = "living_expense"
    if col not in df.columns:
        print("[visualizer] 跳过图7: 缺少列")
        return

    expense_order = ["1000元及以下", "1001-1500元", "1501-2000元",
                     "2001-2500元", "2501元以上"]
    counts = df[col].value_counts()
    counts = counts.reindex([e for e in expense_order if e in counts.index])

    if counts.empty:
        print("[visualizer] 跳过图7: 无有效数据")
        return

    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#74b9ff", "#55efc4", "#ffeaa7", "#fab1a0", "#a29bfe"]
    bars = ax.bar(counts.index, counts.values,
                  color=colors[:len(counts)], edgecolor="gray", width=0.6)

    for bar, v in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{v}人\n({100*v/len(df):.1f}%)",
                ha="center", fontsize=10, fontweight="bold")

    ax.set_xlabel("月生活费区间", fontsize=12)
    ax.set_ylabel("人数", fontsize=12)
    ax.set_title("图7 月生活费区间分布", fontsize=14)
    fig.tight_layout()

    path = os.path.join(output_dir, "fig7_living_expense_bar.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图7 已保存: {path}")


# ============================================================
# 图8: 量表满意度均值 ± SE 柱状图
# ============================================================
def plot_likert_bar(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """Q13-Q20 量表各维度满意度均值 ± 标准误"""
    likert_num_cols = [c + "_num" for c in LIKERT_COLS]
    available = [c for c in likert_num_cols if c in df.columns]

    if len(available) == 0:
        print("[visualizer] 跳过图8: 无数值列")
        return

    means = []
    ses = []
    labels = []
    for col, label in zip(available, LIKERT_LABELS):
        vals = df[col].dropna()
        if len(vals) > 0:
            means.append(vals.mean())
            ses.append(vals.std() / np.sqrt(len(vals)))
            labels.append(label)

    if len(means) == 0:
        print("[visualizer] 跳过图8: 无有效数据")
        return

    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(labels))
    colors = ["#ff6b6b", "#feca57", "#48dbfb", "#ff9ff3",
              "#54a0ff", "#5f27cd", "#01a3a4", "#ff6348"]
    bars = ax.bar(x, means, yerr=ses, capsize=6,
                  color=colors[:len(labels)], edgecolor="gray", width=0.6)

    # 标注数值
    for bar, m, se in zip(bars, means, ses):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + se + 0.03,
                f"{m:.2f}", ha="center", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=25, fontsize=10)
    ax.set_ylabel("满意度均值 (1-5)", fontsize=12)
    ax.set_title("图8 食堂各维度满意度均值 ± SE（5级量表）", fontsize=14)
    ax.set_ylim(1, 5.5)
    ax.axhline(y=3, color="gray", linestyle="--", linewidth=1, alpha=0.5, label="中立=3")
    ax.legend(loc="lower right")
    fig.tight_layout()

    path = os.path.join(output_dir, "fig8_likert_bar.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"[visualizer] 图8 已保存: {path}")


# ============================================================
# 批量生成所有图表
# ============================================================
def generate_all_plots(df: pd.DataFrame, output_dir: str = OUTPUT_DIR):
    """批量生成全部 8 张图表"""
    os.makedirs(output_dir, exist_ok=True)
    print("\n" + "=" * 60)
    print("  开始生成可视化图表...")
    print("=" * 60)

    plot_consumption_hist(df, output_dir)
    plot_consumption_boxplot_gender(df, output_dir)
    plot_consumption_boxplot_grade(df, output_dir)
    plot_consumption_boxplot_region(df, output_dir)
    plot_meal_period_bar(df, output_dir)
    plot_dish_type_pie(df, output_dir)
    plot_living_expense_bar(df, output_dir)
    plot_likert_bar(df, output_dir)

    print("=" * 60)
    print("  全部图表生成完成。")
    print("=" * 60)
