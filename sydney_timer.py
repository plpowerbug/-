from datetime import datetime
import pytz

def convert_time(pacific_time_str):
    # 定义时区
    pacific_tz = pytz.timezone('America/Los_Angeles')  # 美西时间（PDT）
    sydney_tz = pytz.timezone('Australia/Sydney')      # 澳洲悉尼时间（AEDT）

    # 将字符串时间转换为 datetime 对象
    pacific_time = datetime.strptime(pacific_time_str, '%Y-%m-%d %H:%M')

    # 设置美西时区
    pacific_time = pacific_tz.localize(pacific_time)

    # 转换为澳大利亚悉尼时间
    sydney_time = pacific_time.astimezone(sydney_tz)

    # 返回转换后的时间
    return sydney_time.strftime('%Y-%m-%d %H:%M')

# 示例使用：转换美西时间2024年9月27日上午9:00
pacific_time_input = '2024-09-27 09:00'  # 输入美西时间
converted_time = convert_time(pacific_time_input)
print(f"悉尼时间为: {converted_time}")