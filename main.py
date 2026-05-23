"""
main.py — 编排入口

调用 data_reader → data_cleaner → visualizer → statistics
输出：8张PNG图表 + 清洗后Excel + 统计结果txt
"""

import os

from config import INPUT_FILE, OUTPUT_DIR
from data_reader import read_survey_data
from data_cleaner import clean_survey_data
from visualizer import generate_all_plots
from statistics import run_all_statistics


def main():
    """主流程"""
    # 0. 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 70)
    print("  临港地区大学生食堂消费模式分析")
    print("  上海海洋大学（SHOU）| alpha = 0.05")
    print("=" * 70)

    # 1. 读取数据
    print("\n[1/5] 读取问卷数据...")
    df_raw = read_survey_data(INPUT_FILE)

    # 2. 数据清洗与转换
    print("\n[2/5] 数据清洗与转换...")
    df = clean_survey_data(df_raw)

    # 3. 数据可视化
    print("\n[3/5] 生成可视化图表...")
    generate_all_plots(df, OUTPUT_DIR)

    # 4. 统计检验
    print("\n[4/5] 运行统计检验...")
    run_all_statistics(df)

    # 5. 导出清洗后数据
    print("\n[5/5] 导出清洗后数据...")
    output_xlsx = os.path.join(OUTPUT_DIR, "cleaned_survey.xlsx")
    df.to_excel(output_xlsx, index=False, engine="openpyxl")
    print(f"  [OK] 清洗后数据已保存至: {output_xlsx}")
    print(f"  数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")

    print("\n" + "=" * 70)
    print("  分析完成！")
    print(f"  输出目录: {OUTPUT_DIR}")
    print(f"    - cleaned_survey.xlsx        (清洗后数据)")
    print(f"    - fig1_consumption_hist.png  (消费金额直方图+KDE)")
    print(f"    - fig2_boxplot_gender.png    (性别箱线图)")
    print(f"    - fig3_boxplot_grade.png     (年级箱线图)")
    print(f"    - fig4_boxplot_region.png    (区域箱线图)")
    print(f"    - fig5_meal_period_bar.png   (就餐时段柱状图)")
    print(f"    - fig6_dish_type_pie.png     (菜品类型饼图)")
    print(f"    - fig7_living_expense_bar.png(生活费区间柱状图)")
    print(f"    - fig8_likert_bar.png        (满意度均值SE柱状图)")
    print(f"    - statistics_results.txt     (统计检验结果)")
    print("=" * 70)


if __name__ == "__main__":
    main()
