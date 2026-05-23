"""
data_cleaner.py — 数据清洗与转换

清洗流水线：
  1. 删除元数据列
  2. 重命名列
  3. 去除选项前缀（"A. 男" → "男"）
  4. 映射生源地代码 → 区域分类
  5. 消费金额区间 → 数值中点
  6. 生活费区间 → 数值中点
  7. 量表 → 1-5 数值
  8. 多选题展开统计（meal_periods, dish_types, pref_price_range）
  9. IQR 异常值检测
"""

import numpy as np
import pandas as pd
from config import (
    COLUMN_RENAME,
    META_COLS,
    LIKERT_COLS,
    LIKERT_MAP,
    MULTI_SELECT_COLS,
    CONSUMPTION_RANGE_MAP,
    LIVING_EXPENSE_MAP,
    PROVINCE_MAP,
    strip_option_prefix,
)

# 模块级缓存，用于存储多选题统计结果（避免在 DataFrame 上设置自定义属性）
_multi_select_cache: dict = {}


def clean_survey_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    执行完整的数据清洗流水线。

    Parameters
    ----------
    df_raw : pd.DataFrame
        原始问卷数据。

    Returns
    -------
    pd.DataFrame
        清洗后的 DataFrame。
    """
    df = df_raw.copy()

    # ---- 步骤1: 删除元数据列 ----
    cols_to_drop = [c for c in META_COLS if c in df.columns]
    df.drop(columns=cols_to_drop, inplace=True, errors="ignore")
    print(f"1: 删除了 {len(cols_to_drop)} 个元数据列")

    # ---- 步骤2: 重命名列 ----
    df.rename(columns=COLUMN_RENAME, inplace=True)
    print(f"2: 列重命名完成 ({len(COLUMN_RENAME)} 列)")

    # ---- 步骤3: 去除单选题/量表题文本的前缀 ----
    prefix_strip_cols = [
        "gender", "grade", "living_expense", "daily_visits",
        "weekday_freq", "weekend_freq", "per_meal_cost",
        "price_reaction",
    ] + LIKERT_COLS
    for col in prefix_strip_cols:
        if col in df.columns:
            df[col] = df[col].apply(strip_option_prefix)
    print(f"3: 去除了 {len(prefix_strip_cols)} 列的前缀")

    # ---- 步骤3b: 文本标准化（统一 en-dash 和 空格） ----
    range_cols = ["per_meal_cost", "living_expense"]
    for col in range_cols:
        if col in df.columns:
            df[col] = df[col].apply(_normalize_range_text)
    print(f"3b: 文本标准化完成")

    # ---- 步骤4: 映射生源地代码 → 省份名 + 区域 ----
    if "hometown_code" in df.columns:
        # 先提取纯代码（如 "AD. 黑龙江省" → "AD"）
        df["hometown_code_clean"] = df["hometown_code"].apply(_extract_code)
        df["hometown_province"] = df["hometown_code_clean"].map(
            lambda c: PROVINCE_MAP.get(c, ("未知", "未知"))[0]
        )
        df["hometown_region"] = df["hometown_code_clean"].map(
            lambda c: PROVINCE_MAP.get(c, ("未知", "未知"))[1]
        )
        unmapped = df["hometown_code_clean"][
            ~df["hometown_code_clean"].isin(PROVINCE_MAP.keys())
        ].unique()
        if len(unmapped) > 0:
            print(f"  [警告] 未映射的生源地代码: {list(unmapped)}")
        print(f"4: 生源地代码 → 省份 + 区域映射完成")

    # ---- 步骤5: 消费金额区间 → 数值中点 ----
    if "per_meal_cost" in df.columns:
        df["per_meal_cost_num"] = df["per_meal_cost"].map(CONSUMPTION_RANGE_MAP)
        unmapped_cost = df[df["per_meal_cost_num"].isna()]["per_meal_cost"].unique()
        if len(unmapped_cost) > 0:
            print(f"  [警告] 未映射的消费区间: {list(unmapped_cost)}")
        print(f"5: 消费金额区间 → 数值中点 (有效值: {df['per_meal_cost_num'].notna().sum()})")

    # ---- 步骤6: 生活费区间 → 数值中点 ----
    if "living_expense" in df.columns:
        df["living_expense_num"] = df["living_expense"].map(LIVING_EXPENSE_MAP)
        unmapped_le = df[df["living_expense_num"].isna()]["living_expense"].unique()
        if len(unmapped_le) > 0:
            print(f"  [警告] 未映射的生活费区间: {list(unmapped_le)}")
        print(f"6: 生活费区间 → 数值中点 (有效值: {df['living_expense_num'].notna().sum()})")

    # ---- 步骤7: 量表 → 1-5 数值 ----
    for col in LIKERT_COLS:
        if col in df.columns:
            df[col + "_num"] = df[col].map(LIKERT_MAP)
    print(f"7: 量表 {len(LIKERT_COLS)} 列 → 数值完成")

    # ---- 步骤8: 多选题展开统计 ----
    for col in MULTI_SELECT_COLS:
        if col in df.columns:
            df = _expand_multi_select(df, col)
    print(f"8: 多选题展开统计完成 ({len(MULTI_SELECT_COLS)} 列)")

    # ---- 步骤9: IQR 异常值检测 ----
    if "per_meal_cost_num" in df.columns:
        Q1 = df["per_meal_cost_num"].quantile(0.25)
        Q3 = df["per_meal_cost_num"].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df["is_outlier"] = (df["per_meal_cost_num"] < lower) | (df["per_meal_cost_num"] > upper)
        n_outliers = df["is_outlier"].sum()
        print(f"9: IQR异常值检测 Q1={Q1:.2f}, Q3={Q3:.2f}, IQR={IQR:.2f}")
        print(f"  异常范围: <{lower:.2f} 或 >{upper:.2f}, 异常样本: {n_outliers} ({100*n_outliers/len(df):.1f}%)")

    # ---- 步骤10: 检查缺失值 ----
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if len(missing) > 0:
        print(f"\n[cleaner] 缺失值统计:")
        for col, cnt in missing.items():
            print(f"  {col}: {cnt}")
    else:
        print(f"\n[cleaner] 无缺失值")

    print(f"\n[cleaner] 清洗完成: {df.shape[0]} 行 × {df.shape[1]} 列")
    return df


def _extract_code(raw: str) -> str:
    """从 'AD. 黑龙江省' 中提取代码 'AD'"""
    if pd.isna(raw):
        return ""
    s = str(raw).strip()
    parts = s.split(".")
    return parts[0].strip() if parts else ""


def _expand_multi_select(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    将多选题列按 '┋' 拆分展开：
    1. 统计每种选项的总选择次数
    2. 为每个选项创建 0/1 哑变量列
    3. 添加 '{col}_count' 列（受访者选择了几个选项）
    """
    # 解析每个单元格为选项列表（去除前缀）
    parsed = df[col].apply(
        lambda x: [strip_option_prefix(item) for item in str(x).split("┋")]
        if pd.notna(x) and str(x).strip() != ""
        else []
    )

    # 添加选择数量列
    df[col + "_count"] = parsed.apply(len)

    # 统计每种选项的总选择次数
    all_items = []
    for items in parsed:
        all_items.extend(items)
    item_counts = pd.Series(all_items).value_counts()

    # 为 Top-N 选项创建 0/1 哑变量
    top_items = item_counts.head(10).index.tolist()
    for item in top_items:
        safe_name = _make_safe_colname(col, item)
        df[safe_name] = parsed.apply(lambda x: 1 if item in x else 0)

    # 存储选项统计到模块级缓存供后续可视化使用
    _multi_select_cache[id(df)] = _multi_select_cache.get(id(df), {})
    _multi_select_cache[id(df)][col] = item_counts

    return df


def _make_safe_colname(col: str, item: str) -> str:
    """生成安全的哑变量列名，如 'meal_periods_早餐'"""
    # 提取时段名等简短标识
    short = item.split("（")[0].split("(")[0].strip()
    return f"{col}_{short}"


def _normalize_range_text(text: str) -> str:
    """
    标准化区间文本：统一 en-dash/em-dash → 普通连字符，去除多余空格。

    Example:
        "9–12 元" → "9-12元"
        "17–20 元" → "17-20元"
    """
    if pd.isna(text):
        return text
    s = str(text).strip()
    # 统一各种 dash → 普通连字符
    import re
    s = re.sub(r'[\u2013\u2014\u2015]', '-', s)  # en-dash, em-dash, horizontal bar
    s = s.replace(' ', '')  # 去空格
    return s


def get_multi_select_stats(df: pd.DataFrame, col: str) -> pd.Series:
    """
    获取多选题统计结果（各选项被选次数）。
    从模块级缓存中读取，避免在 DataFrame 上设置自定义属性。
    """
    cache = _multi_select_cache.get(id(df), {})
    return cache.get(col, pd.Series(dtype=int))
