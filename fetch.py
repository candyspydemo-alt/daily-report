import requests
import json
from datetime import datetime

# 1. 設定 Header 模擬瀏覽器，防止被證交所阻擋
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 取得今日日期
today = datetime.now().strftime("%Y%m%d")
url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today}&selectType=ALL&response=json"

try:
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
except Exception as e:
    print(f"❌ 請求失敗: {e}")
    exit(0)

# 3. 檢查是否有資料（假日或尚未收盤會查無資料）
if data.get("stat") != "OK" or "data" not in data:
    print(f"⚠️ {today} 查無資料（可能尚未收盤、假日或 API 限制中）")
    exit(0)

foreign_total = 0
investment_total = 0
dealer_total = 0

# 4. 遍歷每檔股票，加總各法人的買賣超張數
for item in data["data"]:
    try:
        # T86 API 欄位索引: 
        # [2]: 外資, [10]: 投信, [11]: 自營商(合計)
        foreign_total += int(item[2].replace(",", ""))
        investment_total += int(item[10].replace(",", ""))
        dealer_total += int(item[11].replace(",", ""))
    except (ValueError, IndexError):
        continue

# 5. 計算總計
total_sum = foreign_total + investment_total + dealer_total

# 6. 整理結果 (將單位轉換為「億股」，四捨五入至小數點後兩位)
result = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "foreign": round(foreign_total / 100000000, 2),
    "investment": round(investment_total / 100000000, 2),
    "dealer": round(dealer_total / 100000000, 2),
    "total": round(total_sum / 100000000, 2)
}

# 7. 儲存為 JSON 檔案
try:
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 處理完成，已更新 data.json: {result}")
except Exception as e:
    print(f"❌ 檔案寫入失敗: {e}")

print("done")
