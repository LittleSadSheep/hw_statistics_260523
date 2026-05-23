"""
statistics.py — 统计检验函数

包含：
  - 独立样本 t 检验（性别 vs 消费金额）
  - 单因素 方差分析（年级 vs 消费金额）
  - 单因素 方差分析（生源地区域 vs 消费金额）

所有检验使用 alpha = 0.05
"""

import os
import numpy as np
import pandas as pd
from scipy.stats import ttest_ind, f_oneway, levene
from itertools import combinations

from config import ALPHA, OUTPUT_DIR


def _print_section(title: str) -> None:
    """打印章节标题"""
    print(f"\n  {'=' * 60}")
    print(f"  {title}")
    print(f"  {'=' * 60}")


def ttest_gender_consumption(df: pd.DataFrame) -> dict:
    """
    独立样本 t 检验：男 vs 女 每餐消费金额差异。

    H0: mu_male = mu_female
    H1: mu_male != mu_female

    Returns
    -------
    dict
        检验结果字典。
    """
    _print_section("方法一：独立样本 t 检验 — 不同性别每餐消费金额差异")

    col = "per_meal_cost_num"
    male = df[df["gender"] == "男"][col].dropna()
    female = df[df["gender"] == "女"][col].dropna()

    if len(male) == 0 or len(female) == 0:
        print("  [跳过] 男女分组数据不足")
        return {}

    print(f"  男生 (n={len(male)}): 均值={male.mean():.2f}, 标准差={male.std():.2f}")
    print(f"  女生 (n={len(female)}): 均值={female.mean():.2f}, 标准差={female.std():.2f}")

    # Levene 方差齐性检验
    lev_stat, lev_p = levene(male, female)
    print(f"  Levene 方差齐性检验: 统计量={lev_stat:.4f}, p={lev_p:.4f}")
    equal_var = lev_p > ALPHA
    print(f"  方差齐性: {'是' if equal_var else '否'} (p={lev_p:.4f} {'>' if equal_var else '<='} {ALPHA})")

    # t 检验
    t_stat, t_p = ttest_ind(male, female, equal_var=equal_var)
    print(f"  t 检验: t={t_stat:.4f}, p={t_p:.4f}")
    if t_p < ALPHA:
        print(f"  结论: p={t_p:.4f} < {ALPHA}, 拒绝 H0，男女生每餐消费金额有显著差异。")
    else:
        print(f"  结论: p={t_p:.4f} >= {ALPHA}, 不拒绝 H0，男女生每餐消费金额无显著差异。")

    return {
        "method": "独立样本 t 检验（性别）",
        "male_n": len(male), "male_mean": male.mean(), "male_std": male.std(),
        "female_n": len(female), "female_mean": female.mean(), "female_std": female.std(),
        "levene_stat": lev_stat, "levene_p": lev_p, "equal_var": equal_var,
        "t_stat": t_stat, "t_p": t_p,
        "significant": t_p < ALPHA,
    }


def 方差分析_grade_consumption(df: pd.DataFrame) -> dict:
    """
    单因素 方差分析：不同年级每餐消费金额差异。

    H0: 各年级均值相等
    H1: 至少有一组均值不等

    Returns
    -------
    dict
        检验结果字典。
    """
    _print_section("方法二：单因素 方差分析 — 不同年级每餐消费金额差异")

    col = "per_meal_cost_num"
    grade_order = ["大一", "大二", "大三", "大四及以上"]
    groups = []
    group_names = []
    for g in grade_order:
        vals = df[df["grade"] == g][col].dropna()
        if len(vals) > 0:
            groups.append(vals)
            group_names.append(g)
            print(f"  {g}: n={len(vals)}, 均值={vals.mean():.2f}, 标准差={vals.std():.2f}")

    if len(groups) < 2:
        print("  [跳过] 年级分组不足")
        return {}

    # 方差分析
    f_stat, 方差分析_p = f_oneway(*groups)
    print(f"  方差分析: F={f_stat:.4f}, p={方差分析_p:.4f}")

    result = {
        "method": "单因素 方差分析（年级）",
        "groups": group_names,
        "ns": [len(g) for g in groups],
        "means": [g.mean() for g in groups],
        "stds": [g.std() for g in groups],
        "f_stat": f_stat, "方差分析_p": 方差分析_p,
        "significant": 方差分析_p < ALPHA,
    }

    if 方差分析_p < ALPHA:
        print(f"  结论: p={方差分析_p:.4f} < {ALPHA}, 拒绝 H0，不同年级每餐消费金额有显著差异。")
        # Tukey HSD 事后检验
        result.update(_tukey_hsd(groups, group_names))
    else:
        print(f"  结论: p={方差分析_p:.4f} >= {ALPHA}, 不拒绝 H0，不同年级每餐消费金额无显著差异。")

    return result


