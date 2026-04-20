import requests
import json
from datetime import datetime
import os

# 1. 設定 Header 模擬瀏覽器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 取得今日日期
today = datetime.now().strftime("%Y%m%d")
url = f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?date={today}&response=json"

try:
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
except Exception as e:
    print(f"❌ 請求失敗: {e}")
    exit(0)

# 3. 檢查是否有資料 (若尚未更新則停止，不覆蓋舊資料)
if data.get("stat") != "OK" or "data" not in data or len(data["data"]) == 0:
    print(f"⚠️ 證交所尚未更新 {today} 的金額資料，程式終止。")
    exit(0)

# 4. 解析並加總自營商金額
try:
    # 索引說明: [0]自營商(避險), [1]自營商(自行買賣), [2]投信, [3]外資及陸資
    # 欄位說明: [3] 是「買賣差額」
    dealer_hedge = float(data["data"][0][3].replace(",", ""))
    dealer_self = float(data["data"][1][3].replace(",", ""))
    investment = float(data["data"][2][3].replace(",", ""))
    foreign = float(data["data"][3][3].replace(",", ""))

    # ✅ 修正：自營商總計 = 自行買賣 + 避險
    dealer_total = dealer_self + dealer_hedge
    total_sum = dealer_total + investment + foreign

    # 單位轉換為「億元」，四捨五入至小數點後兩位
    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "foreign": round(foreign / 100000000, 2),
        "investment": round(investment / 100000000, 2),
        "dealer": round(dealer_total / 100000000, 2),
        "total": round(total_sum / 100000000, 2)
    }

    # 5. 儲存為 JSON 檔案
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 處理完成，已更新 data.json: {result}")

    # 6. LINE Messaging API 推播
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    u_id = os.getenv("LINE_USER_ID")
    if token and u_id:
        endpoint = "https://api.line.me/v2/bot/message/push"
        headers_line = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        
        # 組合 LINE 訊息內容
        msg = (
            f"📊 {result['date']} 三大法人買賣金額\n"
            f"-------------------\n"
            f"🏢 外資：{result['foreign']} 億\n"
            f"🏛️ 投信：{result['investment']} 億\n"
            f"⚖️ 自營：{result['dealer']} 億\n"
            f"-------------------\n"
            f"💰 合計：{result['total']} 億\n"
            f"🔗 網頁：https://candyspydemo-alt.github.io/daily-report/"
        )
        
        payload = {"to": u_id, "messages": [{"type": "text", "text": msg}]}
        requests.post(endpoint, headers=headers_line, json=payload)
        print("📱 LINE 通知發送成功！")

except Exception as e:
    print(f"❌ 解析資料或發送 LINE 失敗: {e}")
