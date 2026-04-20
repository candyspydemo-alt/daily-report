import requests
import json
from datetime import datetime
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 1. 取得日期
today = datetime.now().strftime("%Y%m%d")
url = f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?date={today}&response=json"

try:
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
except Exception as e:
    print(f"❌ 請求失敗: {e}")
    exit(0)

# 2. 💡 嚴格檢查：如果 stat 不是 OK，或是沒資料，立刻停止，不准往下跑！
if data.get("stat") != "OK" or "data" not in data or len(data["data"]) == 0:
    print(f"⚠️ 證交所尚未更新 {today} 的金額資料，程式終止，不更新檔案。")
    exit(0) 

# 3. 解析金額
try:
    # 確保抓到的是今天的數據
    dealer_hedge = float(data["data"][0][3].replace(",", ""))
    dealer_self = float(data["data"][1][3].replace(",", ""))
    investment = float(data["data"][2][3].replace(",", ""))
    foreign = float(data["data"][3][3].replace(",", ""))

    dealer_total = dealer_self + dealer_hedge
    total_sum = dealer_total + investment + foreign

    # 4. ✅ 只有確認抓到資料後，才建立 result 物件
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "foreign": round(foreign / 100000000, 2),
        "investment": round(investment / 100000000, 2),
        "dealer": round(dealer_total / 100000000, 2),
        "total": round(total_sum / 100000000, 2)
    }

    # 5. 寫入檔案 (只有成功抓到資料才會執行到這)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 今日資料更新成功: {result}")

    # 6. 發送 LINE 通知
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    u_id = os.getenv("LINE_USER_ID")
    if token and u_id:
        endpoint = "https://api.line.me/v2/bot/message/push"
        headers_line = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        msg = f"📊 {result['date']} 三大法人買賣金額\n-------------------\n外資：{result['foreign']} 億\n投信：{result['investment']} 億\n自營：{result['dealer']} 億\n-------------------\n合計：{result['total']} 億"
        payload = {"to": u_id, "messages": [{"type": "text", "text": msg}]}
        requests.post(endpoint, headers=headers_line, json=payload)
        print("📱 LINE 通知已發送")

except Exception as e:
    print(f"❌ 資料解析或發送失敗: {e}")
