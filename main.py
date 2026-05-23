"""
GROUP-XXX_main.py — 主分析脚本
用途：临港地区大学生食堂消费模式分析
     包含数据清洗、描述统计、可视化、四种统计模型
目标高校：上海海洋大学（SHOU）
置信度：alpha = 0.05

技术栈：numpy, pandas, matplotlib, scipy.stats, statsmodels
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from scipy import stats
from scipy.stats import (
    ttest_ind, f_oneway, chi2_contingency,
    shapiro, levene, norm
)
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
warnings.filterwarnings("ignore")

# ============================================================
# 0. 全局设置
# ============================================================
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120
ALPHA = 0.05
OUTPUT_DIR = r"c:\stat"

print("=" * 70)
print("  临港地区大学生食堂消费模式分析")
print("  上海海洋大学（SHOU）| alpha = 0.05")
print("=" * 70)

# ============================================================
# 1. 数据读取
# ============================================================
print("\n[1/6] 数据读取...")
DATA_PATH = r"c:\stat\GROUP-XXX_data.xlsx"

students = pd.read_excel(DATA_PATH, sheet_name="students")
dishes = pd.read_excel(DATA_PATH, sheet_name="dishes")
transactions = pd.read_excel(DATA_PATH, sheet_name="transactions")
survey = pd.read_excel(DATA_PATH, sheet_name="survey")

print(f"  students:     {students.shape}")
print(f"  dishes:       {dishes.shape}")
print(f"  transactions: {transactions.shape}")
print(f"  survey:       {survey.shape}")

# ============================================================
# 2. 数据清洗与整理
# ============================================================
print("\n[2/6] 数据清洗与整理...")

# 2.1 检查缺失值
print(f"  students 缺失值: {students.isnull().sum().sum()}")
print(f"  dishes 缺失值: {dishes.isnull().sum().sum()}")
print(f"  transactions 缺失值: {transactions.isnull().sum().sum()}")
print(f"  survey 缺失值: {survey.isnull().sum().sum()}")

# 2.2 检查重复值
print(f"  students 重复行: {students.duplicated().sum()}")
print(f"  transactions 重复行: {transactions.duplicated().sum()}")

# 2.3 异常值检测 — 基于 IQR 方法识别异常高/低消费
Q1 = transactions["amount"].quantile(0.25)
Q3 = transactions["amount"].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
outliers = transactions[(transactions["amount"] < lower_bound) | (transactions["amount"] > upper_bound)]
print(f"  消费金额 IQR: Q1={Q1:.2f}, Q3={Q3:.2f}, IQR={IQR:.2f}")
print(f"  异常值范围: < {lower_bound:.2f} 或 > {upper_bound:.2f}")
print(f"  异常消费记录: {len(outliers)} 条 ({100*len(outliers)/len(transactions):.2f}%)")

# 2.4 转换 timestamp 为 datetime
transactions["timestamp"] = pd.to_datetime(transactions["timestamp"])
transactions["date"] = transactions["timestamp"].dt.date
transactions["hour"] = transactions["timestamp"].dt.hour

# 2.5 计算每个学生的日均消费（用于后续分析）
# 按 student_id + date 聚合
daily_per_student = transactions.groupby(["student_id", "date"])["amount"].sum().reset_index()
daily_per_student.columns = ["student_id", "date", "daily_amount"]

# 每个学生的日均消费
avg_daily = daily_per_student.groupby("student_id")["daily_amount"].mean().reset_index()
avg_daily.columns = ["student_id", "avg_daily_consumption"]

# 合并到学生表
students_merged = students.merge(avg_daily, on="student_id", how="left")
students_merged["avg_daily_consumption"] = students_merged["avg_daily_consumption"].fillna(0)

# 2.6 合并消费数据与学生信息
trans_merged = transactions.merge(students[["student_id", "gender", "gender_label", "hometown_region",
                                              "hometown_label", "college", "college_label", "grade"]],
                                   on="student_id", how="left")

# 2.7 合并菜品价格档位信息
trans_merged = trans_merged.merge(dishes[["dish_id", "price_tier", "price_tier_label", "category", "category_label"]],
                                   on="dish_id", how="left")

# 2.8 计算每个学生的月均消费（基于30天数据）
monthly_consumption = daily_per_student.groupby("student_id")["daily_amount"].sum()
monthly_consumption = monthly_consumption.reset_index()
monthly_consumption.columns = ["student_id", "total_30day_consumption"]

# 2.9 定义消费档次（基于月均消费三分位数）
survey_full = survey.merge(students[["student_id", "gender", "gender_label", "hometown_region",
                                       "hometown_label", "college", "college_label", "grade"]],
                            on="student_id", how="left")

terciles = survey["monthly_consumption"].quantile([1/3, 2/3]).values
def classify_consumption_level(m):
    if m <= terciles[0]:
        return 0  # 低消费
    elif m <= terciles[1]:
        return 1  # 中消费
    else:
        return 2  # 高消费

survey_full["consumption_level"] = survey_full["monthly_consumption"].apply(classify_consumption_level)
level_labels = ["低消费", "中消费", "高消费"]
survey_full["consumption_level_label"] = [level_labels[l] for l in survey_full["consumption_level"]]

print(f"  消费档次划分 (三分位数): 低<={terciles[0]:.2f}, 中<={terciles[1]:.2f}, 高>{terciles[1]:.2f}")

# ============================================================
# 3. 描述性统计分析
# ============================================================
print("\n[3/6] 描述性统计分析...")

# 3.1 单笔消费金额总体分布
amounts = transactions["amount"]
print(f"\n  --- 单笔消费金额分布 ---")
print(f"  样本量: {len(amounts)}")
print(f"  均值: {amounts.mean():.2f} 元")
print(f"  中位数: {amounts.median():.2f} 元")
print(f"  标准差: {amounts.std():.2f} 元")
print(f"  偏度: {amounts.skew():.4f}")
print(f"  峰度: {amounts.kurtosis():.4f}")
print(f"  最小值: {amounts.min():.2f} 元")
print(f"  最大值: {amounts.max():.2f} 元")
print(f"  变异系数 CV: {amounts.std()/amounts.mean():.4f}")

# 3.2 学生日均消费分布
daily_means = avg_daily["avg_daily_consumption"]
print(f"\n  --- 学生日均消费分布 (n={len(daily_means)}) ---")
print(f"  均值: {daily_means.mean():.2f} 元/天")
print(f"  中位数: {daily_means.median():.2f} 元/天")
print(f"  标准差: {daily_means.std():.2f} 元/天")

# 3.3 不同价格档位消费分析
print(f"\n  --- 不同价格档位消费频次 ---")
tier_counts = trans_merged["price_tier_label"].value_counts()
for tier, cnt in tier_counts.items():
    print(f"  {tier}: {cnt} 次 ({100*cnt/len(trans_merged):.1f}%)")

tier_amount = trans_merged.groupby("price_tier_label")["amount"].agg(["mean", "std", "count"])
print(f"\n  --- 不同价格档位消费金额 ---")
print(tier_amount.to_string())

# 3.4 消费时段分析
print(f"\n  --- 各餐段消费分析 ---")
meal_stats = trans_merged.groupby("meal_period_label")["amount"].agg(["count", "mean", "std"])
meal_stats["pct"] = 100 * meal_stats["count"] / len(trans_merged)
print(meal_stats.to_string())

# 3.5 不同类别菜品消费占比
print(f"\n  --- 菜品类别消费占比 ---")
cat_counts = trans_merged["category_label"].value_counts()
for cat, cnt in cat_counts.items():
    print(f"  {cat}: {cnt} 次 ({100*cnt/len(trans_merged):.1f}%)")

# 3.6 按性别的消费对比
print(f"\n  --- 不同性别日均消费对比 ---")
gender_stats = students_merged.groupby("gender_label")["avg_daily_consumption"].agg(["mean", "std", "count"])
print(gender_stats.to_string())

# 3.7 按生源地的消费对比
print(f"\n  --- 不同生源地日均消费对比 ---")
hometown_stats = students_merged.groupby("hometown_label")["avg_daily_consumption"].agg(["mean", "std", "count"])
print(hometown_stats.to_string())

# 3.8 按学院的消费对比
print(f"\n  --- 不同学院日均消费对比 ---")
college_stats = students_merged.groupby("college_label")["avg_daily_consumption"].agg(["mean", "std", "count"])
print(college_stats.to_string())

# ============================================================
# 4. 数据可视化（matplotlib）
# ============================================================
print("\n[4/6] 生成可视化图表...")

# ----- 图1: 单笔消费金额直方图 + KDE -----
fig1, ax1 = plt.subplots(figsize=(10, 6))
ax1.hist(amounts, bins=40, density=True, alpha=0.6, color="steelblue", edgecolor="white", label="频次密度")
# KDE
x_range = np.linspace(amounts.min(), amounts.max(), 500)
kde = stats.gaussian_kde(amounts)
ax1.plot(x_range, kde(x_range), "r-", linewidth=2, label="核密度估计(KDE)")
ax1.axvline(amounts.mean(), color="green", linestyle="--", linewidth=1.5, label=f"均值={amounts.mean():.2f}")
ax1.axvline(amounts.median(), color="orange", linestyle="--", linewidth=1.5, label=f"中位数={amounts.median():.2f}")
ax1.set_xlabel("消费金额 (元)", fontsize=12)
ax1.set_ylabel("概率密度", fontsize=12)
ax1.set_title("图1 单笔食堂消费金额分布直方图与核密度估计", fontsize=14)
ax1.legend(loc="upper right")
fig1.savefig(r"c:\stat\fig1_amount_histogram.png", bbox_inches="tight")
plt.close(fig1)
print("  [OK] 图1: 消费金额直方图")

# ----- 图2: 消费金额箱线图（按性别） -----
fig2, ax2 = plt.subplots(figsize=(8, 6))
gender_groups = [students_merged[students_merged["gender_label"] == "女"]["avg_daily_consumption"],
                 students_merged[students_merged["gender_label"] == "男"]["avg_daily_consumption"]]
bp = ax2.boxplot(gender_groups, labels=["女", "男"], patch_artist=True, widths=0.5)
bp["boxes"][0].set_facecolor("lightpink")
bp["boxes"][1].set_facecolor("lightblue")
ax2.set_ylabel("日均消费 (元/天)", fontsize=12)
ax2.set_title("图2 不同性别学生日均消费箱线图", fontsize=14)
# 添加均值标注
for i, g in enumerate(gender_groups):
    ax2.text(i + 1, g.mean() + 1, f"mean={g.mean():.1f}", ha="center", fontsize=10, color="red")
fig2.savefig(r"c:\stat\fig2_gender_boxplot.png", bbox_inches="tight")
plt.close(fig2)
print("  [OK] 图2: 性别箱线图")

# ----- 图3: 不同价格档位消费金额箱线图 -----
fig3, ax3 = plt.subplots(figsize=(9, 6))
tier_labels_list = ["低价(≤5元)", "中价(5~10元)", "高价(>10元)"]
tier_groups = [trans_merged[trans_merged["price_tier_label"] == t]["amount"] for t in tier_labels_list]
bp3 = ax3.boxplot(tier_groups, labels=tier_labels_list, patch_artist=True, widths=0.5)
colors3 = ["#66c2a5", "#fc8d62", "#8da0cb"]
for patch, c in zip(bp3["boxes"], colors3):
    patch.set_facecolor(c)
ax3.set_ylabel("消费金额 (元)", fontsize=12)
ax3.set_title("图3 不同价格档位菜品消费金额箱线图", fontsize=14)
fig3.savefig(r"c:\stat\fig3_price_tier_boxplot.png", bbox_inches="tight")
plt.close(fig3)
print("  [OK] 图3: 价格档位箱线图")

# ----- 图4: 不同餐段消费频次柱状图 -----
fig4, ax4 = plt.subplots(figsize=(8, 6))
meal_counts = trans_merged["meal_period_label"].value_counts()
meal_order = ["早餐", "午餐", "晚餐", "夜宵"]
meal_counts = meal_counts.reindex(meal_order)
bars4 = ax4.bar(meal_order, meal_counts.values, color=["#ffeaa7", "#fab1a0", "#81ecec", "#a29bfe"], edgecolor="black")
for bar, v in zip(bars4, meal_counts.values):
    ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 100, str(v),
             ha="center", fontsize=11, fontweight="bold")
ax4.set_ylabel("消费频次", fontsize=12)
ax4.set_title("图4 不同餐段消费频次分布", fontsize=14)
fig4.savefig(r"c:\stat\fig4_meal_period_bar.png", bbox_inches="tight")
plt.close(fig4)
print("  [OK] 图4: 餐段柱状图")

# ----- 图5: 菜品类别消费占比饼图 -----
fig5, ax5 = plt.subplots(figsize=(8, 8))
cat_data = trans_merged["category_label"].value_counts()
explode = (0.02, 0.02, 0.02, 0.02, 0.02)
wedges, texts, autotexts = ax5.pie(cat_data.values, labels=cat_data.index, autopct="%1.1f%%",
                                     explode=explode, colors=["#ff6b6b", "#feca57", "#48dbfb", "#ff9ff3", "#54a0ff"],
                                     startangle=140)
for t in autotexts:
    t.set_fontsize(9)
ax5.set_title("图5 菜品类别消费占比饼图", fontsize=14)
fig5.savefig(r"c:\stat\fig5_category_pie.png", bbox_inches="tight")
plt.close(fig5)
print("  [OK] 图5: 菜品类别饼图")

# ----- 图6: 不同生源地月均消费均值 ± SE柱状图 -----
fig6, ax6 = plt.subplots(figsize=(9, 6))
hometown_order = ["上海本地", "东部地区", "中部地区", "西部地区"]
means6, ses6 = [], []
for h in hometown_order:
    vals = students_merged[students_merged["hometown_label"] == h]["avg_daily_consumption"]
    means6.append(vals.mean())
    ses6.append(vals.std() / np.sqrt(len(vals)))
bars6 = ax6.bar(hometown_order, means6, yerr=ses6, capsize=8, color=["#e17055", "#00b894", "#0984e3", "#6c5ce7"],
                edgecolor="black", width=0.5)
for bar, m in zip(bars6, means6):
    ax6.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f"{m:.2f}",
             ha="center", fontsize=10, fontweight="bold")
ax6.set_ylabel("日均消费均值 (元/天)", fontsize=12)
ax6.set_title("图6 不同生源地学生日均消费均值 ± SE", fontsize=14)
fig6.savefig(r"c:\stat\fig6_hometown_bar.png", bbox_inches="tight")
plt.close(fig6)
print("  [OK] 图6: 生源地柱状图")

# ----- 图7: 消费金额按小时分布（消费时段热力）-----
fig7, ax7 = plt.subplots(figsize=(10, 6))
hourly_counts = transactions.groupby("hour").size()
hours = range(24)
counts = [hourly_counts.get(h, 0) for h in hours]
colors7 = ["#dfe6e9" if (h < 6 or h > 22) else
           ("#ffeaa7" if 6 <= h <= 9 else
            ("#fab1a0" if 11 <= h <= 13 else
             ("#81ecec" if 16 <= h <= 19 else "#a29bfe")))
           for h in hours]
bars7 = ax7.bar(hours, counts, color=colors7, edgecolor="gray", width=0.8)
# 标注餐段
for start, end, label, y_pos in [(6, 9, "早餐", max(counts)),
                                   (11, 13, "午餐", max(counts)),
                                   (16, 19, "晚餐", max(counts)),
                                   (20, 22, "夜宵", max(counts))]:
    ax7.axvspan(start - 0.5, end + 0.5, alpha=0.1, color="yellow")
    ax7.text((start + end) / 2, y_pos * 0.95, label, ha="center", fontsize=11, fontweight="bold")
ax7.set_xlabel("小时 (24小时制)", fontsize=12)
ax7.set_ylabel("消费频次", fontsize=12)
ax7.set_title("图7 食堂消费时段分布（按小时）", fontsize=14)
ax7.set_xticks(hours)
fig7.savefig(r"c:\stat\fig7_hourly_pattern.png", bbox_inches="tight")
plt.close(fig7)
print("  [OK] 图7: 时段分布图")

# ----- 图8: 各学院日均消费箱线图 -----
fig8, ax8 = plt.subplots(figsize=(11, 6))
college_order = ["水产与生命学院", "食品学院", "海洋科学学院", "工程学院", "信息学院", "经济管理学院"]
college_groups = [students_merged[students_merged["college_label"] == c]["avg_daily_consumption"]
                  for c in college_order]
bp8 = ax8.boxplot(college_groups, labels=college_order, patch_artist=True, widths=0.5)
for patch in bp8["boxes"]:
    patch.set_facecolor("lightgreen")
ax8.set_ylabel("日均消费 (元/天)", fontsize=12)
ax8.set_title("图8 不同学院学生日均消费箱线图", fontsize=14)
ax8.tick_params(axis="x", rotation=30)
fig8.savefig(r"c:\stat\fig8_college_boxplot.png", bbox_inches="tight")
plt.close(fig8)
print("  [OK] 图8: 学院箱线图")

# ============================================================
# 5. 统计模型分析（四种方法，alpha=0.05）
# ============================================================
print("\n[5/6] 统计模型分析 (alpha = 0.05)...")

# ----- 方法一：独立样本 t 检验（性别消费差异）-----
print("\n  " + "=" * 60)
print("  方法一：独立样本 t 检验 — 不同性别日均消费差异")
print("  " + "=" * 60)

male_daily = students_merged[students_merged["gender"] == 1]["avg_daily_consumption"]
female_daily = students_merged[students_merged["gender"] == 0]["avg_daily_consumption"]

# H0: mu_male = mu_female, H1: mu_male != mu_female
print(f"  男生 (n={len(male_daily)}): 均值={male_daily.mean():.2f}, 标准差={male_daily.std():.2f}")
print(f"  女生 (n={len(female_daily)}): 均值={female_daily.mean():.2f}, 标准差={female_daily.std():.2f}")

# Levene 方差齐性检验
levene_stat, levene_p = levene(male_daily, female_daily)
print(f"  Levene 方差齐性检验: 统计量={levene_stat:.4f}, p={levene_p:.4f}")
equal_var = levene_p > ALPHA
print(f"  方差齐性: {'是' if equal_var else '否'} (p={levene_p:.4f} {'>' if equal_var else '<='} {ALPHA})")

# t 检验
t_stat, t_p = ttest_ind(male_daily, female_daily, equal_var=equal_var)
print(f"  t 检验: t={t_stat:.4f}, p={t_p:.4f}")
if t_p < ALPHA:
    print(f"  结论: p={t_p:.4f} < {ALPHA}, 拒绝 H0，男女生日均消费有显著差异。")
else:
    print(f"  结论: p={t_p:.4f} >= {ALPHA}, 不拒绝 H0，男女生日均消费无显著差异。")

# ----- 方法二：单因素方差分析（生源地消费差异）-----
print("\n  " + "=" * 60)
print("  方法二：单因素方差分析 (ANOVA) — 不同生源地日均消费差异")
print("  " + "=" * 60)

hometown_groups = []
hometown_names = ["上海本地", "东部地区", "中部地区", "西部地区"]
for h in range(4):
    group = students_merged[students_merged["hometown_region"] == h]["avg_daily_consumption"]
    hometown_groups.append(group)
    print(f"  {hometown_names[h]}: n={len(group)}, 均值={group.mean():.2f}, 标准差={group.std():.2f}")

# H0: mu1 = mu2 = mu3 = mu4, H1: 至少有一组不等
f_stat, anova_p = f_oneway(*hometown_groups)
print(f"  ANOVA: F={f_stat:.4f}, p={anova_p:.4f}")

if anova_p < ALPHA:
    print(f"  结论: p={anova_p:.4f} < {ALPHA}, 拒绝 H0，不同生源地日均消费有显著差异。")
    # 事后检验: Tukey HSD（手动实现）
    from itertools import combinations
    n_groups = len(hometown_groups)
    N_total = sum(len(g) for g in hometown_groups)
    # Tukey HSD 临界值
    df_error = N_total - n_groups
    q_critical = 3.633  # q(0.05, 4, df>>120) ≈ 3.63
    mse = sum((len(g) - 1) * g.var() for g in hometown_groups) / df_error

    print(f"  Tukey HSD 事后多重比较 (MSE={mse:.4f}, df_error={df_error}):")
    for (i, g1), (j, g2) in combinations(enumerate(hometown_groups), 2):
        diff = abs(g1.mean() - g2.mean())
        se = np.sqrt(mse * (1 / len(g1) + 1 / len(g2)))
        q_obs = diff / se
        sig = "显著" if q_obs > q_critical else "不显著"
        print(f"    {hometown_names[i]} vs {hometown_names[j]}: diff={diff:.2f}, q={q_obs:.2f} ({sig})")
else:
    print(f"  结论: p={anova_p:.4f} >= {ALPHA}, 不拒绝 H0，不同生源地日均消费无显著差异。")

# 学院 ANOVA
print(f"\n  --- 不同学院 ANOVA ---")
college_groups_anova = []
college_names = ["水产与生命学院", "食品学院", "海洋科学学院", "工程学院", "信息学院", "经济管理学院"]
for c in range(6):
    group = students_merged[students_merged["college"] == c]["avg_daily_consumption"]
    college_groups_anova.append(group)
    print(f"  {college_names[c]}: n={len(group)}, 均值={group.mean():.2f}, 标准差={group.std():.2f}")

f_stat_college, anova_p_college = f_oneway(*college_groups_anova)
print(f"  ANOVA (学院): F={f_stat_college:.4f}, p={anova_p_college:.4f}")
if anova_p_college < ALPHA:
    print(f"  结论: 不同学院日均消费有显著差异 (p={anova_p_college:.4f})。")
else:
    print(f"  结论: 不同学院日均消费无显著差异 (p={anova_p_college:.4f})。")

# ----- 方法三：多元线性回归（影响食堂消费的因素）-----
print("\n  " + "=" * 60)
print("  方法三：多元线性回归 — 影响食堂消费的因素分析")
print("  " + "=" * 60)

# 准备回归数据
# 因变量: monthly_consumption (来自 survey)
# 自变量: gender, hometown_region, grade, taste_score, price_score, service_score, health_score, env_score, variety_score
reg_data = survey_full.dropna(subset=["monthly_consumption"])

X_vars = ["gender", "hometown_region", "grade", "taste_score", "price_score",
          "service_score", "health_score", "env_score", "variety_score"]
X = reg_data[X_vars]
X = sm.add_constant(X)
y = reg_data["monthly_consumption"]

# OLS 回归
model = sm.OLS(y, X).fit()
print(model.summary())

# 模型解释
print(f"\n  模型整体显著性: F={model.fvalue:.4f}, p={model.f_pvalue:.6f}")
print(f"  拟合优度 R-squared: {model.rsquared:.4f}")
print(f"  调整 R-squared: {model.rsquared_adj:.4f}")

# 显著性变量
print(f"\n  在 alpha={ALPHA} 水平下显著的变量:")
for var in X_vars:
    pval = model.pvalues[var]
    coef = model.params[var]
    if pval < ALPHA:
        print(f"    {var}: coef={coef:.4f}, p={pval:.4f} *** 显著")
    elif pval < 0.01:
        print(f"    {var}: coef={coef:.4f}, p={pval:.4f} **")
    elif pval < 0.05:
        print(f"    {var}: coef={coef:.4f}, p={pval:.4f} *")
    else:
        print(f"    {var}: coef={coef:.4f}, p={pval:.4f} (不显著)")

# 模型诊断：VIF 多重共线性
print(f"\n  VIF 多重共线性检验:")
for i, var in enumerate(X_vars):
    vif = variance_inflation_factor(X[X_vars].values, i)
    print(f"    {var}: VIF={vif:.2f} {'(严重共线性!)' if vif > 10 else '(轻微共线性)' if vif > 5 else ''}")

# Breusch-Pagan 异方差检验
bp_test = het_breuschpagan(model.resid, model.model.exog)
print(f"\n  Breusch-Pagan 异方差检验: LM={bp_test[0]:.4f}, p={bp_test[1]:.4f}")
if bp_test[1] < ALPHA:
    print(f"  结论: 存在异方差 (p={bp_test[1]:.4f})，建议使用稳健标准误。")
else:
    print(f"  结论: 无异方差 (p={bp_test[1]:.4f})。")

# 残差正态性 — Shapiro-Wilk
shapiro_stat, shapiro_p = shapiro(model.resid[:500])  # 前500个以避免大样本偏误
print(f"  残差正态性 (Shapiro-Wilk, n=500): W={shapiro_stat:.4f}, p={shapiro_p:.4f}")

# ----- 模型修正：精简回归（处理多重共线性）-----
print(f"\n  --- 模型修正 (精简回归，消除多重共线性) ---")
# 用 overall_satisfaction 替代高度相关的 6 个满意度分项
# 新模型: Y ~ gender + hometown_region + grade + overall_satisfaction
X_vars_revised = ["gender", "hometown_region", "grade", "overall_satisfaction"]
X_revised = reg_data[X_vars_revised]
X_revised = sm.add_constant(X_revised)

model_revised = sm.OLS(y, X_revised).fit()
print(model_revised.summary())

print(f"\n  修正模型拟合优度: R^2={model_revised.rsquared:.4f}, Adj R^2={model_revised.rsquared_adj:.4f}")
print(f"  F={model_revised.fvalue:.4f}, p={model_revised.f_pvalue:.6f}")

# 修正模型 VIF
print(f"\n  修正模型 VIF:")
for i, var in enumerate(X_vars_revised):
    vif_r = variance_inflation_factor(X_revised[X_vars_revised].values, i)
    print(f"    {var}: VIF={vif_r:.2f}")

# 修正模型 Breusch-Pagan
bp_revised = het_breuschpagan(model_revised.resid, model_revised.model.exog)
print(f"\n  修正模型 Breusch-Pagan: LM={bp_revised[0]:.4f}, p={bp_revised[1]:.4f}")

# 模型比较
print(f"\n  --- 模型比较 ---")
print(f"  全模型:   R^2={model.rsquared:.4f}, Adj R^2={model.rsquared_adj:.4f}, AIC={model.aic:.2f}")
print(f"  修正模型: R^2={model_revised.rsquared:.4f}, Adj R^2={model_revised.rsquared_adj:.4f}, AIC={model_revised.aic:.2f}")
print(f"  修正模型消除了多重共线性，整体满意度(overall_satisfaction)系数={model_revised.params['overall_satisfaction']:.4f}, p={model_revised.pvalues['overall_satisfaction']:.4f}")

# ----- 图9: 回归残差诊断图 -----
fig9, axes9 = plt.subplots(2, 2, figsize=(12, 10))

# Q-Q plot
stats.probplot(model.resid, dist="norm", plot=axes9[0, 0])
axes9[0, 0].set_title("残差 Q-Q 图", fontsize=12)

# Residuals vs fitted
axes9[0, 1].scatter(model.fittedvalues, model.resid, alpha=0.5, s=20)
axes9[0, 1].axhline(y=0, color="r", linestyle="--")
axes9[0, 1].set_xlabel("拟合值", fontsize=11)
axes9[0, 1].set_ylabel("残差", fontsize=11)
axes9[0, 1].set_title("残差 vs 拟合值", fontsize=12)

# 残差直方图
axes9[1, 0].hist(model.resid, bins=25, density=True, color="steelblue", alpha=0.6, edgecolor="white")
x_hist = np.linspace(model.resid.min(), model.resid.max(), 200)
axes9[1, 0].plot(x_hist, norm.pdf(x_hist, 0, model.resid.std()), "r-", linewidth=2)
axes9[1, 0].set_xlabel("残差", fontsize=11)
axes9[1, 0].set_title("残差直方图 + 正态曲线", fontsize=12)

# Scale-Location
axes9[1, 1].scatter(model.fittedvalues, np.sqrt(np.abs(model.resid)), alpha=0.5, s=20)
axes9[1, 1].set_xlabel("拟合值", fontsize=11)
axes9[1, 1].set_ylabel("sqrt(|残差|)", fontsize=11)
axes9[1, 1].set_title("Scale-Location 图", fontsize=12)

plt.suptitle("图9 多元线性回归残差诊断图", fontsize=14, fontweight="bold")
plt.tight_layout()
fig9.savefig(r"c:\stat\fig9_regression_diagnostics.png", bbox_inches="tight")
plt.close(fig9)
print("  [OK] 图9: 回归诊断图")

# ----- 方法四：卡方独立性检验（性别 × 消费档次）-----
print("\n  " + "=" * 60)
print("  方法四：卡方独立性检验 — 性别与消费档次的关联分析")
print("  " + "=" * 60)

# 构建列联表
contingency = pd.crosstab(survey_full["gender_label"], survey_full["consumption_level_label"])
print(f"\n  列联表 (性别 × 消费档次):")
print(contingency)
print()

# H0: 性别与消费档次独立, H1: 性别与消费档次不独立
chi2, chi2_p, dof, expected = chi2_contingency(contingency)
print(f"  卡方检验: chi2={chi2:.4f}, df={dof}, p={chi2_p:.4f}")
print(f"  期望频次表:")
print(pd.DataFrame(expected, index=contingency.index, columns=contingency.columns).round(2))

if chi2_p < ALPHA:
    print(f"  结论: p={chi2_p:.4f} < {ALPHA}, 拒绝 H0，性别与消费档次显著相关。")
    # 计算 Cramer's V 效应量
    n_total = contingency.sum().sum()
    cramer_v = np.sqrt(chi2 / (n_total * min(contingency.shape[0] - 1, contingency.shape[1] - 1)))
    print(f"  Cramer's V (效应量): {cramer_v:.4f}")
else:
    print(f"  结论: p={chi2_p:.4f} >= {ALPHA}, 不拒绝 H0，性别与消费档次无显著关联。")

# ============================================================
# 6. 结果汇总
# ============================================================
print("\n[6/6] 分析结果汇总")
print("=" * 70)

print("""
┌─────────────────────────────────────────────────────────────────────┐
│                    统计分析结果汇总 (alpha=0.05)                      │
├─────────────────────────────────────────────────────────────────────┤
│ 方法一: 独立样本 t 检验 (性别)                                       │
│   t={:.4f}, p={:.4f}                                         │
│   结论: 男女生日均消费{}显著差异                                      │
├─────────────────────────────────────────────────────────────────────┤
│ 方法二: 单因素 ANOVA (生源地)                                        │
│   F={:.4f}, p={:.4f}                                         │
│   结论: 不同生源地{}显著差异                                          │
├─────────────────────────────────────────────────────────────────────┤
│ 方法三: 多元线性回归 (消费影响因素)                                   │
│   R^2={:.4f}, Adj R^2={:.4f}, F={:.4f}, p={:.6f}        │
│   显著因素: 见模型摘要                                               │
├─────────────────────────────────────────────────────────────────────┤
│ 方法四: 卡方独立性检验 (性别 × 消费档次)                              │
│   chi2={:.4f}, df={}, p={:.4f}                                  │
│   结论: 性别与消费档次{}显著关联                                      │
└─────────────────────────────────────────────────────────────────────┘
""".format(
    t_stat, t_p,
    "有" if t_p < ALPHA else "无",
    f_stat, anova_p,
    "有" if anova_p < ALPHA else "无",
    model.rsquared, model.rsquared_adj, model.fvalue, model.f_pvalue,
    chi2, dof, chi2_p,
    "有" if chi2_p < ALPHA else "无"
))

print("[OK] 所有分析完成！")
print(f"[OK] 图表保存至: {OUTPUT_DIR}")
print("[OK] 最终数据保存至: c:\\stat\\GROUP-XXX_analysis_results.xlsx")

# 输出分析结果汇总表
with pd.ExcelWriter(r"c:\stat\GROUP-XXX_analysis_results.xlsx", engine="openpyxl") as writer:
    # 描述统计
    summary_data = {
        "指标": ["单笔消费均值(元)", "单笔消费中位数(元)", "单笔消费标准差(元)",
                 "学生日均消费均值(元)", "学生日均消费标准差(元)",
                 "月均消费均值(元)-问卷", "问卷总体满意度均值(1-5)", "有效消费记录数"],
        "数值": [amounts.mean(), amounts.median(), amounts.std(),
                 daily_means.mean(), daily_means.std(),
                 survey["monthly_consumption"].mean(), survey["overall_satisfaction"].mean(),
                 len(transactions)]
    }
    pd.DataFrame(summary_data).to_excel(writer, sheet_name="描述统计", index=False)

    # 性别统计
    gender_summary = students_merged.groupby("gender_label")["avg_daily_consumption"].agg(
        ["count", "mean", "std", "min", "max"]).reset_index()
    gender_summary.to_excel(writer, sheet_name="性别对比", index=False)

    # 回归结果
    reg_results = pd.DataFrame({
        "变量": ["const"] + X_vars,
        "系数": model.params,
        "标准误": model.bse,
        "t值": model.tvalues,
        "p值": model.pvalues,
        "95%CI_下": model.conf_int()[0],
        "95%CI_上": model.conf_int()[1],
    })
    reg_results.to_excel(writer, sheet_name="回归结果", index=False)

    # 列联表
    contingency.to_excel(writer, sheet_name="性别消费列联表")

print("\n" + "=" * 70)
print("  分析完成。请查看 c:\\stat\\ 目录下的图表和结果文件。")
print("=" * 70)