def 方差分析_region_consumption(df: pd.DataFrame) -> dict:
    """
    单因素 方差分析：不同生源地区域每餐消费金额差异。

    H0: 各区域均值相等
    H1: 至少有一组均值不等

    Returns
    -------
    dict
        检验结果字典。
    """
    _print_section("方法三：单因素 方差分析 — 不同生源地区域每餐消费金额差异")

    col = "per_meal_cost_num"
    region_order = ["上海本地", "东部地区", "中部地区", "西部地区"]
    groups = []
    group_names = []
    for r in region_order:
        vals = df[df["hometown_region"] == r][col].dropna()
        if len(vals) > 0:
            groups.append(vals)
            group_names.append(r)
            print(f"  {r}: n={len(vals)}, 均值={vals.mean():.2f}, 标准差={vals.std():.2f}")

    if len(groups) < 2:
        print("  [跳过] 区域分组不足")
        return {}

    # 方差分析
    f_stat, 方差分析_p = f_oneway(*groups)
    print(f"  方差分析: F={f_stat:.4f}, p={方差分析_p:.4f}")

    result = {
        "method": "单因素 方差分析（生源地区域）",
        "groups": group_names,
        "ns": [len(g) for g in groups],
        "means": [g.mean() for g in groups],
        "stds": [g.std() for g in groups],
        "f_stat": f_stat, "方差分析_p": 方差分析_p,
        "significant": 方差分析_p < ALPHA,
    }

    if 方差分析_p < ALPHA:
        print(f"  结论: p={方差分析_p:.4f} < {ALPHA}, 拒绝 H0，不同生源地区域每餐消费金额有显著差异。")
        result.update(_tukey_hsd(groups, group_names))
    else:
        print(f"  结论: p={方差分析_p:.4f} >= {ALPHA}, 不拒绝 H0，不同生源地区域每餐消费金额无显著差异。")

    return result


def _tukey_hsd(groups: list, group_names: list) -> dict:
    """
    Tukey HSD 事后多重比较。

    Parameters
    ----------
    groups : list of np.array
        各组数据。
    group_names : list of str
        各组名称。

    Returns
    -------
    dict
        包含 tukey_results 列表。
    """
    n_groups = len(groups)
    N_total = sum(len(g) for g in groups)
    df_error = N_total - n_groups

    # MSE（组内均方）
    mse = sum((len(g) - 1) * g.var(ddof=1) for g in groups) / df_error if df_error > 0 else 0

    # 近似 q 临界值（alpha=0.05, k=组数, df=误差自由度）
    # 这里使用一个简化的查表值。对于 df > 120 且 k=3~4, q ≈ 3.31~3.63
    q_critical_map = {2: 2.77, 3: 3.31, 4: 3.63, 5: 3.86, 6: 4.03}
    q_critical = q_critical_map.get(n_groups, 3.63)

    print(f"  Tukey HSD 事后多重比较 (MSE={mse:.4f}, df_e={df_error}, q_crit≈{q_critical}):")

    tukey_results = []
    for (i, g1), (j, g2) in combinations(enumerate(groups), 2):
        diff = abs(g1.mean() - g2.mean())
        if mse > 0:
            se = np.sqrt(mse * (1 / len(g1) + 1 / len(g2)))
            q_obs = diff / se if se > 0 else 0
        else:
            q_obs = 0
            se = 0
        sig = "显著" if q_obs > q_critical else "不显著"
        print(f"    {group_names[i]} vs {group_names[j]}: diff={diff:.2f}, q={q_obs:.2f} ({sig})")
        tukey_results.append({
            "pair": f"{group_names[i]} vs {group_names[j]}",
            "diff": diff, "q_obs": q_obs, "q_crit": q_critical, "significant_sig": sig,
        })

    return {"mse": mse, "df_error": df_error, "q_critical": q_critical, "tukey_results": tukey_results}


def run_all_statistics(df: pd.DataFrame) -> None:
    """运行全部统计检验并输出汇总"""
    print("\n" + "=" * 70)
    print("  统计模型分析 (alpha = 0.05)")
    print("=" * 70)

    results = {}
    results["ttest_gender"] = ttest_gender_consumption(df)
    results["方差分析_grade"] = 方差分析_grade_consumption(df)
    results["方差分析_region"] = 方差分析_region_consumption(df)

    # 打印汇总
    _print_section("统计检验结果汇总")
    for key, res in results.items():
        if not res:
            continue
        method = res.get("method", key)
        if "t_stat" in res:
            print(f"  {method}: t={res['t_stat']:.4f}, p={res['t_p']:.4f} "
                  f"({'显著' if res['significant'] else '不显著'})")
        elif "f_stat" in res:
            print(f"  {method}: F={res['f_stat']:.4f}, p={res['方差分析_p']:.4f} "
                  f"({'显著' if res['significant'] else '不显著'})")

    # 保存结果到文本文件
    _save_results_txt(results)

    print("\n" + "=" * 70)
    print("  统计检验完成。")
    print("=" * 70)

    return results


def _save_results_txt(results: dict) -> None:
    """保存统计结果到 output/statistics_results.txt"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, "statistics_results.txt")

    lines = [
        "=" * 70,
        "  临港地区大学生食堂消费模式分析 — 统计检验结果",
        "  上海海洋大学（SHOU）| alpha = 0.05",
        "=" * 70,
        "",
    ]

    for key, res in results.items():
        if not res:
            continue
        method = res.get("method", key)
        lines.append(f"--- {method} ---")
        for k, v in res.items():
            if k == "tukey_results":
                lines.append("  Tukey HSD 事后比较:")
                for tr in v:
                    lines.append(f"    {tr['pair']}: diff={tr['diff']:.2f}, q={tr['q_obs']:.2f} ({tr['significant_sig']})")
            elif isinstance(v, float):
                lines.append(f"  {k}: {v:.4f}")
            elif not isinstance(v, (list, dict)):
                lines.append(f"  {k}: {v}")
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [OK] 统计结果已保存至: {path}")
