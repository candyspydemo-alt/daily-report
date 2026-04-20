import requests
import json
from datetime import datetime

today = datetime.now().strftime("%Y%m%d")

url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today}&selectType=ALL&response=json"

res = requests.get(url)

try:
    data = res.json()
except:
    print("API 回傳不是 JSON")
    exit(0)

# 👉 如果沒資料就跳過（避免爆掉）
if "data" not in data or not data["data"]:
    print("今天還沒有資料")
    exit(0)

foreign = 0
investment = 0
dealer = 0

for item in data["data"]:
    try:
        name = item[0]
        value = float(item[-1].replace(",", ""))
    except:
        continue

    if "外資" in name:
        foreign += value
    elif "投信" in name:
        investment += value
    elif "自營商" in name:
        dealer += value

total = foreign + investment + dealer

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
