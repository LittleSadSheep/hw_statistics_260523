"""
generate_data.py — 模拟数据集生成脚本
用途：为"临港地区大学生食堂消费模式分析"生成模拟的一卡通消费数据
目标高校：上海海洋大学（SHOU）
输出：GROUP-XXX_data.xlsx（含 4 个 Sheet）

此脚本是项目的第一步，先运行它生成数据，再运行 main.py 进行分析。
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ============================================================
# 0. 随机种子设定（确保可复现）
# ============================================================
np.random.seed(42)

# ============================================================
# 1. 生成学生基本信息表 (students) — 500 人
# ============================================================
N_STUDENTS = 500

student_ids = [f"M2206{i:05d}" for i in range(1, N_STUDENTS + 1)]

# 性别：0=女, 1=男（约 48:52）
genders = np.random.choice([0, 1], size=N_STUDENTS, p=[0.48, 0.52])

# 生源地：0=上海本地, 1=东部地区, 2=中部地区, 3=西部地区
hometown_labels = ["上海本地", "东部地区", "中部地区", "西部地区"]
hometown_region = np.random.choice([0, 1, 2, 3], size=N_STUDENTS, p=[0.35, 0.25, 0.22, 0.18])

# 学院：6 个学院
college_labels = [
    "水产与生命学院", "食品学院", "海洋科学学院",
    "工程学院", "信息学院", "经济管理学院"
]
colleges = np.random.choice(range(6), size=N_STUDENTS, p=[0.18, 0.17, 0.15, 0.18, 0.16, 0.16])

# 年级：1=大一, 2=大二, 3=大三, 4=大四
grades = np.random.choice([1, 2, 3, 4], size=N_STUDENTS, p=[0.28, 0.27, 0.25, 0.20])

students_df = pd.DataFrame({
    "student_id": student_ids,
    "gender": genders,
    "hometown_region": hometown_region,
    "college": colleges,
    "grade": grades,
    "gender_label": ["女" if g == 0 else "男" for g in genders],
    "hometown_label": [hometown_labels[r] for r in hometown_region],
    "college_label": [college_labels[c] for c in colleges],
})

print(f"[1/4] 学生基本信息表: {len(students_df)} 条记录")

# ============================================================
# 2. 生成菜品/窗口信息表 (dishes) — ~80 道
# ============================================================
N_DISHES = 80

dish_names = [
    # 主食类 (0)
    "白米饭", "蛋炒饭", "扬州炒饭", "馒头", "花卷", "包子", "煎饼",
    "面条", "炸酱面", "兰州拉面", "馄饨", "水饺", "锅贴", "春卷",
    # 荤菜类 (1)
    "红烧肉", "糖醋排骨", "宫保鸡丁", "鱼香肉丝", "回锅肉", "红烧鸡块",
    "清蒸鱼", "红烧鱼块", "辣子鸡", "孜然牛肉", "爆炒腰花", "糖醋里脊",
    "红烧狮子头", "咖喱鸡", "可乐鸡翅", "椒盐大虾", "干锅花菜炒肉",
    "鱼香茄子煲", "土豆烧牛肉", "洋葱炒肉片", "木耳炒肉", "酱爆肉丁",
    # 素菜类 (2)
    "蒜蓉西兰花", "清炒小白菜", "凉拌黄瓜", "番茄炒蛋", "麻婆豆腐",
    "干煸四季豆", "醋溜土豆丝", "蒜蓉生菜", "香菇青菜", "地三鲜",
    "红烧茄子", "清炒豆芽", "凉拌木耳", "虎皮青椒", "糖醋藕片",
    "素炒西葫芦", "蒜苗炒香干", "菠菜拌粉丝",
    # 汤粥类 (3)
    "紫菜蛋花汤", "番茄蛋汤", "酸辣汤", "排骨汤", "玉米排骨汤",
    "小米粥", "皮蛋瘦肉粥", "绿豆粥", "银耳羹", "红豆粥",
    # 小吃/饮料类 (4)
    "炸鸡排", "煎饼果子", "烤肠", "手抓饼", "奶茶", "豆浆",
    "牛奶", "咖啡", "面包", "蛋糕", "水果拼盘", "酸奶",
]

# 确保正好 80 道
dish_names = dish_names[:N_DISHES]

# 类别分配
categories = ([0] * 14 + [1] * 22 + [2] * 18 + [3] * 10 + [4] * 12 + [0] * 4)[:N_DISHES]
np.random.shuffle(categories)  # 打乱顺序
# 重新按菜品名称逻辑分配类别以保证合理性
category_list = []
for name in dish_names:
    if name in ["白米饭", "蛋炒饭", "扬州炒饭", "馒头", "花卷", "包子", "煎饼",
                 "面条", "炸酱面", "兰州拉面", "馄饨", "水饺", "锅贴", "春卷"]:
        category_list.append(0)
    elif name in ["红烧肉", "糖醋排骨", "宫保鸡丁", "鱼香肉丝", "回锅肉", "红烧鸡块",
                   "清蒸鱼", "红烧鱼块", "辣子鸡", "孜然牛肉", "爆炒腰花", "糖醋里脊",
                   "红烧狮子头", "咖喱鸡", "可乐鸡翅", "椒盐大虾", "干锅花菜炒肉",
                   "鱼香茄子煲", "土豆烧牛肉", "洋葱炒肉片", "木耳炒肉", "酱爆肉丁"]:
        category_list.append(1)
    elif name in ["蒜蓉西兰花", "清炒小白菜", "凉拌黄瓜", "番茄炒蛋", "麻婆豆腐",
                   "干煸四季豆", "醋溜土豆丝", "蒜蓉生菜", "香菇青菜", "地三鲜",
                   "红烧茄子", "清炒豆芽", "凉拌木耳", "虎皮青椒", "糖醋藕片",
                   "素炒西葫芦", "蒜苗炒香干", "菠菜拌粉丝"]:
        category_list.append(2)
    elif name in ["紫菜蛋花汤", "番茄蛋汤", "酸辣汤", "排骨汤", "玉米排骨汤",
                   "小米粥", "皮蛋瘦肉粥", "绿豆粥", "银耳羹", "红豆粥"]:
        category_list.append(3)
    else:
        category_list.append(4)

category_labels = ["主食", "荤菜", "素菜", "汤粥", "小吃/饮料"]

# 价格生成（基于类别分布）
prices = []
for cat in category_list:
    if cat == 0:  # 主食
        p = np.random.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0])
    elif cat == 1:  # 荤菜
        p = np.random.choice([6, 7, 8, 9, 10, 12, 14, 15, 16, 18, 20, 22])
    elif cat == 2:  # 素菜
        p = np.random.choice([2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8])
    elif cat == 3:  # 汤粥
        p = np.random.choice([1, 1.5, 2, 3, 4, 5, 6, 8])
    else:  # 小吃/饮料
        p = np.random.choice([3, 4, 5, 6, 7, 8, 9, 10, 12, 15])
    prices.append(float(p))

# 价格档位：0=低价(≤5), 1=中价(5~10), 2=高价(>10)
def classify_tier(p):
    if p <= 5:
        return 0
    elif p <= 10:
        return 1
    else:
        return 2

price_tiers = [classify_tier(p) for p in prices]
tier_labels = ["低价(≤5元)", "中价(5~10元)", "高价(>10元)"]

# 以实际菜品数量为准
actual_n_dishes = len(dish_names)

# 食堂分布：0=第一食堂, 1=第二食堂, 2=清真食堂, 3=风味餐厅
canteen_labels = ["第一食堂", "第二食堂", "清真食堂", "风味餐厅"]
canteens = np.random.choice([0, 1, 2, 3], size=actual_n_dishes, p=[0.35, 0.30, 0.15, 0.20])

dishes_df = pd.DataFrame({
    "dish_id": range(1, actual_n_dishes + 1),
    "dish_name": dish_names,
    "category": category_list,
    "category_label": [category_labels[c] for c in category_list],
    "price": prices,
    "price_tier": price_tiers,
    "price_tier_label": [tier_labels[t] for t in price_tiers],
    "canteen": canteens,
    "canteen_label": [canteen_labels[c] for c in canteens],
})

print(f"[2/4] 菜品信息表: {len(dishes_df)} 条记录")

# ============================================================
# 3. 生成一卡通消费流水表 (transactions) — 30 天
# ============================================================
# 设定参数
N_DAYS = 30
START_DATE = datetime(2026, 3, 1)

# 每个学生每天的消费概率由多个因素决定
# 基础：每个人每天大致吃 2-3 餐（早餐有些人不吃）
# 每餐可能点 1-3 道菜

transactions = []

for day in range(N_DAYS):
    current_date = START_DATE + timedelta(days=day)
    # 周末消费略有不同（外出就餐增多，食堂消费略降）
    is_weekend = current_date.weekday() >= 5

    for _, student in students_df.iterrows():
        sid = student["student_id"]
        # 每天消费餐数
        if is_weekend:
            n_meals = np.random.choice([0, 0, 1, 1, 2, 2, 3], p=[0.15, 0.10, 0.20, 0.15, 0.20, 0.10, 0.10])
        else:
            n_meals = np.random.choice([0, 1, 2, 2, 3, 3], p=[0.05, 0.10, 0.20, 0.25, 0.20, 0.20])

        for _ in range(n_meals):
            # 选择餐段（基于时段概率）
            meal_period = np.random.choice([0, 1, 2, 3], p=[0.18, 0.42, 0.35, 0.05])

            # 根据餐段生成时间
            if meal_period == 0:  # 早餐 6:00-9:00
                hour = np.random.choice([6, 7, 7, 7, 8, 8, 8, 9])
                minute = np.random.randint(0, 60)
            elif meal_period == 1:  # 午餐 11:00-13:30
                hour = np.random.choice([11, 11, 11, 12, 12, 12, 12, 12, 13])
                minute = np.random.randint(0, 60)
            elif meal_period == 2:  # 晚餐 16:30-19:30
                hour = np.random.choice([16, 17, 17, 17, 18, 18, 18, 18, 19])
                minute = np.random.randint(0, 60)
            else:  # 夜宵 20:00-22:30
                hour = np.random.choice([20, 20, 21, 21, 21, 22])
                minute = np.random.randint(0, 60)

            ts = current_date.replace(hour=hour, minute=minute,
                                       second=np.random.randint(0, 60))

            # 每餐道数（早餐通常少一些）
            if meal_period == 0:
                n_dishes = np.random.choice([1, 1, 1, 2, 2], p=[0.35, 0.25, 0.15, 0.15, 0.10])
            elif meal_period == 3:
                n_dishes = np.random.choice([1, 1, 2], p=[0.6, 0.25, 0.15])
            else:
                n_dishes = np.random.choice([1, 2, 2, 3, 3], p=[0.15, 0.30, 0.25, 0.15, 0.15])

            # 选择本次就餐的食堂
            canteen_choice = np.random.choice([0, 1, 2, 3], p=[0.35, 0.30, 0.15, 0.20])

            # 从该食堂筛选菜品
            canteen_dishes = dishes_df[dishes_df["canteen"] == canteen_choice]
            if len(canteen_dishes) == 0:
                canteen_dishes = dishes_df  # fallback

            chosen_dishes = canteen_dishes.sample(n=min(n_dishes, len(canteen_dishes)), replace=True)

            total_amount = chosen_dishes["price"].sum()

            # 添加抖动：消费金额 ± 随机小波动（米饭免费/加量等）
            total_amount = round(total_amount + np.random.normal(0, 0.5), 2)
            total_amount = max(total_amount, 1.0)  # 最低 1 元

            for _, dish in chosen_dishes.iterrows():
                transactions.append({
                    "student_id": sid,
                    "timestamp": ts,
                    "meal_period": meal_period,
                    "dish_id": dish["dish_id"],
                    "amount": dish["price"],
                    "canteen": canteen_choice,
                    "is_weekend": 1 if is_weekend else 0,
                })

trans_df = pd.DataFrame(transactions)
# 添加餐段标签
meal_labels = ["早餐", "午餐", "晚餐", "夜宵"]
trans_df["meal_period_label"] = [meal_labels[p] for p in trans_df["meal_period"]]
trans_df["canteen_label"] = [canteen_labels[c] for c in trans_df["canteen"]]

# 添加交易 ID
trans_df.insert(0, "trans_id", range(1, len(trans_df) + 1))

print(f"[3/4] 消费流水表: {len(trans_df)} 条记录")
print(f"    日期范围: {trans_df['timestamp'].min()} ~ {trans_df['timestamp'].max()}")
print(f"    日均交易: {len(trans_df) / N_DAYS:.0f} 条")

# ============================================================
# 4. 生成问卷数据表 (survey) — 从 students 中抽取 n≥200
# ============================================================
N_SURVEY = 220
survey_students = np.random.choice(student_ids, size=N_SURVEY, replace=False)

# 问卷数据与学生属性关联以增加合理性
survey_data = []
for sid in survey_students:
    stu = students_df[students_df["student_id"] == sid].iloc[0]
    gender = stu["gender"]      # 0=女, 1=男
    grade = stu["grade"]
    college = stu["college"]

    # 月均消费（基于性别和年级模拟）
    base = 450 if gender == 0 else 550  # 男生略高
    grade_adj = {1: 1.0, 2: 1.05, 3: 1.08, 4: 1.12}
    monthly = base * grade_adj.get(grade, 1.0) + np.random.normal(0, 80)

    # 各维度评分（1-5 Likert，基于真实水平模拟）
    # 引入一些系统性差异以支持后续回归分析
    taste = np.clip(round(np.random.normal(3.5, 0.8)), 1, 5)
    price = np.clip(round(np.random.normal(3.2, 0.9)), 1, 5)
    service = np.clip(round(np.random.normal(3.3, 0.85)), 1, 5)
    health = np.clip(round(np.random.normal(3.6, 0.75)), 1, 5)
    env = np.clip(round(np.random.normal(3.4, 0.8)), 1, 5)
    variety = np.clip(round(np.random.normal(3.5, 0.85)), 1, 5)
    overall = np.clip(round(np.random.normal(3.4, 0.7)), 1, 5)

    survey_data.append({
        "student_id": sid,
        "monthly_consumption": round(monthly, 2),
        "taste_score": int(taste),
        "price_score": int(price),
        "service_score": int(service),
        "health_score": int(health),
        "env_score": int(env),
        "variety_score": int(variety),
        "overall_satisfaction": int(overall),
    })

survey_df = pd.DataFrame(survey_data)

print(f"[4/4] 问卷数据表: {len(survey_df)} 条记录")
print(f"    月均消费均值: {survey_df['monthly_consumption'].mean():.2f} 元")
print(f"    总体满意度均值: {survey_df['overall_satisfaction'].mean():.2f}")

# ============================================================
# 5. 输出到 Excel（多个 Sheet）
# ============================================================
OUTPUT_PATH = r"c:\stat\GROUP-XXX_data.xlsx"

with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
    students_df.to_excel(writer, sheet_name="students", index=False)
    dishes_df.to_excel(writer, sheet_name="dishes", index=False)
    trans_df.to_excel(writer, sheet_name="transactions", index=False)
    survey_df.to_excel(writer, sheet_name="survey", index=False)

print(f"\n✅ 数据已成功输出至: {OUTPUT_PATH}")
print(f"   Sheet 'students':     {len(students_df)} 行 × {len(students_df.columns)} 列")
print(f"   Sheet 'dishes':       {len(dishes_df)} 行 × {len(dishes_df.columns)} 列")
print(f"   Sheet 'transactions': {len(trans_df)} 行 × {len(trans_df.columns)} 列")
print(f"   Sheet 'survey':       {len(survey_df)} 行 × {len(survey_df.columns)} 列")
print("\n📊 数据概览:")
print(f"   学生总数: {N_STUDENTS}")
print(f"   菜品总数: {N_DISHES}")
print(f"   消费记录: {len(trans_df)}")
print(f"   问卷回收: {N_SURVEY}")
print(f"   时间跨度: {N_DAYS} 天")
