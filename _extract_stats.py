"""临时脚本：提取清洗后数据的完整描述性统计（修复多选统计）"""
import pandas as pd
import numpy as np
from data_cleaner import clean_survey_data

# 从原始数据重新清洗以填充多选缓存
df_raw = pd.read_excel("大学生食堂消费模式调查问卷.xlsx", sheet_name="Sheet1")
df = clean_survey_data(df_raw)

N = len(df)

def pct(count):
    return f"{100 * count / N:.1f}%"

# 输出到文件避免终端乱码
lines = []
def w(s=""):
    lines.append(s)
    print(s)

w("=" * 60)
w(f"  描述性统计汇总 (N = {N})")
w("=" * 60)

w("\n--- 1) 性别分布 ---")
for k, v in df["gender"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 2) 年级分布 ---")
for k, v in df["grade"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 3) 生源地区域分布 ---")
for k, v in df["hometown_region"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 4) 每月生活费区间分布 ---")
expense_order = ["1000元及以下", "1001-1500元", "1501-2000元", "2001-2500元", "2501元以上"]
vc = df["living_expense"].value_counts()
for e in expense_order:
    vv = vc.get(e, 0)
    w(f"  {e}: {vv} ({pct(vv)})")

w("\n--- 5) 每日去食堂次数 ---")
for k, v in df["daily_visits"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 6) 工作日就餐频率 ---")
for k, v in df["weekday_freq"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 7) 周末就餐频率 ---")
for k, v in df["weekend_freq"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 8) 价格上涨10%反应 ---")
for k, v in df["price_reaction"].value_counts().items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 9) 每餐消费金额(数值)描述统计 ---")
desc = df["per_meal_cost_num"].describe()
w(f"  N={desc['count']:.0f}, Mean={desc['mean']:.2f}, Std={desc['std']:.2f}")
w(f"  Min={desc['min']:.2f}, Q1={desc['25%']:.2f}, Median={desc['50%']:.2f}, Q3={desc['75%']:.2f}, Max={desc['max']:.2f}")
w(f"  IQR={desc['75%']-desc['25%']:.2f}")

w("\n--- 10) 每月生活费(数值)描述统计 ---")
desc2 = df["living_expense_num"].describe()
w(f"  N={desc2['count']:.0f}, Mean={desc2['mean']:.2f}, Std={desc2['std']:.2f}")
w(f"  Min={desc2['min']:.2f}, Q1={desc2['25%']:.2f}, Median={desc2['50%']:.2f}, Q3={desc2['75%']:.2f}, Max={desc2['max']:.2f}")

w("\n--- 11) 李克特量表满意度描述统计 ---")
likert_cols = ["sat_taste", "sat_price", "sat_freshness", "sat_health",
               "sat_service", "sat_env", "sat_waiting", "sat_variety"]
likert_labels = ["菜品口味", "价格合理性", "新鲜度与卫生", "营养健康",
                 "服务态度", "就餐环境", "排队等待时间", "菜品种类丰富度"]
for col, label in zip(likert_cols, likert_labels):
    vals = df[col + "_num"].dropna()
    w(f"  {label}: mean={vals.mean():.3f}, std={vals.std():.3f}, "
      f"min={vals.min():.0f}, max={vals.max():.0f}")

w("\n--- 12) 就餐时段偏好(多选) ---")
from data_cleaner import get_multi_select_stats
stats = get_multi_select_stats(df, "meal_periods")
for k, v in stats.items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 13) 菜品类型偏好(多选) ---")
stats = get_multi_select_stats(df, "dish_types")
for k, v in stats.items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 14) 偏好价格区间(多选) ---")
stats = get_multi_select_stats(df, "pref_price_range")
for k, v in stats.items():
    w(f"  {k}: {v} ({pct(v)})")

w("\n--- 15) 生源地省份分布 ---")
prov = df["hometown_province"].value_counts()
for k, v in prov.items():
    w(f"  {k}: {v} ({pct(v)})")
w(f"  共 {len(prov)} 个省份/直辖市/自治区")

w("\n--- 16) 分性别每餐消费 ---")
for g in ["男", "女"]:
    vals = df[df["gender"] == g]["per_meal_cost_num"].dropna()
    w(f"  {g}: n={len(vals)}, mean={vals.mean():.2f}, std={vals.std():.2f}")

w("\n--- 17) 分年级每餐消费 ---")
for g in ["大一", "大二", "大三", "大四及以上"]:
    vals = df[df["grade"] == g]["per_meal_cost_num"].dropna()
    w(f"  {g}: n={len(vals)}, mean={vals.mean():.2f}, std={vals.std():.2f}")

w("\n--- 18) 分区域每餐消费 ---")
for r in ["上海本地", "东部地区", "中部地区", "西部地区"]:
    vals = df[df["hometown_region"] == r]["per_meal_cost_num"].dropna()
    w(f"  {r}: n={len(vals)}, mean={vals.mean():.2f}, std={vals.std():.2f}")

w("\n" + "=" * 60)
w("  统计提取完成")
w("=" * 60)

# 保存到文件
with open("_stats_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n[OK] 已保存至 _stats_output.txt")
