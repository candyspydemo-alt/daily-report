import requests
import json
from datetime import datetime, timedelta, timezone
import os

# --- 設定時區 (台灣 UTC+8) ---
tz = timezone(timedelta(hours=8))
now_tw = datetime.now(tz)
today_str = now_tw.strftime("%Y%m%d")
today_hyphen = now_tw.strftime("%Y-%m-%d")

# 1. 檢查今日是否已執行過
if os.path.exists("data.json"):
    try:
        with open("data.json", "r", encoding="utf-8") as f:
            old_data = json.load(f)
            if old_data.get("date") == today_hyphen:
                print(f"✅ {today_hyphen} 資料今日已更新過，跳過執行。")
                exit(0)
    except Exception as e:
        print(f"⚠️ 讀取舊資料失敗: {e}")

# 2. 設定 Header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 3. 取得證交所 BFI82U API
url = f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?date={today_str}&response=json"

try:
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
except Exception as e:
    print(f"❌ 請求失敗: {e}")
    exit(0)

if data.get("stat") != "OK" or "data" not in data or len(data["data"]) == 0:
    print(f"⚠️ 證交所尚未更新 {today_str} 的資料。")
    exit(0)

# 4. 解析指定項目 (索引 3 是買賣差額)
try:
    # 根據證交所 BFI82U 的資料順序：
    # [0] 自營商(避險)
    # [1] 自營商(自行買賣)
    # [2] 投信
    # [3] 外資及陸資(不含外資自營商)
    # [4] 外資自營商
    # [5] 合計 (總計)
    
    val_dealer_hedge = float(data["data"][0][3].replace(",", ""))
    val_dealer_self  = float(data["data"][1][3].replace(",", ""))
    val_investment   = float(data["data"][2][3].replace(",", ""))
    val_foreign_ex   = float(data["data"][3][3].replace(",", "")) # 不含外資自營
    val_foreign_deal = float(data["data"][4][3].replace(",", "")) # 外資自營
    val_total        = float(data["data"][5][3].replace(",", ""))

    result = {
        "date": today_hyphen,
        "dealer_self": round(val_dealer_self / 100000000, 2),
        "dealer_hedge": round(val_dealer_hedge / 100000000, 2),
        "investment": round(val_investment / 100000000, 2),
        "foreign_ex": round(val_foreign_ex / 100000000, 2),
        "foreign_dealer": round(val_foreign_deal / 100000000, 2),
        "total": round(val_total / 100000000, 2)
    }

    # 5. 儲存 JSON
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 6. LINE 推播
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    u_id = os.getenv("LINE_USER_ID")
    
    if token and u_id:
        endpoint = "https://api.line.me/v2/bot/message/push"
        headers_line = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        
        msg = (
            f"📊 {result['date']} 三大法人買賣金額\n"
            f"-------------------\n"
            f"👤 自營(自行)：{result['dealer_self']} 億\n"
            f"🛡️ 自營(避險)：{result['dealer_hedge']} 億\n"
            f"🏛️ 投信：{result['investment']} 億\n"
            f"🌍 外資(不含自營)：{result['foreign_ex']} 億\n"
            f"🏦 外資自營商：{result['foreign_dealer']} 億\n"
            f"-------------------\n"
            f"💰 合計：{result['total']} 億\n"
            f"🔗 網頁：你的網頁連結"
        )
        
        payload = {"to": u_id, "messages": [{"type": "text", "text": msg}]}
        requests.post(endpoint, headers=headers_line, json=payload)
        print("📱 LINE 通知已根據新格式發送！")

except Exception as e:
    print(f"❌ 解析失敗: {e}")
