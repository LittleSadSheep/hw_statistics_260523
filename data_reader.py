"""
data_reader.py — 读取 Excel 问卷数据
"""

import pandas as pd


def read_survey_data(filepath: str) -> pd.DataFrame:
    """
    读取大学生食堂消费模式调查问卷 Excel 文件。

    Parameters
    ----------
    filepath : str
        Excel 文件路径。

    Returns
    -------
    pd.DataFrame
        原始问卷数据 DataFrame。
    """
    df = pd.read_excel(filepath, sheet_name="Sheet1")
    print(f"[data_reader] 读取完成: {df.shape[0]} 行 × {df.shape[1]} 列")
    return df
