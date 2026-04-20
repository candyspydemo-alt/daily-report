import requests
import json
from datetime import datetime

# 建議 User-Agent 模擬瀏覽器，避免被封鎖
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

today = datetime.now().strftime("%Y%m%d")
url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today}&selectType=ALL&response=json"

try:
    res = requests.get(url, headers=headers)
    data = res.json()
except Exception as e:
    print(f"請求失敗: {e}")
    exit(0)

if data.get("stat") != "OK" or "data" not in data:
    print(f"{today} 查無資料（可能尚未收盤或假日）")
    exit(0)

foreign_total = 0
investment_total = 0
dealer_total = 0

for item in data["data"]:
    try:
        # 索引說明 (以證交所 T86 格式為準):
        # item[2] 外資買賣超, item[10] 投信買賣超, item[11] 自營商買賣超
        foreign_total += int(item[2].replace(",", ""))
        investment_total += int(item[10].replace(",", ""))
        dealer_total += int(item[11].replace(",", ""))
    except (ValueError, IndexError):
        continue

total = foreign_total + investment_total + dealer_total

result = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "foreign": round(foreign_total / 100000000, 2),    # 單位：億
    "investment": round(investment_total / 100000000, 2),
    "dealer": round(dealer_total / 100000000, 2),
    "total": round(total / 100000000, 2)
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"處理完成: {result}")
