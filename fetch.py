import requests
import json
from datetime import datetime

# 取得今天日期
today = datetime.now().strftime("%Y%m%d")

url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today}&selectType=ALL&response=json"

res = requests.get(url)
data = res.json()

# 預設值
foreign = 0
investment = 0
dealer = 0

# 抓三大法人
for item in data.get("data", []):
    name = item[0]
    value = float(item[-1].replace(",", ""))

    if "外資" in name:
        foreign += value
    elif "投信" in name:
        investment += value
    elif "自營商" in name:
        dealer += value

total = foreign + investment + dealer

# 輸出成 JSON
result = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "foreign": round(foreign / 100000000, 2),
    "investment": round(investment / 100000000, 2),
    "dealer": round(dealer / 100000000, 2),
    "total": round(total / 100000000, 2)
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("done")
